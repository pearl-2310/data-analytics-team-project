"""
validate_project.py  --  Member 4 (Validation) 
=====================================================================
Independent checks on the whole project:
    A. Data quality (basic checks)
    (more sections are added step by step)

HOW TO RUN (from the repository ROOT folder):
    py .\\validation\\validate_project.py              (Windows)
    python validation/validate_project.py              (Mac / Linux)

OUTPUT:
    * a PASS / WARN / FAIL table on screen
    * validation/validation_results.csv   (same table, for your report)

Result meanings:
    PASS = check succeeded            WARN = works, but needs attention
    FAIL = real problem found         INFO = a number worth reporting
    SKIP = could not be run here
=====================================================================
"""

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = ROOT / "data-preparation" / "synthetic_pricing_data.csv"
NOTEBOOK = ROOT / "data-preparation" / "Synthetic_Panel_Generators_Experimental.ipynb"
CAUSAL = ROOT / "causal-analysis"
READY_FILE = CAUSAL / "analysis_ready_data.csv"
RESULTS = CAUSAL / "results"
BACKEND = ROOT / "dashboard-creation" / "backend" / "app.py"
FRONTEND = ROOT / "dashboard-creation" / "frontend"
OUT_CSV = Path(__file__).resolve().parent / "validation_results.csv"

TREATED = "Region_1"
T0 = pd.Timestamp("2025-03-10")          # treatment date used by the team
OUTCOMES = ["Revenue_Proxy", "Sales_Volume"]

# Ground truth: written in the data-generator notebook (price +15 %,
# sales fall by 2.5 units for every 1 unit of price). Only possible
# because the data is SIMULATED -- real data never has a known answer.
TRUE_PRICE_JUMP = 1.15
TRUE_PRICE_COEF = 2.5

rows = []


def record(area, check, result, detail):
    """Store one check result."""
    rows.append({"ID": f"{area}{sum(r['Area'] == area for r in rows) + 1}",
                 "Area": area, "Check": check, "Result": result, "Detail": detail})


def fit_weights(pre, target, donors):
    """Independent synthetic-control fit: weights >= 0, sum to 1.
    The objective is SCALED so the optimiser actually moves (see report)."""
    y = pre[target].to_numpy(float)
    X = pre[donors].to_numpy(float)
    scale = y.std() or 1.0
    n = len(donors)
    res = minimize(lambda w: np.mean(((y - X @ w) / scale) ** 2),
                   np.full(n, 1 / n), method="SLSQP",
                   bounds=[(0, 1)] * n,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
                   options={"maxiter": 3000, "ftol": 1e-12})
    return np.clip(res.x, 0, 1) / np.clip(res.x, 0, 1).sum()


def panel_of(df, outcome):
    return df.pivot(index="Date", columns="Region_ID", values=outcome).sort_index()


def rmse(x):
    return float(np.sqrt(np.mean(np.square(x))))


# =================================================================
# A. DATA QUALITY
# =================================================================
def check_data():
    A = "A"
    if not RAW_FILE.exists():
        record(A, "Raw dataset exists", "FAIL", f"Missing: {RAW_FILE}")
        return None, None
    raw = pd.read_csv(RAW_FILE, parse_dates=["Date"])
    record(A, "Raw dataset exists", "PASS", f"{len(raw):,} rows, {raw.shape[1]} columns")

    need = ["Date", "Region_ID", "Price", "Sales_Volume", "Competitor_Price",
            "Regional_Google_Trends_Index", "Treated", "Post_Treatment", "Treatment_Effect"]
    miss = [c for c in need if c not in raw.columns]
    record(A, "All required columns present", "FAIL" if miss else "PASS",
           f"Missing: {miss}" if miss else "9 of 9 columns found")

    nulls = int(raw.isnull().sum().sum())
    record(A, "No missing values", "PASS" if nulls == 0 else "FAIL", f"{nulls} missing cells")

    dups = int(raw.duplicated(["Date", "Region_ID"]).sum())
    record(A, "No duplicate Date + Region rows", "PASS" if dups == 0 else "FAIL", f"{dups} duplicates")

    per_region = raw.groupby("Region_ID").size()
    days = raw["Date"].nunique()
    full_range = pd.date_range(raw["Date"].min(), raw["Date"].max(), freq="D")
    balanced = per_region.nunique() == 1 and len(full_range) == days
    record(A, "Balanced daily panel (same days for every region)", "PASS" if balanced else "FAIL",
           f"{raw['Region_ID'].nunique()} regions x {days} days; "
           f"{raw['Date'].min().date()} to {raw['Date'].max().date()}")

    ok_range = (raw["Price"] > 0).all() and (raw["Sales_Volume"] >= 0).all()
    record(A, "Price > 0 and Sales >= 0", "PASS" if ok_range else "FAIL",
           f"Price {raw['Price'].min():.1f}-{raw['Price'].max():.1f}; "
           f"Sales {raw['Sales_Volume'].min():.0f}-{raw['Sales_Volume'].max():.0f}")

    treated_regions = sorted(raw.loc[raw["Treated"] == 1, "Region_ID"].unique())
    record(A, "Exactly one treated region (Region_1)", "PASS" if treated_regions == [TREATED] else "FAIL",
           f"Treated regions: {treated_regions}")

    post_start = raw.loc[raw["Post_Treatment"] == 1, "Date"].min()
    eff_ok = (raw["Treatment_Effect"] == raw["Treated"] * raw["Post_Treatment"]).all()
    record(A, "Treatment flags consistent; starts on 2025-03-10",
           "PASS" if (post_start == T0 and eff_ok) else "FAIL",
           f"Post period starts {post_start.date()}; Treatment_Effect = Treated x Post: {eff_ok}")

    # Treated region: price jump visible in data?
    r1 = raw[raw["Region_ID"] == TREATED].set_index("Date")["Price"]
    jump = r1.loc[T0] / r1.loc[T0 - pd.Timedelta(days=1)] - 1
    record(A, "Intervention is a PRICE INCREASE (not a cut)", "INFO",
           f"Region_1 price changes {jump:+.1%} on 2025-03-10 -> revenue rises, sales fall")

    # Pre-period similarity: are donors a sensible comparison group?
    sales = panel_of(raw, "Sales_Volume")
    pre = sales[sales.index < T0]
    corr = pre[TREATED].corr(pre.drop(columns=TREATED).mean(axis=1))
    record(A, "Region_1 moves with donors before treatment", "PASS" if corr > 0.5 else "WARN",
           f"Correlation with average donor (sales, pre-period): {corr:.2f}")

    return raw, None


# =================================================================
def main():
    print("Running validation ...\n")
    raw, ready = check_data()

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    pd.set_option("display.width", 250, "display.max_colwidth", 120)
    for _, r in df.iterrows():
        print(f"[{r['Result']:4s}] {r['ID']:4s} {r['Check']}\n         {r['Detail']}")
    print("\n" + "=" * 60)
    print(df["Result"].value_counts().to_string())
    print(f"\nSaved: {OUT_CSV}")


if __name__ == "__main__":
    main()
