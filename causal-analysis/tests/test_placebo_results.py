
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
RESULTS_FILE = PROJECT_DIR / "results" / "placebo_test_results.csv"

EXPECTED_COLUMNS = [
    "Outcome",
    "Target_Region",
    "Pre_Treatment_RMSE",
    "Post_Treatment_RMSE",
    "Post_Pre_RMSE_Ratio",
    "Average_Post_Treatment_Gap",
]

EXPECTED_OUTCOMES = {"Revenue_Proxy", "Sales_Volume"}
EXPECTED_REGIONS = {
    "Region_1",
    "Region_2",
    "Region_3",
    "Region_4",
    "Region_5",
    "Region_6",
    "Region_7",
    "Region_8",
    "Region_9",
    "Region_10",
}


class TestPlaceboResults(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load the generated placebo results once for all tests."""

        if not RESULTS_FILE.exists():
            raise FileNotFoundError(
                f"Placebo results file not found: {RESULTS_FILE}. "
                "Run placebo_test.py first."
            )

        cls.results = pd.read_csv(RESULTS_FILE)

    def test_results_file_has_expected_columns(self):
        """Check that all expected diagnostic columns are present."""

        self.assertEqual(
            list(self.results.columns),
            EXPECTED_COLUMNS
        )

    def test_results_contain_both_outcomes(self):
        """Check that both analysis outcomes are represented."""

        actual_outcomes = set(self.results["Outcome"])

        self.assertEqual(actual_outcomes, EXPECTED_OUTCOMES)

    def test_all_regions_are_present_for_each_outcome(self):
        """Check that treated and placebo regions are included."""

        for outcome in EXPECTED_OUTCOMES:
            outcome_regions = set(
                self.results.loc[
                    self.results["Outcome"] == outcome,
                    "Target_Region"
                ]
            )

            self.assertEqual(outcome_regions, EXPECTED_REGIONS)

    def test_each_outcome_has_ten_region_results(self):
        """Check that each outcome has one result per region."""

        counts = self.results.groupby("Outcome").size()

        for outcome in EXPECTED_OUTCOMES:
            self.assertEqual(counts[outcome], 10)

    def test_diagnostic_metrics_are_non_negative_where_required(self):
        """Check RMSE values and ratios are non-negative."""

        self.assertTrue(
            (self.results["Pre_Treatment_RMSE"] >= 0).all()
        )

        self.assertTrue(
            (self.results["Post_Treatment_RMSE"] >= 0).all()
        )

        valid_ratios = self.results[
            "Post_Pre_RMSE_Ratio"
        ].dropna()

        self.assertTrue((valid_ratios >= 0).all())

    def test_diagnostic_metrics_contain_no_infinite_values(self):
        """Check that numerical diagnostic metrics are not infinite."""

        metric_columns = [
            "Pre_Treatment_RMSE",
            "Post_Treatment_RMSE",
            "Post_Pre_RMSE_Ratio",
            "Average_Post_Treatment_Gap",
        ]

        values = self.results[metric_columns].to_numpy(dtype=float)

        self.assertTrue(np.isfinite(values).all())


if __name__ == "__main__":
    unittest.main()
