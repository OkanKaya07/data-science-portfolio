# Data Analytics & Machine Learning Portfolio

Three intermediate case studies built from real UCI datasets. Each connects a business question to reproducible code, measured results, and limitations.

| Project | Question | Methods | Walkthrough |
|---|---|---|---|
| Retail analytics | How do sales, order value, and geographic concentration change? | Python ETL, SQLite CTEs, window functions, data-quality audit | [Case study](projects/01-retail-analytics/README.md) |
| Customer segmentation | Which customers have similar purchase behavior? | RFM, log transform, standardization, K-means, silhouette, seed stability | [Case study](projects/02-customer-segmentation/README.md) |
| Bike demand modeling | How well can calendar and observed weather explain daily demand? | Chronological holdout, expanding-window CV, baseline, Ridge, gradient boosting, permutation importance | [Case study](projects/03-bike-demand/README.md) |

## Run locally

Python 3.12 recommended. From the repository root:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
python -m unittest discover -s tests -v
```

The first run downloads the original archives from UCI. `python run.py --download-only` downloads without analyzing. Raw data, local caches, and SQLite databases are ignored by Git. Aggregate reports, charts, and source archive SHA-256 hashes are versioned. No synthetic rows are used. Do not load pickle caches from third parties; delete your local `data/cache/` to rebuild.

## Evidence and reproducibility

- [Source provenance](data/provenance.json): original URLs and archive hashes.
- [Generated findings](reports/FINDINGS.md): measured outputs from a full local run.
- [SQL](sql/retail.sql): monthly revenue, average order value, and month-over-month change.
- [Pipeline](run.py): download, cleaning, analysis, training, and export.
- [Tests](tests/test_outputs.py): reconciliation, leakage checks, split integrity, and output validation.

The small dataset checks and fixed random seeds make unexpected changes visible. Exact numeric results can vary slightly across numerical libraries and hardware. Dependency versions are pinned for the primary libraries; `environment.txt` records the actual local execution versions.

## Data sources and attribution

1. Chen, D. (2015). **Online Retail**. UCI Machine Learning Repository. [Dataset](https://archive.ics.uci.edu/dataset/352/online+retail), [DOI: 10.24432/C5BW33](https://doi.org/10.24432/C5BW33). Real UK retail transactions, December 2010–December 2011.
2. Fanaee-T, H. (2013). **Bike Sharing**. UCI Machine Learning Repository. [Dataset](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset), [DOI: 10.24432/C5W894](https://doi.org/10.24432/C5W894). Capital Bikeshare observations, 2011–2012.

Both datasets are distributed by UCI under CC BY 4.0. Derived data and charts retain that attribution. Code is MIT licensed; third-party datasets are not relicensed as MIT. These historical datasets demonstrate methods and do not describe current business conditions.

## Portfolio notes

Prepared with AI assistance. Results come from executable analysis, not claimed production deployments. Suggested business actions are hypotheses for validation; no revenue uplift or causal effect is asserted.

Türkçe: Bu repo gerçek verilerle hazırlanmış üç orta seviye proje içerir. Her proje için yöntemi, sonuçları ve sınırlamaları açıklayan İngilizce rapor bulunur.
