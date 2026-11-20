"""Draw portfolio charts from the saved analysis tables, without refitting models.

Run ``python plot_results.py`` to save every Python project's chart.
Run ``python plot_results.py --project 05 --show`` for a live Matplotlib window.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs/visual-studio/charts"
BLUE, TEAL, ORANGE = "#245D89", "#147D74", "#C46236"


def read_table(path: str, columns: list[str]) -> pd.DataFrame:
    frame = pd.read_csv(ROOT / path)
    missing = set(columns).difference(frame.columns)
    if frame.empty or missing:
        raise ValueError(f"Empty table or missing columns in {path}: {sorted(missing)}")
    return frame


def finite(frame: pd.DataFrame, columns: list[str]) -> None:
    if not np.isfinite(frame[columns].to_numpy(dtype=float)).all():
        raise ValueError(f"Nonfinite values in {columns}")


def decorate(fig, title: str, note: str) -> None:
    fig.suptitle(title, fontsize=15, fontweight="bold", y=0.97)
    fig.text(0.5, 0.025, note, ha="center", va="bottom", fontsize=9, color="#46535D")
    fig.subplots_adjust(left=0.10, right=0.96, bottom=0.17, top=0.86)


def retail():
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    data = read_table("reports/monthly_sales.csv", ["month", "revenue_gbp"])
    finite(data, ["revenue_gbp"])
    if data.month.duplicated().any() or (data.revenue_gbp < 0).any():
        raise ValueError("Monthly sales must have unique months and nonnegative revenue")
    fig, ax = plt.subplots(figsize=(9, 5.3))
    bars = ax.bar(data.month, data.revenue_gbp, color=TEAL)
    bars[-1].set_color(ORANGE)
    ax.set(xlabel="Invoice month", ylabel="Positive sales (GBP)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1e6:.1f}m"))
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    decorate(fig, "01 | Retail: monthly positive sales", "Returns excluded from positive sales; December 2011 is a partial month.")
    fig.subplots_adjust(bottom=0.28)
    return fig, "01-retail-monthly.png", {"months": len(data), "last_month": data.month.iloc[-1]}


def segments():
    import matplotlib.pyplot as plt
    from matplotlib.ticker import StrMethodFormatter

    data = read_table("reports/segment_profiles.csv", ["cluster", "customers", "median_spend_gbp"])
    finite(data, ["customers", "median_spend_gbp"])
    if int(data.customers.sum()) != 4338 or (data.customers <= 0).any():
        raise ValueError("Customer profile totals no longer match the saved analysis")
    fig, axes = plt.subplots(1, 2, figsize=(9, 5.3))
    labels = [f"Cluster {value}" for value in data.cluster]
    for ax, column, ylabel in zip(axes, ["customers", "median_spend_gbp"], ["Customers", "Median customer spend (GBP)"]):
        bars = ax.bar(labels, data[column], color=[BLUE, TEAL][:len(data)])
        ax.bar_label(bars, labels=[f"{value:,.0f}" for value in data[column]], padding=4)
        ax.set(ylabel=ylabel, ylim=(0, data[column].max() * 1.18))
        ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
    decorate(fig, "02 | Customer segmentation: two RFM profiles", "Cluster numbers are arbitrary labels; these profiles describe historical customers.")
    fig.subplots_adjust(wspace=0.40)
    return fig, "02-customer-profiles.png", {"clusters": len(data), "customers": int(data.customers.sum())}


def bike():
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    data = read_table("reports/bike_predictions.csv", ["date", "actual", "predicted"])
    finite(data, ["actual", "predicted"])
    dates = pd.to_datetime(data.date)
    if not dates.is_monotonic_increasing or dates.duplicated().any():
        raise ValueError("Bike holdout dates are not unique and ordered")
    mae = float(np.abs(data.actual - data.predicted).mean())
    metrics = read_table("reports/bike_metrics.csv", ["selected_by_cv", "test_mae"])
    selected = metrics.loc[metrics.selected_by_cv.astype(str).str.lower().eq("true")]
    if len(selected) != 1 or not np.isclose(mae, selected.test_mae.iloc[0]):
        raise ValueError("Prediction MAE disagrees with the selected model report")
    fig, ax = plt.subplots(figsize=(9, 5.3))
    ax.plot(dates, data.actual, color=BLUE, label="Observed", linewidth=1.5)
    ax.plot(dates, data.predicted, color=ORANGE, label="Selected model", linewidth=1.4)
    ax.set(xlabel="Later holdout date", ylabel="Daily rentals")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.legend(frameon=False)
    ax.grid(alpha=0.2)
    decorate(fig, "03 | Bike demand: chronological holdout", f"MAE = {mae:,.0f} rentals. Conditional on observed weather; not a day-ahead forecast.")
    return fig, "03-bike-holdout.png", {"holdout_days": len(data), "mae_rentals": mae}


def air_quality():
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    data = read_table("projects/05-python-air-quality/reports/daily_summary.csv", [
        "day", "recorded_hours", "valid_co_hours", "qualified_co_mean_mg_m3",
    ])
    finite(data, ["recorded_hours", "valid_co_hours"])
    if (data.valid_co_hours < 0).any() or (data.valid_co_hours > data.recorded_hours).any():
        raise ValueError("Valid CO hours must lie between zero and recorded hours")
    dates = pd.to_datetime(data.day)
    if dates.duplicated().any() or not dates.is_monotonic_increasing:
        raise ValueError("Air-quality dates must be unique and ordered")
    # Reindex to a full calendar so any missing days also produce visible gaps.
    daily = data.assign(day=dates).set_index("day").reindex(pd.date_range(dates.min(), dates.max()))
    valid_means = data.qualified_co_mean_mg_m3.dropna()
    if valid_means.empty or not np.isfinite(valid_means).all() or (valid_means < 0).any():
        raise ValueError("Qualified CO means must be finite and nonnegative")
    fig, axes = plt.subplots(2, 1, figsize=(9, 5.3), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    axes[0].plot(daily.index, daily.qualified_co_mean_mg_m3, color=TEAL, linewidth=1.2)
    axes[0].set(ylabel="Daily mean CO (mg/m³)")
    axes[1].plot(daily.index, daily.valid_co_hours, color=BLUE, linewidth=1)
    axes[1].axhline(18, color=ORANGE, linestyle="--", linewidth=1, label="18-hour qualification")
    axes[1].set(ylabel="Valid CO hours", xlabel="Observation date", ylim=(-0.5, 25))
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    axes[1].legend(loc="lower left", frameon=False, fontsize=9)
    for ax in axes:
        ax.grid(alpha=0.2)
    decorate(fig, "05 | Air quality: daily CO and data coverage", "Daily means require at least 18 valid CO hours. Missing or unqualified values remain gaps.")
    fig.subplots_adjust(hspace=0.12)
    return fig, "05-air-quality.png", {"days": len(data), "qualified_days": int(valid_means.size)}


def pasilla():
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    data = read_table("projects/07-pasilla-rnaseq/reports/samples.csv", ["sample", "condition", "type", "PC1", "PC2"])
    finite(data, ["PC1", "PC2"])
    if len(data) != 7 or data["sample"].duplicated().any():
        raise ValueError("Pasilla PCA must contain seven distinct libraries")
    colors = {"untreated": BLUE, "treated": ORANGE}
    markers = {"single-read": "o", "paired-end": "s"}
    if not set(data.condition).issubset(colors) or not set(data.type).issubset(markers):
        raise ValueError("Unexpected Pasilla condition or read layout")
    fig, ax = plt.subplots(figsize=(9, 5.3))
    for row in data.itertuples():
        ax.scatter(row.PC1, row.PC2, color=colors[row.condition], marker=markers[row.type], s=90)
        offset = (7, -16) if row.sample == "untreated3" else (7, 7)
        ax.annotate(row.sample, (row.PC1, row.PC2), xytext=offset, textcoords="offset points", fontsize=9)
    ax.margins(x=0.20, y=0.20)
    ax.set(xlabel="PC1 score", ylabel="PC2 score")
    ax.grid(alpha=0.2)
    handles = [Line2D([], [], color=color, marker="o", linestyle="", label=condition) for condition, color in colors.items()]
    handles += [Line2D([], [], color="#46535D", marker=marker, linestyle="", label=layout) for layout, marker in markers.items()]
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=9, ncol=2)
    decorate(fig, "07 | Pasilla RNA-seq: sample PCA", "Saved PCA scores for seven libraries; condition and read layout are both shown. Exploratory only.")
    return fig, "07-pasilla-pca.png", {"libraries": len(data), "conditions": data.condition.value_counts().to_dict()}


def diagnostic():
    import matplotlib.pyplot as plt
    from sklearn.metrics import confusion_matrix, roc_auc_score, roc_curve

    data = read_table("projects/08-diagnostic-risk-classification/reports/holdout_predictions.csv", [
        "actual_malignant", "probability_malignant", "triage_flag",
    ])
    finite(data, ["actual_malignant", "probability_malignant", "triage_flag"])
    if not data.probability_malignant.between(0, 1).all() or set(data.actual_malignant) != {0, 1}:
        raise ValueError("Diagnostic labels or probabilities are invalid")
    metrics = read_table("projects/08-diagnostic-risk-classification/reports/model_metrics.csv", ["selected", "test_roc_auc"])
    selected = metrics.loc[metrics.selected.eq("yes")]
    auc = float(roc_auc_score(data.actual_malignant, data.probability_malignant))
    if len(data) != 143 or len(selected) != 1 or not np.isclose(auc, selected.test_roc_auc.iloc[0], atol=1e-5):
        raise ValueError("Diagnostic holdout size or AUC differs from the saved report")
    matrix = confusion_matrix(data.actual_malignant, data.triage_flag, labels=[0, 1])
    expected = selected[["holdout_true_negative", "holdout_false_positive", "holdout_false_negative", "holdout_true_positive"]].to_numpy().reshape(2, 2)
    if not np.array_equal(matrix, expected):
        raise ValueError("Confusion counts differ from the saved evaluation")
    fpr, tpr, _ = roc_curve(data.actual_malignant, data.probability_malignant)
    fig, axes = plt.subplots(1, 2, figsize=(9, 5.3))
    axes[0].plot(fpr, tpr, color=TEAL, label=f"ROC AUC = {auc:.3f}")
    axes[0].plot([0, 1], [0, 1], "--", color="#97A2AB", linewidth=1)
    axes[0].set(xlabel="False positive rate", ylabel="True positive rate", xlim=(0, 1), ylim=(0, 1.03))
    axes[0].legend(frameon=False, loc="lower right")
    axes[0].grid(alpha=0.2)
    axes[1].imshow(matrix, cmap="Blues", vmin=0, vmax=matrix.max())
    for i in range(2):
        for j in range(2):
            axes[1].text(j, i, str(matrix[i, j]), ha="center", va="center", fontsize=17, color="white" if matrix[i, j] > matrix.max() / 2 else "#202932")
    axes[1].set(xticks=[0, 1], yticks=[0, 1], xticklabels=["Benign", "Malignant"], yticklabels=["Benign", "Malignant"], xlabel="Predicted flag", ylabel="Actual label")
    axes[1].set_title("Flags at development-selected threshold", fontsize=9.5)
    decorate(fig, "08 | Diagnostic classification: 143-row holdout", "Educational historical-data analysis; not clinical validation or a diagnostic tool.")
    fig.subplots_adjust(wspace=0.40)
    return fig, "08-diagnostic-holdout.png", {"holdout_rows": len(data), "roc_auc": auc, "confusion_matrix": matrix.tolist()}


def bank():
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    path = ROOT / "projects/09-bank-campaign-propensity/reports/run_summary.json"
    summary = json.loads(path.read_text(encoding="utf-8"))
    metrics = summary["holdout_metrics"]
    rates = [metrics["base_subscription_rate"], metrics["precision_at_capacity"]]
    if not all(np.isfinite(rate) and 0 <= rate <= 1 for rate in rates):
        raise ValueError("Bank subscription rates are invalid")
    if metrics["selected_rows"] > metrics["rows"] or not summary["duration_excluded"]:
        raise ValueError("Bank holdout selection or leakage exclusion is invalid")
    fig, ax = plt.subplots(figsize=(9, 5.3))
    labels = [f"All later holdout contacts\n(n = {metrics['rows']:,})", f"Selected top 15%\n(n = {metrics['selected_rows']:,})"]
    bars = ax.bar(labels, rates, color=[BLUE, TEAL], width=0.55)
    ax.bar_label(bars, labels=[f"{rate:.1%}" for rate in rates], padding=6, fontweight="bold")
    ax.set(ylabel="Observed term-deposit subscription rate", ylim=(0, max(rates) + 0.15))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    decorate(fig, "09 | Bank campaign: observed later-holdout subscriptions", "Selected contacts are part of the same holdout; this is ranking performance, not a causal uplift estimate.")
    return fig, "09-bank-holdout.png", {"holdout_rows": metrics["rows"], "selected_rows": metrics["selected_rows"], "rates": rates}


PROJECTS = {"01": retail, "02": segments, "03": bike, "05": air_quality, "07": pasilla, "08": diagnostic, "09": bank}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=["all", *PROJECTS], default="all")
    parser.add_argument("--show", action="store_true", help="Also open live Matplotlib figure windows")
    args = parser.parse_args()
    import matplotlib
    matplotlib.use("TkAgg" if args.show else "Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    OUT.mkdir(parents=True, exist_ok=True)
    selected = PROJECTS if args.project == "all" else {args.project: PROJECTS[args.project]}
    for number, build in selected.items():
        figure, name, checks = build()
        figure.canvas.manager.set_window_title(f"{number} | Portfolio chart")
        destination = OUT / name
        figure.savefig(destination, dpi=140, facecolor="white")
        print(json.dumps({"project": number, "chart": str(destination.relative_to(ROOT)), **checks}))
        if not args.show:
            plt.close(figure)
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
