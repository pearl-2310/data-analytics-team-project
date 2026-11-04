import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

# Add the causal-analysis folder to the Python path.
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from synthetic_control import fit_synthetic_control


class TestSyntheticControl(unittest.TestCase):

    def test_weights_are_non_negative(self):
        """Check that donor weights are not negative."""

        pre_treatment = pd.DataFrame({
            "Region_1": [100, 110, 120, 130],
            "Region_2": [90, 100, 110, 120],
            "Region_3": [105, 115, 125, 135],
            "Region_4": [95, 105, 115, 125],
        })

        donors = ["Region_2", "Region_3", "Region_4"]

        weights = fit_synthetic_control(
            pre_treatment,
            donors,
            "Revenue_Proxy",
        )

        self.assertTrue(np.all(weights >= 0))

    def test_weights_sum_to_one(self):
        """Check that donor weights add up to one."""

        pre_treatment = pd.DataFrame({
            "Region_1": [100, 110, 120, 130],
            "Region_2": [90, 100, 110, 120],
            "Region_3": [105, 115, 125, 135],
            "Region_4": [95, 105, 115, 125],
        })

        donors = ["Region_2", "Region_3", "Region_4"]

        weights = fit_synthetic_control(
            pre_treatment,
            donors,
            "Revenue_Proxy",
        )

        self.assertAlmostEqual(weights.sum(), 1.0)

    def test_correct_number_of_weights(self):
        """Check that one weight is returned for each donor."""

        pre_treatment = pd.DataFrame({
            "Region_1": [100, 110, 120, 130],
            "Region_2": [90, 100, 110, 120],
            "Region_3": [105, 115, 125, 135],
            "Region_4": [95, 105, 115, 125],
        })

        donors = ["Region_2", "Region_3", "Region_4"]

        weights = fit_synthetic_control(
            pre_treatment,
            donors,
            "Revenue_Proxy",
        )

        self.assertEqual(len(weights), len(donors))


if __name__ == "__main__":
    unittest.main()