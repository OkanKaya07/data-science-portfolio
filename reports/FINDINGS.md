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

## 4. Excel operations dashboard

The workbook includes 731 daily source records and summarizes **3,292,679 rentals**. Registered rentals represent **81.17%** of the total. SUMIFS/COUNTIFS calculate monthly volume, observed days, and rider mix. The full total reconciles to the source; changing a source count by +10 changed the summary by +10, and the change was restored before export. Cached export values, chart references, and line color were checked. Both sheets were visually reviewed. Native Excel desktop recalculation was not separately exercised.

## 5. Python sensor-data application

The real UCI CSV contains **9,357 valid timestamped rows**, with 114 date-empty trailing rows skipped. The actual file spans **10 March 2004–4 April 2005**. There are 1,683 missing CO readings. The CLI preserves missing values as SQL NULL and exports daily coverage-qualified averages. Five unit tests pass, including repeat-load idempotence and malformed-input rejection.

## 6. R leukemia expression analysis

The Golub subset has **3,051 features and 38 samples**: 27 ALL and 11 AML. Two-sided Welch tests with BH correction identify **695 features at adjusted p < 0.05**. Unsupervised PCA of the 500 highest-variance scaled features explains **19.97%** of variance on PC1 and **12.41%** on PC2. This is a small historical exploratory dataset, with no independent replication or clinical validation. Effects use the supplied preprocessed scale and are not log2 fold changes.

## Verification

Nine Python tests pass: four existing output integration checks and five sensor-pipeline unit tests. The R script validates dimensions, class counts, finite inputs, and adjusted p-value bounds. Excel calculations, temporary input-change behavior, saved formula caches, native chart bindings, and visual layout were verified. Reported results come from the real source files.
