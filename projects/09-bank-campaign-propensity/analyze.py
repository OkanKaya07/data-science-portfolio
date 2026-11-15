"""Time-aware, capacity-constrained campaign propensity analysis.

The original UCI data are downloaded on demand and are not committed to this
repository.  This is an educational portfolio analysis, not a production
marketing system.
"""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sys
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_DIR = Path(__file__).resolve().parent
CACHE_DIR = PROJECT_DIR / "data" / "cache"
REPORTS_DIR = PROJECT_DIR / "reports"
ARCHIVE_PATH = CACHE_DIR / "bank_marketing.zip"
ARCHIVE_URL = "https://archive.ics.uci.edu/static/public/222/bank%2Bmarketing.zip"
ARCHIVE_SHA256 = "e0bf5f5de5b846e2f18e9d90606637267d46dfa260e0f17bb12e605db5efbeb4"
CSV_MEMBER = "bank-additional/bank-additional-full.csv"
TEST_FRACTION = 0.20
CAPACITY_FRACTION = 0.15
RANDOM_STATE = 42


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1_048_576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_archive() -> Path:
    """Download the original UCI archive once and verify its SHA-256 hash."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE_PATH.exists():
        temporary = ARCHIVE_PATH.with_suffix(".download")
        try:
            with urlopen(ARCHIVE_URL, timeout=60) as response, temporary.open("wb") as destination:
                shutil.copyfileobj(response, destination)
            temporary.replace(ARCHIVE_PATH)
        finally:
            if temporary.exists():
                temporary.unlink()
    observed = sha256(ARCHIVE_PATH)
    if observed != ARCHIVE_SHA256:
        raise ValueError(f"Archive hash mismatch: expected {ARCHIVE_SHA256}, observed {observed}")
    return ARCHIVE_PATH


def load_data() -> pd.DataFrame:
    """Load the 41,188-row UCI bank-additional-full table from the verified archive."""
    archive = ensure_archive()
    with ZipFile(archive) as outer:
        nested_archive = outer.read("bank-additional.zip")
    with ZipFile(BytesIO(nested_archive)) as nested, nested.open(CSV_MEMBER) as csv_file:
        frame = pd.read_csv(csv_file, sep=";")
    expected_columns = {
        "age", "job", "marital", "education", "default", "housing", "loan", "contact", "month",
        "day_of_week", "duration", "campaign", "pdays", "previous", "poutcome", "emp.var.rate",
        "cons.price.idx", "cons.conf.idx", "euribor3m", "nr.employed", "y",
    }
    if frame.shape != (41_188, 21) or set(frame.columns) != expected_columns:
        raise ValueError("Unexpected UCI Bank Marketing table shape or schema.")
    if frame.isna().any().any():
        raise ValueError("Unexpected missing values in the original table.")
    return frame


def prepare_features(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Build pre-contact features and a binary subscription target.

    `duration` is deliberately excluded: it is known only after a call ends and
    would leak post-contact information into a pre-contact targeting model.
    `campaign` includes the current contact in the original documentation, so
    it is converted to the number of contacts before the current call.
    """
    target = frame["y"].eq("yes").astype(int).rename("subscribed")
    features = frame.drop(columns=["y", "duration"]).copy()
    features["prior_campaign_contacts"] = (features.pop("campaign") - 1).clip(lower=0)
    features["previously_contacted"] = np.where(features["pdays"].eq(999), "no", "yes")
    # Keep a numeric sentinel alongside the explicit flag.  Unlike NaN, this
    # remains a valid feature even in early time folds where no earlier contact
    # has yet occurred in the training rows.
    features["days_since_previous_contact"] = np.where(features["pdays"].ne(999), features["pdays"], -1)
    features = features.drop(columns=["pdays"])
    if "duration" in features or not set(target.unique()).issubset({0, 1}):
        raise AssertionError("Leakage exclusion or target encoding failed.")
    return features, target


def make_models(features: pd.DataFrame) -> dict[str, Pipeline]:
    """Create pipelines that refit all preprocessing inside each temporal fold."""
    numeric_columns = features.select_dtypes(include=["number"]).columns.tolist()
    categorical_columns = [column for column in features.columns if column not in numeric_columns]
    preprocessing = ColumnTransformer(
        transformers=[
            ("numeric", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric_columns),
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("one_hot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_columns,
            ),
        ]
    )
    return {
        "dummy_prior": Pipeline([("preprocess", clone(preprocessing)), ("model", DummyClassifier(strategy="prior"))]),
        "logistic_regression": Pipeline(
            [
                ("preprocess", clone(preprocessing)),
                ("model", LogisticRegression(C=0.5, max_iter=1_000, random_state=RANDOM_STATE, solver="liblinear")),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("preprocess", clone(preprocessing)),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=250,
                        max_features=0.7,
                        min_samples_leaf=10,
                        n_jobs=1,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
    }


def top_capacity_mask(probabilities: np.ndarray, fraction: float = CAPACITY_FRACTION) -> np.ndarray:
    """Select exactly the highest-scored fraction, breaking any ties by row order."""
    if not 0 < fraction <= 1 or len(probabilities) == 0:
        raise ValueError("A non-empty score array and a fraction in (0, 1] are required.")
    count = int(np.ceil(len(probabilities) * fraction))
    mask = np.zeros(len(probabilities), dtype=bool)
    positions = np.argsort(-np.asarray(probabilities), kind="mergesort")[:count]
    mask[positions] = True
    return mask


def targeting_metrics(target: np.ndarray, probabilities: np.ndarray, fraction: float = CAPACITY_FRACTION) -> dict[str, float | int]:
    """Report ranking metrics and response concentration under a fixed call capacity."""
    target = np.asarray(target, dtype=int)
    probabilities = np.asarray(probabilities, dtype=float)
    selected = top_capacity_mask(probabilities, fraction)
    base_rate = float(target.mean())
    selected_rate = float(target[selected].mean())
    return {
        "rows": int(len(target)),
        "selected_rows": int(selected.sum()),
        "selected_fraction": float(selected.mean()),
        "base_subscription_rate": base_rate,
        "precision_at_capacity": selected_rate,
        "recall_at_capacity": float(target[selected].sum() / target.sum()),
        "lift_at_capacity": float(selected_rate / base_rate) if base_rate else float("nan"),
        "roc_auc": float(roc_auc_score(target, probabilities)),
        "average_precision": float(average_precision_score(target, probabilities)),
        "brier_score": float(brier_score_loss(target, probabilities)),
        "subscribers_in_selected_rows": int(target[selected].sum()),
    }


def evaluate_time_folds(models: dict[str, Pipeline], features: pd.DataFrame, target: pd.Series) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """Fit each candidate on earlier rows and validate it on later rows only."""
    splitter = TimeSeriesSplit(n_splits=5)
    records: list[dict[str, float | int | str]] = []
    out_of_fold = {name: np.full(len(features), np.nan) for name in models}
    for fold, (train_index, validation_index) in enumerate(splitter.split(features), start=1):
        x_train, y_train = features.iloc[train_index], target.iloc[train_index]
        x_validation, y_validation = features.iloc[validation_index], target.iloc[validation_index]
        for name, pipeline in models.items():
            fitted = clone(pipeline).fit(x_train, y_train)
            probabilities = fitted.predict_proba(x_validation)[:, 1]
            out_of_fold[name][validation_index] = probabilities
            metrics = targeting_metrics(y_validation.to_numpy(), probabilities)
            records.append({"fold": fold, "model": name, **metrics})
    return pd.DataFrame(records), out_of_fold


def run() -> pd.DataFrame:
    """Run temporal model selection, fixed-capacity targeting, and one later holdout evaluation."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_data()
    features, target = prepare_features(raw)
    split = int(len(features) * (1 - TEST_FRACTION))
    x_development, x_holdout = features.iloc[:split], features.iloc[split:]
    y_development, y_holdout = target.iloc[:split], target.iloc[split:]
    if x_development.index.max() >= x_holdout.index.min():
        raise AssertionError("Chronological development/holdout split is not ordered.")

    models = make_models(features)
    fold_metrics, _ = evaluate_time_folds(models, x_development, y_development)
    fold_metrics.to_csv(REPORTS_DIR / "fold_metrics.csv", index=False, float_format="%.6f")
    comparison = (
        fold_metrics.groupby("model", as_index=False)
        .agg(
            cv_average_precision_mean=("average_precision", "mean"),
            cv_average_precision_std=("average_precision", "std"),
            cv_roc_auc_mean=("roc_auc", "mean"),
            cv_roc_auc_std=("roc_auc", "std"),
            cv_precision_at_capacity_mean=("precision_at_capacity", "mean"),
            cv_recall_at_capacity_mean=("recall_at_capacity", "mean"),
            cv_lift_at_capacity_mean=("lift_at_capacity", "mean"),
        )
        .sort_values("cv_average_precision_mean", ascending=False, kind="stable")
        .reset_index(drop=True)
    )
    selected_name = str(comparison.loc[0, "model"])

    selected = clone(models[selected_name]).fit(x_development, y_development)
    holdout_probabilities = selected.predict_proba(x_holdout)[:, 1]
    holdout_metrics = targeting_metrics(y_holdout.to_numpy(), holdout_probabilities)
    comparison["selected"] = comparison["model"].eq(selected_name).map({True: "yes", False: "no"})
    for column in holdout_metrics:
        comparison[column] = np.nan
    comparison.loc[comparison["model"].eq(selected_name), list(holdout_metrics)] = list(holdout_metrics.values())
    comparison.to_csv(REPORTS_DIR / "model_comparison.csv", index=False, float_format="%.6f")

    holdout_selected = top_capacity_mask(holdout_probabilities)
    selected_contacts = pd.DataFrame(
        {
            "source_row": x_holdout.index[holdout_selected],
            "actual_subscription": y_holdout.to_numpy()[holdout_selected],
            "predicted_subscription_probability": holdout_probabilities[holdout_selected],
        }
    ).sort_values("predicted_subscription_probability", ascending=False)
    selected_contacts.to_csv(REPORTS_DIR / "holdout_targeted_contacts.csv", index=False, float_format="%.6f")

    summary = {
        "data_source": "UCI Machine Learning Repository: Bank Marketing (Moro et al., 2014)",
        "archive_url": ARCHIVE_URL,
        "archive_sha256": ARCHIVE_SHA256,
        "data_rows": int(len(raw)),
        "feature_count_after_leakage_exclusion": int(features.shape[1]),
        "duration_excluded": True,
        "development_rows": int(len(x_development)),
        "holdout_rows": int(len(x_holdout)),
        "development_subscription_rate": float(y_development.mean()),
        "holdout_subscription_rate": float(y_holdout.mean()),
        "validation": "five expanding time-series folds on earlier development rows; final 20% later-row holdout",
        "capacity_policy": f"select the top {CAPACITY_FRACTION:.0%} of scored contacts",
        "selected_model": selected_name,
        "development_validation_metrics": "Per-fold results are recorded in reports/fold_metrics.csv; only their within-fold averages are used for model selection.",
        "holdout_metrics": holdout_metrics,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
    }
    (REPORTS_DIR / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return comparison


if __name__ == "__main__":
    result = run()
    print(result.to_string(index=False))
