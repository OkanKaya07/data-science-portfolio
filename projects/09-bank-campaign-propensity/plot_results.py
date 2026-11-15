"""Plot observed subscription rates from the saved holdout evaluation."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


def main() -> None:
    reports = Path(__file__).resolve().parent / "reports"
    with (reports / "run_summary.json").open(encoding="utf-8") as source:
        metrics = json.load(source)["holdout_metrics"]

    rates = [metrics["base_subscription_rate"], metrics["precision_at_capacity"]]
    labels = [
        f"All holdout contacts\n(n = {metrics['rows']:,})",
        f"Selected top 15%\n(n = {metrics['selected_rows']:,})",
    ]
    fig, ax = plt.subplots(figsize=(7.5, 4.3), layout="constrained")
    bars = ax.bar(labels, rates, width=0.54, color=["#71849B", "#147D74"])
    ax.bar_label(bars, labels=[f"{rate:.1%}" for rate in rates], padding=6, fontweight="bold")
    ax.set(
        title="Observed term-deposit subscriptions on the later holdout",
        ylabel="Observed subscription rate",
        ylim=(0, min(1.1, max(rates) + 0.15)),
    )
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.grid(axis="y", alpha=0.22)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(reports / "holdout_subscription_rates.png", dpi=96)
    plt.close(fig)


if __name__ == "__main__":
    main()
