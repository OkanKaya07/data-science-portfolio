# Diagnostic risk classification

[← All projects](../../README.md#projects) · [Source code](analyze.py) · [Model comparison](reports/model_metrics.csv) · [Run record](reports/run_summary.json)

**Tools** · Python · pandas · NumPy · scikit-learn

This compact project demonstrates a leakage-aware binary-classification workflow: compare a baseline and two models on development data, choose a model using cross-validation, select a triage threshold using out-of-fold predictions, and evaluate once on an untouched holdout set.

> **Important:** this is an educational analysis of a small historical dataset. It is not a clinical tool and must not be used to diagnose, screen, or make treatment decisions.

## Questions

1. Do a scaled logistic-regression model and a random forest improve on a class-prior baseline?
2. What is the ranking and triage performance on data excluded from model selection?
3. How does a recall-weighted threshold change the errors that would be sent for review?

## Data

The workflow uses the **Breast Cancer Wisconsin (Diagnostic)** data made available by the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic), loaded reproducibly through `sklearn.datasets.load_breast_cancer`.

There are **569 observations**, **30 numeric measurements**, **212 malignant** and **357 benign** cases. The original scikit-learn target uses `0` for malignant; the script explicitly recodes the target so `1` means malignant throughout. No patient identifiers are present or added to the project.

## Validation design

1. **Hold out 25% first.** A stratified split reserves 143 rows before choosing a model or threshold.
2. **Compare models on the remaining 426 rows.** A dummy class-prior baseline, scaled logistic regression, and random forest each use five shuffled stratified folds.
3. **Keep preprocessing inside pipelines.** Imputation and scaling are fit separately within each fold, avoiding information from validation rows leaking into training transformations.
4. **Select by mean cross-validated ROC AUC.** Logistic regression was selected on the development data.
5. **Set the triage threshold only on development out-of-fold probabilities.** The threshold maximizes the F2 score, which weights recall more heavily than precision. The holdout is then evaluated once.

## Measured results

| Model | Development CV ROC AUC (mean ± SD) | Development CV average precision | Development CV balanced accuracy |
|---|---:|---:|---:|
| Class-prior baseline | 0.500 ± 0.000 | 0.373 | 0.500 |
| Scaled logistic regression | **0.991 ± 0.011** | **0.990** | **0.964** |
| Random forest | 0.988 ± 0.008 | 0.986 | 0.952 |

The selected logistic-regression pipeline used an out-of-fold threshold of **0.402**. On the untouched 143-row holdout, it achieved **ROC AUC 0.995**, **average precision 0.993**, **balanced accuracy 0.976**, **malignant recall 0.962**, **malignant precision 0.981**, and **F2 0.966**.

At that threshold, the holdout confusion counts were **89 true negatives**, **1 false positive**, **2 false negatives**, and **51 true positives**. Those are descriptive results from one split—not a performance guarantee.

## Outputs

| File | Contents |
|---|---|
| [model_metrics.csv](reports/model_metrics.csv) | Cross-validation metrics for all candidates and one holdout evaluation for the selected model |
| [holdout_predictions.csv](reports/holdout_predictions.csv) | Row index, true class, predicted malignant probability, and threshold flag for the held-out rows |
| [run_summary.json](reports/run_summary.json) | Data source, split size, package versions, threshold and measured evaluation values |

## Reproduce

Tested with Python 3.12.14, NumPy 2.3.5, pandas 2.2.3, and scikit-learn 1.8.0.

```sh
cd projects/08-diagnostic-risk-classification
python -m pip install -r requirements.txt
python -m unittest discover -s . -p 'test_*.py' -v
python analyze.py
```

The script uses a fixed seed (`42`), writes all reported outputs, and checks that development and holdout rows do not overlap. Exact floating-point output can differ slightly on another platform or library release.

## Limitations and responsible interpretation

- The data are small, historic, and may not represent contemporary patients, devices, populations, or clinical workflows.
- Feature measurements and diagnoses alone omit the context required for real decision-making. The data cannot establish causality or treatment benefit.
- Model selection and the F2 threshold use the same development set; the single holdout is a useful safeguard, but not independent external validation.
- The high values are specific to this dataset and split. They must not be interpreted as clinical performance.
- In a real review system, threshold choice should reflect the costs of false negatives and false positives, be validated externally, and be monitored for calibration and subgroup performance.

## What I learned

- A strong score is less meaningful unless the split, preprocessing, selection rule and threshold procedure are documented.
- `Pipeline` objects make it practical to keep transformations inside cross-validation rather than scaling the full dataset first.
- ROC AUC evaluates ranking; it does not choose an operating threshold. An explicit threshold should match the review objective and its error costs.
- Reporting the baseline and error counts makes a model comparison more auditable than showing one headline score.

[See the code and output in Visual Studio](../../docs/visual-studio/README.md#08-diagnostic-risk-classification).
