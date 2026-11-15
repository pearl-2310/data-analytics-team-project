
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from placebo_test import evaluate_region


class TestPlaceboDiagnostics(unittest.TestCase):

    def setUp(self):
        dates = pd.date_range(
            start="2025-01-01",
            end="2025-04-01",
            freq="D"
        )

        self.panel = pd.DataFrame(
            {
                "Region_1": np.linspace(100, 120, len(dates)),
                "Region_2": np.linspace(95, 115, len(dates)),
                "Region_3": np.linspace(105, 125, len(dates)),
            },
            index=dates
        )

    def test_diagnostic_metrics_are_finite(self):
        """Valid input should produce finite diagnostic metrics."""

        result = evaluate_region(
            self.panel,
            "Region_2",
            ["Region_1", "Region_3"],
            "Revenue_Proxy"
        )

        metric_keys = [
            "Pre_Treatment_RMSE",
            "Post_Treatment_RMSE",
            "Average_Post_Treatment_Gap",
        ]

        for key in metric_keys:
            self.assertTrue(np.isfinite(result[key]), key)

        self.assertTrue(
            np.isfinite(result["Post_Pre_RMSE_Ratio"])
        )

    def test_zero_pre_treatment_rmse_returns_nan_ratio(self):
        """A zero pre-treatment RMSE should not produce an infinite ratio."""

        dates = self.panel.index

        exact_panel = pd.DataFrame(
            {
                "Region_1": np.linspace(100, 120, len(dates)),
                "Region_2": np.linspace(100, 120, len(dates)),
                "Region_3": np.linspace(90, 110, len(dates)),
            },
            index=dates
        )

        result = evaluate_region(
            exact_panel,
            "Region_2",
            ["Region_1"],
            "Revenue_Proxy"
        )

        self.assertAlmostEqual(
            result["Pre_Treatment_RMSE"],
            0.0,
            places=6
        )

        self.assertTrue(
            np.isnan(result["Post_Pre_RMSE_Ratio"])
        )

        self.assertTrue(
            np.isfinite(result["Post_Treatment_RMSE"])
        )


if __name__ == "__main__":
    unittest.main()
