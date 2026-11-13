
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from synthetic_control import fit_synthetic_control


class TestOptimizerValidation(unittest.TestCase):

    def setUp(self):
        self.pre_treatment = pd.DataFrame({
            "Region_1": [100, 110, 120, 130],
            "Region_2": [90, 100, 110, 120],
            "Region_3": [105, 115, 125, 135],
            "Region_4": [95, 105, 115, 125],
        })

        self.donors = ["Region_2", "Region_3", "Region_4"]

    @patch("synthetic_control.minimize")
    def test_negative_weights_raise_error(self, mock_minimize):
        mock_minimize.return_value = SimpleNamespace(
            success=True,
            x=np.array([-0.1, 0.6, 0.5]),
            message="Optimization successful",
        )

        with self.assertRaises(RuntimeError):
            fit_synthetic_control(
                self.pre_treatment,
                self.donors,
                "Revenue_Proxy",
            )

    @patch("synthetic_control.minimize")
    def test_weights_not_summing_to_one_raise_error(self, mock_minimize):
        mock_minimize.return_value = SimpleNamespace(
            success=True,
            x=np.array([0.2, 0.2, 0.2]),
            message="Optimization successful",
        )

        with self.assertRaises(RuntimeError):
            fit_synthetic_control(
                self.pre_treatment,
                self.donors,
                "Revenue_Proxy",
            )

    @patch("synthetic_control.minimize")
    def test_incorrect_number_of_weights_raises_error(self, mock_minimize):
        mock_minimize.return_value = SimpleNamespace(
            success=True,
            x=np.array([0.5, 0.5]),
            message="Optimization successful",
        )

        with self.assertRaises(RuntimeError):
            fit_synthetic_control(
                self.pre_treatment,
                self.donors,
                "Revenue_Proxy",
            )


if __name__ == "__main__":
    unittest.main()
