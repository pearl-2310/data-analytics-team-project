from pathlib import Path
import unittest

import pandas as pd


# Locate the original dataset
PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data-preparation"
    / "synthetic_pricing_data.csv"
)


class TestDatasetLoading(unittest.TestCase):

    def test_dataset_file_exists(self):
        """Check whether the original CSV file exists."""

        self.assertTrue(
            INPUT_FILE.exists(),
            "Synthetic pricing dataset was not found."
        )

    def test_dataset_loads_successfully(self):
        """Check whether Pandas can load the CSV file."""

        df = pd.read_csv(INPUT_FILE)

        self.assertIsNotNone(df)
        self.assertFalse(df.empty)

    def test_dataset_has_expected_columns(self):
        """Check whether all required columns are available."""

        df = pd.read_csv(INPUT_FILE)

        expected_columns = [
            "Date",
            "Region_ID",
            "Price",
            "Sales_Volume",
            "Competitor_Price",
            "Regional_Google_Trends_Index",
            "Treated",
            "Post_Treatment",
            "Treatment_Effect",
        ]

        for column in expected_columns:
            self.assertIn(column, df.columns)


if __name__ == "__main__":
    unittest.main()