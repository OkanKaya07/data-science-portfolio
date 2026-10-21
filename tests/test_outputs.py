"""Integration checks against generated evidence, not mock model scores."""
import json
from pathlib import Path
import unittest
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
REPORTS=ROOT/'reports'

class EvidenceTests(unittest.TestCase):
    def test_revenue_reconciliation(self):
        audit=json.loads((REPORTS/'retail_audit.json').read_text())
        monthly=pd.read_csv(REPORTS/'monthly_sales.csv')
        countries=pd.read_csv(REPORTS/'country_sales.csv')
        self.assertAlmostEqual(monthly.revenue_gbp.sum(),audit['gross_positive_sales_gbp'],places=4)
        self.assertAlmostEqual(countries.revenue_gbp.sum(),monthly.revenue_gbp.sum(),places=4)
        self.assertEqual(audit['raw_rows'],541909)

    def test_customer_accounting(self):
        profile=pd.read_csv(REPORTS/'segment_profiles.csv')
        validation=json.loads((REPORTS/'segment_validation.json').read_text())
        self.assertEqual(profile.customers.sum(),validation['customers'])
        self.assertAlmostEqual(profile.revenue_share_pct.sum(),100,places=6)
        self.assertEqual(len(profile),validation['selected_k'])

    def test_time_boundaries_and_leakage(self):
        split=json.loads((REPORTS/'bike_split.json').read_text())
        self.assertLess(split['train_end'],split['test_start'])
        folds=pd.read_csv(REPORTS/'bike_cv.csv')
        self.assertTrue((folds.train_end < folds.validation_start).all())
        importance=pd.read_csv(REPORTS/'bike_importance.csv')
        self.assertFalse(set(importance.feature)&{'cnt','casual','registered','instant'})
        predictions=pd.read_csv(REPORTS/'bike_predictions.csv')
        self.assertEqual(len(predictions),split['test_rows'])
        self.assertFalse(predictions.isna().any().any())
        self.assertTrue(predictions.date.is_monotonic_increasing)

    def test_selected_model_and_metrics(self):
        cv=pd.read_csv(REPORTS/'bike_cv.csv')
        metrics=pd.read_csv(REPORTS/'bike_metrics.csv')
        winner=cv.groupby('model').mae.mean().idxmin()
        self.assertEqual(metrics.loc[metrics.selected_by_cv,'model'].tolist(),[winner])
        pred=pd.read_csv(REPORTS/'bike_predictions.csv')
        mae=(pred.actual-pred.predicted).abs().mean()
        self.assertAlmostEqual(mae,metrics.set_index('model').loc[winner,'test_mae'],places=6)

if __name__=='__main__': unittest.main()
