
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from synthetic_control import fit_synthetic_control


class TestSyntheticControlValidation(unittest.TestCase):

    def setUp(self):
        self.pre_treatment = pd.DataFrame({
            "Region_1": [100, 110, 120, 130],
            "Region_2": [90, 100, 110, 120],
            "Region_3": [105, 115, 125, 135],
            "Region_4": [95, 105, 115, 125],
        })

        self.donors = ["Region_2", "Region_3", "Region_4"]

    def test_empty_dataframe_raises_error(self):
        with self.assertRaises(ValueError):
            fit_synthetic_control(
                pd.DataFrame(),
                self.donors,
                "Revenue_Proxy",
            )

    def test_missing_treated_region_raises_error(self):
        data = self.pre_treatment.drop(columns=["Region_1"])

        with self.assertRaises(ValueError):
            fit_synthetic_control(
                data,
                self.donors,
                "Revenue_Proxy",
            )

    def test_empty_donor_list_raises_error(self):
        with self.assertRaises(ValueError):
            fit_synthetic_control(
                self.pre_treatment,
                [],
                "Revenue_Proxy",
            )

    def test_missing_donor_region_raises_error(self):
        with self.assertRaises(ValueError):
            fit_synthetic_control(
                self.pre_treatment,
                ["Region_2", "Region_5"],
                "Revenue_Proxy",
            )

    def test_treated_region_in_donor_list_raises_error(self):
        with self.assertRaises(ValueError):
            fit_synthetic_control(
                self.pre_treatment,
                ["Region_1", "Region_2"],
                "Revenue_Proxy",
            )

    def test_duplicate_donor_regions_raise_error(self):
        with self.assertRaises(ValueError):
            fit_synthetic_control(
                self.pre_treatment,
                ["Region_2", "Region_2"],
                "Revenue_Proxy",
            )

    def test_non_numeric_values_raise_error(self):
        data = self.pre_treatment.copy()
        data["Region_2"] = ["invalid", 100, 110, 120]

        with self.assertRaises(ValueError):
            fit_synthetic_control(
                data,
                self.donors,
                "Revenue_Proxy",
            )

    def test_missing_values_raise_error(self):
        data = self.pre_treatment.copy()
        data.loc[0, "Region_2"] = np.nan

        with self.assertRaises(ValueError):
            fit_synthetic_control(
                data,
                self.donors,
                "Revenue_Proxy",
            )

    def test_infinite_values_raise_error(self):
        data = self.pre_treatment.copy()
        data["Region_2"] = data["Region_2"].astype(float)
        data.loc[0, "Region_2"] = np.inf

        with self.assertRaises(ValueError):
            fit_synthetic_control(
                data,
                self.donors,
                "Revenue_Proxy",
            )
    def test_non_dataframe_input_raises_error(self):
        with self.assertRaises(TypeError):
            fit_synthetic_control(
                [[100, 110]],
                self.donors,
                "Revenue_Proxy",
            )


if __name__ == "__main__":
    unittest.main()
