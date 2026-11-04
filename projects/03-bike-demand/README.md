# 03 · Time-aware bike demand modeling

**Decision:** How much daily demand variation can calendar and weather explain?

## Step-by-step walkthrough

1. **Hold out the most recent dates.** I sorted 731 UCI Bike Sharing days by date and reserved the final fifth for evaluation. I excluded casual and registered counts because their sum gives away the target.
2. **Validate forward in time.** I used scikit-learn TimeSeriesSplit on the earlier dates, fit each model using past observations and scored it on the following window. I chose the model before opening the final holdout. [Open the implementation](../../run.py#L132-L136).

![Source walkthrough showing the input, method and exact code excerpt](walkthrough/source.png)

3. **Inspect the output.** Open [bike_metrics.csv](../../reports/bike_metrics.csv) and the [analysis figure](../../reports/bike_holdout.png). The browser capture below shows values from that artifact.
4. **Interpret the result.** Gradient boosting averaged 725 rentals of absolute error per day versus 2,290 for the training-mean baseline. Large gaps between lines are individual misses. Weather was observed the same day.

![Output walkthrough showing measured values and their interpretation](walkthrough/result.png)

## What I built

I compared scikit-learn models using four expanding time windows. On the final chronological holdout, gradient boosting missed by 725 rentals per day on average, compared with 2,290 for the training-mean baseline. The estimate uses observed weather.

```python
        for fold,(train,val) in enumerate(TimeSeriesSplit(n_splits=4).split(Xdev)):
            model.fit(Xdev.iloc[train],ydev.iloc[train])
            pred = model.predict(Xdev.iloc[val])
```

[See this code in context](../../run.py#L132) · [Inspect the results](../../reports/bike_metrics.csv)

## Reading the figure

The gap between the two lines is the daily prediction error. On 29 October 2012, the model predicted 3,169 rentals and only 22 occurred. The 725-rental average error hides misses of this size. The chart identifies a day to investigate but cannot explain why demand fell.

[Inspect the underlying result](../../reports/bike_predictions.csv)

## Evaluation design

The analysis uses all 731 daily observations, sorted by date. The first 80% are development data and the final 20% form an untouched chronological holdout during model selection. Four expanding-window folds compare a training-mean baseline, standardized Ridge regression, and histogram gradient boosting. The lowest mean validation MAE selects the model before final holdout evaluation. All model holdout scores are reported transparently; the winner is not reselected based on those scores.

Inputs include a calendar trend, cyclical annual features, holidays, working-day status, temperature, humidity, and wind. The target is `cnt`. `casual` and `registered` are excluded because their sum is the target. Row identifiers and raw dates are excluded.

**Scope:** Weather values are same-day observations. This is a conditional demand estimate, not a validated day-ahead forecasting system. A real forecast would need weather forecasts available at prediction time and a new backtest.

![Holdout](../../reports/bike_holdout.png)

## Deliverables

- [Expanding-window CV](../../reports/bike_cv.csv)
- [Holdout MAE, RMSE, R²](../../reports/bike_metrics.csv)
- [Date boundaries](../../reports/bike_split.json)
- [Predictions](../../reports/bike_predictions.csv)
- [Permutation importance](../../reports/bike_importance.csv)
- [Measured findings](../../reports/FINDINGS.md)

MAE is interpretable as average absolute daily rental error. RMSE emphasizes large misses; negative R² can reveal poor extrapolation. Permutation importance measures predictive sensitivity, not causality. Correlated weather and seasonal features complicate interpretation. The dataset contains only two years from one city, and the final holdout covers a particular season. Extend to rolling seasonal backtests and compare operational lag baselines before using the model for staffing or inventory decisions.

**Interview discussion:** Why avoid random splits? Why can tree models struggle with a growing trend? What would change for a genuine day-ahead forecast?
