"""
validate_project.py  --  Member 4 (Validation) 
=====================================================================
Independent checks on the whole project:
    A. Data quality           B. Reproducibility
    C. Synthetic Control      D. Placebo tests
    (more sections are added step by step)

HOW TO RUN (from the repository ROOT folder):
    py .\\validation\\validate_project.py              (Windows)
    python validation/validate_project.py              (Mac / Linux)

Optional:  --skip-rerun   (skips B, which re-runs the team's scripts; faster)

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

    # Analysis-ready file
    if not READY_FILE.exists():
        record(A, "Analysis-ready file exists", "FAIL", f"Missing: {READY_FILE}")
        return raw, None
    ready = pd.read_csv(READY_FILE, parse_dates=["Date"])
    same_cols = ready[raw.columns].equals(raw) or np.allclose(
        ready[raw.select_dtypes("number").columns].to_numpy(),
        raw[raw.select_dtypes("number").columns].to_numpy())
    rev_ok = np.allclose(ready["Revenue_Proxy"], ready["Price"] * ready["Sales_Volume"])
    record(A, "Analysis-ready data = raw data + Revenue_Proxy (Price x Sales)",
           "PASS" if (same_cols and rev_ok) else "FAIL",
           f"Original columns unchanged: {same_cols}; Revenue_Proxy correct: {rev_ok}")
    record(A, "Revenue_Proxy is mechanical, not independent",
           "INFO", "Revenue_Proxy = Price x Sales, so a price rise lifts it by construction; "
                   "judge the demand effect from Sales_Volume")

    # Notebook regenerates the CSV?
    if NOTEBOOK.exists():
        try:
            nb = json.load(open(NOTEBOOK, encoding="utf-8"))
            code = next("".join(c["source"]) for c in nb["cells"]
                        if c["cell_type"] == "code" and "treatment_day = 800" in "".join(c["source"]))
            ns = {"display": lambda *a, **k: None}      # 'display' exists only inside Jupyter
            import contextlib, io, os
            # The notebook cell ends with .to_csv(...). Run it inside a throw-away folder so
            # this validation NEVER writes a file into your repository.
            scratch = tempfile.mkdtemp(prefix="nbrun_")
            here = os.getcwd()
            try:
                os.chdir(scratch)
                with contextlib.redirect_stdout(io.StringIO()):
                    exec(code, ns)
            finally:
                os.chdir(here)
                shutil.rmtree(scratch, ignore_errors=True)
            gen = ns["synthetic_data"]
            num = raw.select_dtypes("number").columns
            diff = float(np.abs(gen[num].to_numpy() - raw[num].to_numpy()).max())
            record(A, "Notebook generator reproduces the CSV exactly",
                   "PASS" if diff < 1e-6 else "FAIL", f"Largest difference: {diff:.2e}")
        except Exception as exc:                      # noqa: BLE001
            record(A, "Notebook generator reproduces the CSV exactly", "SKIP", f"Could not run: {exc}")
    return raw, ready


# =================================================================
# B. REPRODUCIBILITY
# =================================================================
def check_reproducibility():
    B = "B"
    tmp = Path(tempfile.mkdtemp(prefix="validate_"))
    try:
        copy = tmp / "repo"
        shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__"))
        for script in ["prepare_data.py", "synthetic_control.py", "placebo_test.py"]:
            run = subprocess.run([sys.executable, str(copy / "causal-analysis" / script)],
                                 capture_output=True, text=True, cwd=copy)
            ok = run.returncode == 0
            record(B, f"{script} runs without errors", "PASS" if ok else "FAIL",
                   "exit code 0" if ok else run.stderr.strip().splitlines()[-1][:200])
            if not ok:
                return
        worst = 0.0
        files = [Path("analysis_ready_data.csv")] + [Path("results") / f.name for f in sorted(RESULTS.glob("*.csv"))]
        for rel in files:
            a = pd.read_csv(CAUSAL / rel)
            b = pd.read_csv(copy / "causal-analysis" / rel)
            num = a.select_dtypes("number").columns
            if a.shape != b.shape:
                record(B, f"Re-run output matches saved: {rel.name}", "FAIL", "shape differs")
                continue
            worst = max(worst, float(np.abs(a[num].to_numpy() - b[num].to_numpy()).max()))
        record(B, "Re-run reproduces every saved result file", "PASS" if worst < 1e-3 else "FAIL",
               f"{len(files)} CSV files compared; largest difference {worst:.2e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# =================================================================
# C. SYNTHETIC CONTROL
# =================================================================
def check_synthetic_control(ready):
    C = "C"
    w = pd.read_csv(RESULTS / "synthetic_control_weights.csv")
    summ = pd.read_csv(RESULTS / "synthetic_control_summary.csv").set_index("Outcome")
    out = {}

    for outcome in OUTCOMES:
        wo = w[w["Outcome"] == outcome]
        valid = (wo["Weight"] >= -1e-9).all() and abs(wo["Weight"].sum() - 1) < 1e-6
        record(C, f"{outcome}: weights are >= 0 and sum to 1", "PASS" if valid else "FAIL",
               f"sum = {wo['Weight'].sum():.6f}, min = {wo['Weight'].min():.2e}")

        panel = panel_of(ready, outcome)
        donors = sorted(c for c in panel.columns if c != TREATED)
        pre = panel[panel.index < T0]
        post_mask = panel.index >= T0

        # independent re-fit
        mine = fit_weights(pre, TREATED, donors)
        gap_mine = panel[TREATED].to_numpy() - panel[donors].to_numpy() @ mine
        saved_w = wo.set_index("Donor_Region").loc[donors, "Weight"].to_numpy()
        gap_saved = panel[TREATED].to_numpy() - panel[donors].to_numpy() @ saved_w
        pre_saved, pre_mine = rmse(gap_saved[~post_mask]), rmse(gap_mine[~post_mask])
        eff_saved, eff_mine = gap_saved[post_mask].mean(), gap_mine[post_mask].mean()
        out[outcome] = dict(panel=panel, donors=donors, w=mine, eff_mine=eff_mine, eff_saved=eff_saved)

        equal = np.allclose(saved_w, 1 / len(donors), atol=1e-3)
        suboptimal = pre_saved > pre_mine * 1.01
        record(C, f"{outcome}: saved weights are optimal",
               "FAIL" if suboptimal else "PASS",
               (f"Saved weights are all {1/len(donors):.4f} (= plain average of donors); " if equal else "")
               + f"pre-treatment RMSE saved {pre_saved:,.2f} vs re-fit {pre_mine:,.2f}")

        rel = pre_saved / pre[TREATED].mean()
        record(C, f"{outcome}: pre-treatment fit is close (RMSE < 5% of level)",
               "PASS" if rel < 0.05 else "WARN", f"RMSE {pre_saved:,.2f} = {rel:.1%} of average level")

        diff = abs(eff_saved - eff_mine) / abs(eff_mine)
        record(C, f"{outcome}: average post-treatment gap matches independent re-fit",
               "PASS" if diff < 0.02 else "FAIL",
               f"team {eff_saved:,.2f} vs re-fit {eff_mine:,.2f} ({diff:.1%} apart)")

        # summary file vs daily file (internal consistency)
        daily = pd.read_csv(RESULTS / f"{outcome}_synthetic_control.csv", parse_dates=["Date"])
        s = summ.loc[outcome]
        d_avg = daily.loc[daily["Date"] >= T0, "Gap"].mean()
        d_cum = daily.loc[daily["Date"] >= T0, "Gap"].sum()
        d_rmse = rmse(daily.loc[daily["Date"] < T0, "Gap"])
        ok = (np.isclose(d_avg, s["Average_Post_Treatment_Gap"], rtol=1e-6)
              and np.isclose(d_cum, s["Cumulative_Post_Treatment_Gap"], rtol=1e-6)
              and np.isclose(d_rmse, s["Pre_Treatment_RMSE"], rtol=1e-6))
        record(C, f"{outcome}: summary file matches daily results file", "PASS" if ok else "FAIL",
               f"avg gap {d_avg:,.2f}, cumulative {d_cum:,.2f}, pre-RMSE {d_rmse:,.2f}")

    # same treatment date in every file?
    dates = {}
    for name, path in [("synthetic_control.py", CAUSAL / "synthetic_control.py"),
                       ("placebo_test.py", CAUSAL / "placebo_test.py"),
                       ("backend app.py", BACKEND)]:
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        dates[name] = "2025-03-10" in text
    record(C, "Same treatment date (2025-03-10) in all scripts", "PASS" if all(dates.values()) else "FAIL",
           str(dates) + " -- note: hard-coded in 3 places, so change all three together")
    return out


# =================================================================
# D. PLACEBO TESTS
# =================================================================
def check_placebo(ready, sc):
    D = "D"
    plc = pd.read_csv(RESULTS / "placebo_test_results.csv")
    summ = pd.read_csv(RESULTS / "synthetic_control_summary.csv").set_index("Outcome")

    for outcome in OUTCOMES:
        p = plc[plc["Outcome"] == outcome]
        ratio = p.set_index("Target_Region")["Post_Pre_RMSE_Ratio"]
        rank = int((ratio > ratio[TREATED]).sum() + 1)
        n = len(ratio)
        others = ratio.drop(TREATED)
        record(D, f"{outcome}: Region_1 is the most extreme of {n} regions",
               "PASS" if rank == 1 else "WARN",
               f"Region_1 post/pre RMSE ratio {ratio[TREATED]:.2f} (rank {rank}/{n}); "
               f"placebo regions {others.min():.2f}-{others.max():.2f}")
        record(D, f"{outcome}: permutation p-value", "INFO",
               f"p = {rank}/{n} = {rank/n:.2f}. With only {n} regions the smallest possible p-value is "
               f"{1/n:.2f}, so it can never reach 0.05 -- report it as 'most extreme of {n}', not 'significant'")

        a = p.set_index("Target_Region").loc[TREATED, "Average_Post_Treatment_Gap"]
        b = summ.loc[outcome, "Average_Post_Treatment_Gap"]
        d = abs(a - b) / abs(b)
        record(D, f"{outcome}: placebo script agrees with main script for Region_1",
               "PASS" if d < 0.02 else "WARN",
               f"placebo_test.py gap {a:,.2f} vs synthetic_control.py gap {b:,.2f} ({d:.1%} apart) "
               "-- the two scripts fit weights in different ways")

    # in-time placebo: pretend treatment happened earlier
    fake = pd.Timestamp("2024-07-01")
    for outcome in OUTCOMES:
        panel, donors = sc[outcome]["panel"], sc[outcome]["donors"]
        fit_part = panel[panel.index < fake]
        w = fit_weights(fit_part, TREATED, donors)
        gap = panel[TREATED].to_numpy() - panel[donors].to_numpy() @ w
        window = (panel.index >= fake) & (panel.index < T0)
        fake_effect = gap[window].mean()
        real_effect = sc[outcome]["eff_mine"]
        share = abs(fake_effect) / abs(real_effect)
        record(D, f"{outcome}: in-time placebo (fake treatment on 2024-07-01)",
               "PASS" if share < 0.25 else "WARN",
               f"fake 'effect' {fake_effect:,.2f} vs real estimate {real_effect:,.2f} ({share:.1%} of it)")


# =================================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-rerun", action="store_true", help="skip section B")
    args = parser.parse_args()

    print("Running validation ...\n")
    raw, ready = check_data()
    if ready is None:
        print("Cannot continue: analysis-ready data missing. Run prepare_data.py first.")
    else:
        if args.skip_rerun:
            record("B", "Re-run reproduces saved results", "SKIP", "--skip-rerun used")
        else:
            check_reproducibility()
        sc = check_synthetic_control(ready)
        check_placebo(ready, sc)

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
