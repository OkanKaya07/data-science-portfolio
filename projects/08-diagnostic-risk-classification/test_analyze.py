"""Small regression checks for the project workflow."""

import unittest

import numpy as np

from analyze import load_data, make_models, select_f2_threshold


class DiagnosticWorkflowTests(unittest.TestCase):
    def test_dataset_shape_and_target_encoding(self):
        features, target = load_data()
        self.assertEqual(features.shape, (569, 30))
        self.assertEqual(int(target.sum()), 212)
        self.assertEqual(set(target.unique()), {0, 1})

    def test_threshold_is_valid_and_not_worse_than_half_for_this_example(self):
        target = np.array([0, 0, 1, 1])
        probabilities = np.array([0.05, 0.45, 0.55, 0.95])
        threshold, score = select_f2_threshold(target, probabilities)
        self.assertGreaterEqual(threshold, 0.0)
        self.assertLessEqual(threshold, 1.0)
        self.assertGreaterEqual(score, 0.8)

    def test_all_estimators_are_pipelines(self):
        models = make_models()
        self.assertEqual(set(models), {"dummy_prior", "scaled_logistic_regression", "random_forest"})
        self.assertTrue(all("impute" in model.named_steps for model in models.values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
