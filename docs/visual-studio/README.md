# Projects in Visual Studio

These screenshots show the source, saved outputs and charts for the portfolio. The Python charts use Matplotlib code run in Visual Studio. The Excel dashboard and R figures are shown in their own applications; each project page links to its reproduction instructions.

- [Retail sales](#01-retail-sales)
- [Customer segmentation](#02-customer-segmentation)
- [Bike rental demand](#03-bike-rental-demand)
- [Excel bike operations](#04-excel-bike-operations)
- [Air quality pipeline](#05-air-quality-pipeline)
- [Leukemia expression analysis](#06-leukemia-expression-analysis)
- [Pasilla RNA-seq](#07-pasilla-rna-seq)
- [Diagnostic risk classification](#08-diagnostic-risk-classification)
- [Bank campaign propensity](#09-bank-campaign-propensity)

## Redraw the Python charts

Open [PortfolioCharts.pyproj](../../PortfolioCharts.pyproj) in Visual Studio and choose a Python environment with NumPy, pandas, Matplotlib and scikit-learn. **Start / F5** runs [plot_results.py](../../plot_results.py), saves all seven Python charts under [charts](charts), and opens them in seven Matplotlib windows. Open a generated PNG in Visual Studio to inspect it with the code.

The plotting step reads the saved CSV and JSON reports; it does not fit models or change the recorded analysis results. To display one chart in a live Matplotlib window, run `python plot_results.py --project 05 --show` from the repository root, replacing `05` with the project number. R and Excel use the separate instructions below.

## 01 Retail sales

[Project instructions](../../projects/01-retail-analytics/README.md)

1. Open [retail.sql](../../sql/retail.sql) to inspect the code.

   ![Retail sales source in Visual Studio](01-code.jpg)

2. Open [monthly_sales.csv](../../reports/monthly_sales.csv) to inspect the saved output.

   ![Retail sales output in Visual Studio](01-output.jpg)

3. Plot the monthly positive-sales totals, keeping the incomplete final month visible.

   ![Retail monthly sales chart in Visual Studio](01-chart.jpg)

## 02 Customer segmentation

[Project instructions](../../projects/02-customer-segmentation/README.md)

1. Open [run.py](../../run.py) to inspect the code.

   ![Customer segmentation source in Visual Studio](02-code.jpg)

2. Open [segment_profiles.csv](../../reports/segment_profiles.csv) to inspect the saved output.

   ![Customer segmentation output in Visual Studio](02-output.jpg)

3. Compare each group's customer count and median spending in the saved-profile chart. Group IDs are arbitrary labels.

   ![Customer counts and median spending by group in Visual Studio](02-chart.jpg)

## 03 Bike rental demand

[Project instructions](../../projects/03-bike-demand/README.md)

1. Open [run.py](../../run.py) to inspect the code.

   ![Bike rental demand source in Visual Studio](02-model-validation.jpg)

2. Open [bike_metrics.csv](../../reports/bike_metrics.csv) to inspect the saved output.

   ![Bike rental demand output in Visual Studio](03-output.jpg)

3. Compare the saved predictions with observed rentals on the chronological holdout.

   ![Observed and estimated rentals on later dates in Visual Studio](03-chart.jpg)

## 04 Excel bike operations

[Project instructions](../../projects/04-excel-bike-operations/README.md)

1. Open [build_workbook.mjs](../../projects/04-excel-bike-operations/build_workbook.mjs) to inspect the code.

   ![Excel bike operations source in Visual Studio](04-code.jpg)

2. Open [verification.json](../../projects/04-excel-bike-operations/verification.json) to inspect the saved output.

   ![Excel bike operations output in Visual Studio](04-output.jpg)

   The JSON shows the workbook validation results. Open the [generated workbook](../../projects/04-excel-bike-operations/bike_operations.xlsx) in Excel to use the dashboard.

3. Use the year and day-type selectors in Excel. The monthly, user-type and weather charts are native workbook charts linked to the same filtered calculations.

   ![The dashboard and editable charts in Microsoft Excel](../../projects/04-excel-bike-operations/excel-charts.jpg)

## 05 Air quality pipeline

[Project instructions](../../projects/05-python-air-quality/README.md)

1. Open [air_quality.py](../../projects/05-python-air-quality/air_quality.py) to inspect the code.

   ![Air quality pipeline source in Visual Studio](05-code.jpg)

2. Open [daily_summary.csv](../../projects/05-python-air-quality/reports/daily_summary.csv) to inspect the saved output.

   ![Air quality pipeline output in Visual Studio](05-output.jpg)

3. Plot the daily CO report with valid-hour coverage. Missing qualified means remain gaps in the line.

   ![Daily CO and measurement coverage in Visual Studio](05-chart.jpg)

## 06 Leukemia expression analysis

[Project instructions](../../projects/06-r-bioinformatics/README.md)

1. Open [analyze.R](../../projects/06-r-bioinformatics/analyze.R) to inspect the code.

   ![Leukemia expression analysis source in Visual Studio](06-code.jpg)

2. Open [summary.csv](../../projects/06-r-bioinformatics/reports/summary.csv) to inspect the saved output.

   ![Leukemia expression analysis output in Visual Studio](06-output.jpg)

3. In R, source [plot_results.R](../../projects/06-r-bioinformatics/plot_results.R) and call `show_pca()` or `show_volcano()` from the repository root. [analyze.R](../../projects/06-r-bioinformatics/analyze.R) also regenerates the statistics and saves the volcano figure.

   ![Volcano plotting code in R](../../projects/06-r-bioinformatics/r-volcano-code.jpg)

   ![Volcano-style expression plot displayed in R](../../projects/06-r-bioinformatics/r-volcano.jpg)

   The horizontal axis is the supplied-scale mean expression difference, AML minus ALL, not log₂ fold change. The vertical axis uses BH-adjusted p-values.

## 07 Pasilla RNA-seq

[Project instructions](../../projects/07-pasilla-rnaseq/README.md)

1. Open [analyze.py](../../projects/07-pasilla-rnaseq/analyze.py) to inspect the code.

   ![Pasilla RNA-seq source in Visual Studio](07-code.jpg)

2. Open [samples.csv](../../projects/07-pasilla-rnaseq/reports/samples.csv) to inspect the saved output.

   ![Pasilla RNA-seq output in Visual Studio](07-output.jpg)

3. Redraw the saved PCA coordinates with condition shown by color and sequencing layout by marker shape.

   ![Seven Pasilla libraries in the sample PCA chart in Visual Studio](07-chart.jpg)

## 08 Diagnostic risk classification

[Project instructions](../../projects/08-diagnostic-risk-classification/README.md)

1. Open [analyze.py](../../projects/08-diagnostic-risk-classification/analyze.py) to inspect the code.

   ![Diagnostic risk classification source in Visual Studio](08-code.jpg)

2. Open [model_metrics.csv](../../projects/08-diagnostic-risk-classification/reports/model_metrics.csv) to inspect the saved output.

   ![Diagnostic risk classification output in Visual Studio](08-output.jpg)

3. Inspect the ROC curve and confusion matrix from the saved holdout probabilities and flags. The threshold was selected on development data; this chart does not tune it on the holdout.

   ![Holdout ROC curve and confusion matrix in Visual Studio](08-chart.jpg)

## 09 Bank campaign propensity

[Project instructions](../../projects/09-bank-campaign-propensity/README.md)

1. Open [analyze.py](../../projects/09-bank-campaign-propensity/analyze.py) to inspect the temporal model comparison.

   ![Bank campaign analysis source in Visual Studio](09-code.jpg)

2. Run the analysis and inspect the test and holdout results.

   ![Bank campaign tests and holdout results in Visual Studio](09-debug-output.jpg)

3. Open the [holdout subscription rate chart](../../projects/09-bank-campaign-propensity/reports/holdout_subscription_rates.png) to compare the full holdout with the selected contacts.

   ![Holdout subscription rate chart in Visual Studio](09-chart.jpg)

   These are observed rates for the full holdout and its top-scored 15% subset. The comparison measures ranking concentration, not causal campaign uplift.
