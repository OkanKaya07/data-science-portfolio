# Results from the full local run

Execution date: 22 October 2026. Source datasets are historical; figures below are measured outputs, not current business statistics.

## 1. Retail analytics

- Raw workbook: **541,909** lines.
- Exact duplicate lines removed: **5,268**.
- Raw lines with missing customer IDs: **135,080**.
- Positive sales lines after cleaning: **524,878**.
- Positive sales value: **£10,642,110.80**.
- Negative-quantity value after deduplication, with positive prices: **−£893,979.73**, reported separately rather than matched to sales.

Positive sales do not equal profit or reconciled accounting revenue. The value is the sum of quantity × unit price under the documented filter. See the monthly and country CSVs for the complete breakdown. December 2011 is partial.

## 2. Customer segmentation

**4,338** identifiable customers are analyzed at the **10 December 2011** snapshot. The best tested silhouette is **0.4271** at **k=2**. Agreement across two initialization seeds is **ARI 0.9982**.

| Cluster | Customers | Median recency | Median orders | Median spend | Share of identified positive sales |
|---|---:|---:|---:|---:|---:|
| 0 | 1,652 | 16 days | 6 | £2,077.92 | 84.95% |
| 1 | 2,686 | 95 days | 1 | £363.65 | 15.05% |

Cluster 0 is a reasonable candidate for retention experiments; cluster 1 merits investigation for reactivation. These are proposed experiments, not demonstrated effects. Sales shares here exclude customers without IDs and therefore use a different denominator from the overall retail total.

## 3. Bike demand modeling

Development: **584 days through 6 August 2012**. Holdout: **147 days from 7 August 2012**. Gradient boosting was selected by mean expanding-window validation MAE before holdout scoring.

| Model | Holdout MAE | Holdout RMSE | Holdout R² |
|---|---:|---:|---:|
| Training mean | 2,290.41 | 2,560.56 | −0.8657 |
| Ridge | 1,121.63 | 1,478.65 | 0.3778 |
| Gradient boosting | 724.78 | 1,022.15 | 0.7027 |

The selected model reduces holdout MAE by approximately **68.4%** relative to the training-mean baseline in this particular split. This is a conditional estimate using observed same-day weather. It does not establish day-ahead accuracy or generalization to another city or year. Permutation importance is descriptive and is not causal evidence.

## Verification

Four integration tests pass: sales totals reconcile across SQL exports; customer counts and shares reconcile; chronological fold boundaries and excluded leakage columns are checked; reported selected-model MAE matches saved predictions. All three chart files were generated from the full datasets.
