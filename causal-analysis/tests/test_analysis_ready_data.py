from pathlib import Path
import unittest

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "causal-analysis"
    / "analysis_ready_data.csv"
)


class TestAnalysisReadyData(unittest.TestCase):

    def setUp(self):
        """Load the analysis-ready dataset."""

        self.assertTrue(INPUT_FILE.exists())
        self.df = pd.read_csv(INPUT_FILE)

    def test_revenue_proxy_column_exists(self):
        """Check whether Revenue_Proxy is available."""

        self.assertIn("Revenue_Proxy", self.df.columns)

    def test_revenue_proxy_calculation(self):
        """Verify Revenue_Proxy = Price * Sales_Volume."""

        expected = self.df["Price"] * self.df["Sales_Volume"]

        self.assertTrue(
            np.allclose(self.df["Revenue_Proxy"], expected)
        )

    def test_no_missing_values(self):
        """Check whether the prepared dataset has missing values."""

        self.assertEqual(self.df.isnull().sum().sum(), 0)


if __name__ == "__main__":
    unittest.main()