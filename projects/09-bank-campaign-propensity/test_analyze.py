"""Regression checks for data integrity, leakage exclusion, and capacity selection."""

import unittest

import numpy as np

from analyze import CAPACITY_FRACTION, load_data, prepare_features, top_capacity_mask, targeting_metrics


class BankCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = load_data()
        cls.features, cls.target = prepare_features(cls.raw)

    def test_verified_table_shape_and_target_count(self):
        self.assertEqual(self.raw.shape, (41_188, 21))
        self.assertEqual(int(self.target.sum()), 4_640)
        self.assertEqual(set(self.target.unique()), {0, 1})

    def test_post_call_duration_is_not_a_feature(self):
        self.assertNotIn("duration", self.features.columns)
        self.assertIn("prior_campaign_contacts", self.features.columns)
        self.assertIn("previously_contacted", self.features.columns)

    def test_capacity_policy_selects_exactly_the_requested_count(self):
        scores = np.array([0.10, 0.90, 0.40, 0.70, 0.20, 0.60, 0.30])
        selected = top_capacity_mask(scores, fraction=0.30)
        self.assertEqual(int(selected.sum()), 3)
        self.assertTrue(selected[1])
        self.assertTrue(selected[3])
        metrics = targeting_metrics(np.array([0, 1, 0, 1, 0, 1, 0]), scores, fraction=0.30)
        self.assertEqual(metrics["selected_rows"], 3)
        self.assertAlmostEqual(metrics["selected_fraction"], 3 / 7)

    def test_default_capacity_is_fifteen_percent(self):
        self.assertEqual(CAPACITY_FRACTION, 0.15)


if __name__ == "__main__":
    unittest.main(verbosity=2)
