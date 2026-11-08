"""Leakage-aware diagnostic classification workflow using an open UCI dataset.

This is an educational machine-learning analysis, not a clinical decision tool.
"""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.datasets import load_breast_cancer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    fbeta_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


RANDOM_STATE = 42
TEST_SIZE = 0.25
PROJECT_DIR = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_DIR / "reports"
SOURCE_URL = "https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic"


def load_data() -> tuple[pd.DataFrame, pd.Series]:
    """Load the scikit-learn copy of the UCI diagnostic dataset.

    The original target encodes malignant as 0 and benign as 1.  This project
    reverses it so that 1 consistently means the positive (malignant) class.
    """
    dataset = load_breast_cancer(as_frame=True)
    features = dataset.data.copy()
    malignant = pd.Series(
        (dataset.target.to_numpy() == 0).astype(int),
        index=features.index,
        name="malignant",
    )
    if len(features) != len(malignant) or features.isna().any().any():
        raise ValueError("Unexpected dataset shape or missing values.")
    return features, malignant


def make_models() -> dict[str, Pipeline]:
    """Return pipelines so preprocessing is refit only inside each CV fold."""
    return {
        "dummy_prior": Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                ("model", DummyClassifier(strategy="prior")),
            ]
        ),
        "scaled_logistic_regression": Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=10_000,
                        random_state=RANDOM_STATE,
                        solver="liblinear",
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=500,
                        class_weight="balanced",
                        min_samples_leaf=2,
                        n_jobs=-1,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
    }


def select_f2_threshold(y_true: pd.Series, probabilities: np.ndarray) -> tuple[float, float]:
    """Choose a triage threshold on development-only out-of-fold probabilities."""
    candidates = np.unique(np.r_[0.0, probabilities, 1.0])
    scores = [fbeta_score(y_true, probabilities >= value, beta=2, zero_division=0) for value in candidates]
    best_position = int(np.argmax(scores))
    return float(candidates[best_position]), float(scores[best_position])


def holdout_metrics(y_true: pd.Series, probabilities: np.ndarray, threshold: float) -> dict[str, float | int]:
    """Return ranking, calibration and triage metrics for the untouched holdout."""
    predicted = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predicted, labels=[0, 1]).ravel()
    return {
        "test_roc_auc": float(roc_auc_score(y_true, probabilities)),
        "test_average_precision": float(average_precision_score(y_true, probabilities)),
        "test_brier_score": float(brier_score_loss(y_true, probabilities)),
        "test_balanced_accuracy": float(balanced_accuracy_score(y_true, predicted)),
        "test_recall_malignant": float(recall_score(y_true, predicted, zero_division=0)),
        "test_precision_malignant": float(precision_score(y_true, predicted, zero_division=0)),
        "test_f2": float(fbeta_score(y_true, predicted, beta=2, zero_division=0)),
        "holdout_true_negative": int(tn),
        "holdout_false_positive": int(fp),
        "holdout_false_negative": int(fn),
        "holdout_true_positive": int(tp),
    }


def run() -> pd.DataFrame:
    """Run development-set model selection, then score one untouched holdout."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    features, target = load_data()
    x_development, x_holdout, y_development, y_holdout = train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=target,
    )
    if not x_development.index.intersection(x_holdout.index).empty:
        raise AssertionError("Development and holdout rows overlap.")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    scoring = {"roc_auc": "roc_auc", "average_precision": "average_precision", "balanced_accuracy": "balanced_accuracy"}
    rows: list[dict[str, float | str]] = []
    models = make_models()
    for name, estimator in models.items():
        result = cross_validate(estimator, x_development, y_development, cv=cv, scoring=scoring, n_jobs=-1)
        rows.append(
            {
                "model": name,
                "cv_roc_auc_mean": float(np.mean(result["test_roc_auc"])),
                "cv_roc_auc_std": float(np.std(result["test_roc_auc"], ddof=1)),
                "cv_average_precision_mean": float(np.mean(result["test_average_precision"])),
                "cv_balanced_accuracy_mean": float(np.mean(result["test_balanced_accuracy"])),
            }
        )

    metrics = pd.DataFrame(rows).sort_values("cv_roc_auc_mean", ascending=False, kind="stable").reset_index(drop=True)
    selected_name = str(metrics.loc[0, "model"])
    selected = clone(models[selected_name])
    oof_probabilities = cross_val_predict(
        selected,
        x_development,
        y_development,
        cv=cv,
        method="predict_proba",
        n_jobs=-1,
    )[:, 1]
    threshold, development_f2 = select_f2_threshold(y_development, oof_probabilities)
    selected.fit(x_development, y_development)
    holdout_probabilities = selected.predict_proba(x_holdout)[:, 1]
    evaluated = holdout_metrics(y_holdout, holdout_probabilities, threshold)

    for column, value in {"selected": "no", "threshold_from_oof_f2": np.nan, "development_oof_f2": np.nan, **{key: np.nan for key in evaluated}}.items():
        metrics[column] = value
    selected_row = metrics.index[metrics["model"] == selected_name][0]
    metrics.loc[selected_row, "selected"] = "yes"
    metrics.loc[selected_row, "threshold_from_oof_f2"] = threshold
    metrics.loc[selected_row, "development_oof_f2"] = development_f2
    for key, value in evaluated.items():
        metrics.loc[selected_row, key] = value
    metrics.to_csv(REPORTS_DIR / "model_metrics.csv", index=False, float_format="%.6f")

    predictions = pd.DataFrame(
        {
            "source_row": x_holdout.index,
            "actual_malignant": y_holdout.to_numpy(),
            "probability_malignant": holdout_probabilities,
            "triage_flag": (holdout_probabilities >= threshold).astype(int),
        }
    ).sort_values("probability_malignant", ascending=False)
    predictions.to_csv(REPORTS_DIR / "holdout_predictions.csv", index=False, float_format="%.6f")

    summary = {
        "data_source": SOURCE_URL,
        "dataset_loader": "sklearn.datasets.load_breast_cancer",
        "total_rows": int(len(features)),
        "feature_count": int(features.shape[1]),
        "malignant_rows": int(target.sum()),
        "benign_rows": int((1 - target).sum()),
        "development_rows": int(len(x_development)),
        "holdout_rows": int(len(x_holdout)),
        "random_state": RANDOM_STATE,
        "selected_model": selected_name,
        "threshold_selection": "maximum F2 on development-set out-of-fold probabilities",
        "selected_threshold": threshold,
        "development_oof_f2": development_f2,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        **evaluated,
    }
    (REPORTS_DIR / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return metrics


if __name__ == "__main__":
    frame = run()
    print(frame.to_string(index=False))
