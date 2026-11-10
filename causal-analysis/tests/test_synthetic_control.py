
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from synthetic_control import fit_synthetic_control


class TestSyntheticControl(unittest.TestCase):

    def setUp(self):
        self.pre_treatment = pd.DataFrame({
            "Region_1": [100, 110, 120, 130],
            "Region_2": [90, 100, 110, 120],
            "Region_3": [105, 115, 125, 135],
            "Region_4": [95, 105, 115, 125],
        })

        self.donors = ["Region_2", "Region_3", "Region_4"]

    def test_weights_are_non_negative(self):
        weights = fit_synthetic_control(
            self.pre_treatment, self.donors, "Revenue_Proxy"
        )
        self.assertTrue(np.all(weights >= 0))

    def test_weights_sum_to_one(self):
        weights = fit_synthetic_control(
            self.pre_treatment, self.donors, "Revenue_Proxy"
        )
        self.assertAlmostEqual(weights.sum(), 1.0)

    def test_correct_number_of_weights(self):
        weights = fit_synthetic_control(
            self.pre_treatment, self.donors, "Revenue_Proxy"
        )
        self.assertEqual(len(weights), len(self.donors))

    def test_weights_are_finite(self):
        """Check that all optimized weights are valid numbers."""

        weights = fit_synthetic_control(
            self.pre_treatment, self.donors, "Revenue_Proxy"
        )

        self.assertTrue(np.all(np.isfinite(weights)))

    def test_synthetic_control_matches_exact_combination(self):
        """Check whether donors can reproduce the treated region."""

        weights = fit_synthetic_control(
            self.pre_treatment, self.donors, "Revenue_Proxy"
        )

        synthetic = (
            self.pre_treatment[self.donors].to_numpy() @ weights
        )

        actual = self.pre_treatment["Region_1"].to_numpy()

        rmse = np.sqrt(np.mean((actual - synthetic) ** 2))

        self.assertLess(rmse, 0.01)


if __name__ == "__main__":
    unittest.main()
