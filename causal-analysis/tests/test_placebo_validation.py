
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from placebo_test import evaluate_region


class TestPlaceboValidation(unittest.TestCase):

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

    def test_missing_target_region(self):
        with self.assertRaises(KeyError):
            evaluate_region(
                self.panel,
                "Region_4",
                ["Region_1", "Region_3"],
                "Revenue_Proxy"
            )

    def test_missing_donor_region(self):
        with self.assertRaises(KeyError):
            evaluate_region(
                self.panel,
                "Region_2",
                ["Region_4"],
                "Revenue_Proxy"
            )

    def test_empty_donor_list(self):
        with self.assertRaises((ValueError, ZeroDivisionError)):
            evaluate_region(
                self.panel,
                "Region_2",
                [],
                "Revenue_Proxy"
            )


if __name__ == "__main__":
    unittest.main()
