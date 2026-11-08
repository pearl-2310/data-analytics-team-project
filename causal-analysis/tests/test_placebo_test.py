
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

# Add the causal-analysis folder to Python's import path.
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from placebo_test import evaluate_region


class TestPlaceboAnalysis(unittest.TestCase):

    def setUp(self):
        """Create a small sample panel dataset."""

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

    def test_placebo_analysis_returns_expected_metrics(self):
        """Check whether placebo analysis returns all expected metrics."""

        result = evaluate_region(
            self.panel,
            "Region_2",
            ["Region_1", "Region_3"],
            "Revenue_Proxy"
        )

        expected_keys = [
            "Outcome",
            "Target_Region",
            "Pre_Treatment_RMSE",
            "Post_Treatment_RMSE",
            "Post_Pre_RMSE_Ratio",
            "Average_Post_Treatment_Gap",
        ]

        for key in expected_keys:
            self.assertIn(key, result)

    def test_placebo_analysis_uses_correct_region(self):
        """Check whether the selected region is correctly recorded."""

        result = evaluate_region(
            self.panel,
            "Region_2",
            ["Region_1", "Region_3"],
            "Revenue_Proxy"
        )

        self.assertEqual(result["Target_Region"], "Region_2")
        self.assertEqual(result["Outcome"], "Revenue_Proxy")

    def test_placebo_metrics_are_valid(self):
        """Check whether RMSE metrics are non-negative."""

        result = evaluate_region(
            self.panel,
            "Region_2",
            ["Region_1", "Region_3"],
            "Revenue_Proxy"
        )

        self.assertGreaterEqual(result["Pre_Treatment_RMSE"], 0)
        self.assertGreaterEqual(result["Post_Treatment_RMSE"], 0)


if __name__ == "__main__":
    unittest.main()
