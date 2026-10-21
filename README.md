# Data Analytics & Machine Learning Portfolio

Six intermediate projects built from real UCI and Bioconductor data. They cover data analysis, machine learning, Excel, Python application development, and R bioinformatics. Each connects a question to reproducible code, measured results, and limitations.

| Project | Question | Methods | Walkthrough |
|---|---|---|---|
| Retail analytics | How do sales, order value, and geographic concentration change? | Python ETL, SQLite CTEs, window functions, data-quality audit | [Case study](projects/01-retail-analytics/README.md) |
| Customer segmentation | Which customers have similar purchase behavior? | RFM, log transform, standardization, K-means, silhouette, seed stability | [Case study](projects/02-customer-segmentation/README.md) |
| Bike demand modeling | How well can calendar and observed weather explain daily demand? | Chronological holdout, expanding-window CV, baseline, Ridge, gradient boosting, permutation importance | [Case study](projects/03-bike-demand/README.md) |
| Excel operations report | How does rental volume and rider mix change by month? | SUMIFS, COUNTIFS, EDATE, reconciliation, native chart | [Workbook and guide](projects/04-excel-bike-operations/README.md) |
| Python air-quality CLI | How can messy sensor records be loaded reliably? | Dataclasses, type hints, validation, logging, transactions, SQLite, tests | [Application](projects/05-python-air-quality/README.md) |
| R bioinformatics | Which expression features differ between leukemia groups? | Welch tests, BH correction, PCA, reproducible base-R pipeline | [Research analysis](projects/06-r-bioinformatics/README.md) |

## Run locally

Python 3.12 recommended. From the repository root:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
python -m unittest discover -s tests -v
python -m unittest discover -s projects/05-python-air-quality -v
```

`run.py` reproduces projects 1–3 and downloads their original UCI archives. `python run.py --download-only` downloads without analyzing. Projects 4–6 have their own instructions linked above. Raw archives, local caches, and SQLite databases are ignored by Git. Reports, charts, the Excel workbook, and source hashes are versioned. Unit tests use tiny constructed edge cases; all reported analytical results use real source data. Do not load pickle caches from third parties; delete your local `data/cache/` to rebuild.

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

These two datasets are distributed by UCI under CC BY 4.0. Derived data and charts retain that attribution. The air-quality and Golub projects document their own source terms in their READMEs: the air-quality source explicitly excludes commercial use, and the Bioconductor package is LGPL. Original project code is MIT licensed; third-party data are not relicensed as MIT. These historical datasets demonstrate methods and do not describe current conditions.

## Portfolio notes

Prepared with AI assistance. Results come from executable analysis, not claimed production deployments. Suggested business actions are hypotheses for validation; no revenue uplift or causal effect is asserted.

Türkçe: Bu repo gerçek verilerle hazırlanmış altı orta seviye proje içerir. Excel, Python, SQL, makine öğrenmesi ve R biyoinformatik çalışmalarında yöntemler, sonuçlar ve sınırlamalar İngilizce açıklanmıştır.
