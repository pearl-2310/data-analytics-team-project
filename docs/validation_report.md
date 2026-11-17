# Validation Report

| | |
|---|---|
| **Project** | Causal Inference & Synthetic Control for Algorithmic Pricing |
| **Prepared by** | Member 4, Validation & Documentation |
| **Date** | 29 October 2026 |
| **Code validated** | Repository as received (`data-analytics-team-project-main`) |
| **Tool** | `validation/validate_project.py` (re-runnable; results in `validation/validation_results.csv`) |

## 1. Verdict

**The analysis is sound and reproducible, with one fixable defect in the revenue result.**

- The **sales result is trustworthy**: -39.4 units/day versus a true simulated effect of -40.3 (2.2 % off), confirmed by four independent checks.
- The **revenue result is directionally right but slightly under-estimated** (+2,684 vs true +2,867, 6.4 % off) because its weights were never actually optimised (Finding 1). A tested 3-line fix brings it to +2,937 (2.4 % off).
- The **dashboard backend works** (7 of 7 API tests pass, numbers match the CSVs). The **frontend could not be verified** and is missing files needed to start (Finding 3).
- **Double Machine Learning, named in the original problem statement, is not in the repository** (Finding 4).

## 2. Summary of 54 checks

| Area | What was checked | Pass | Info | Warn | Fail |
|---|---|---|---|---|---|
| A. Data quality | nulls, duplicates, balance, ranges, treatment flags, notebook regenerates the CSV | 11 | 2 | 0 | 0 |
| B. Reproducibility | all three scripts re-run from scratch and match saved results | 4 | 0 | 0 | 0 |
| C. Synthetic control | weights valid, optimal, fit quality, files consistent | 9 | 0 | 0 | 2 |
| D. Placebo tests | rank, p-value, in-time placebo, agreement between scripts | 5 | 2 | 1 | 0 |
| E. Robustness | leave-one-out, difference-in-differences, comparison with true effect | 7 | 0 | 1 | 0 |
| F. Dashboard | 7 API endpoints, filters, error handling, frontend files | 8 | 0 | 2 | 0 |
| **Total** | | **44** | **4** | **4** | **2** |

## 3. What was verified as correct

- **Data is clean:** 10,950 rows (10 regions x 1,095 days, 2023-01-01 to 2025-12-30), no missing values, no duplicates, no impossible values, perfectly balanced.
- **Data lineage is intact:** running the notebook generator reproduces `synthetic_pricing_data.csv` exactly (largest difference 1.1e-13), and `analysis_ready_data.csv` equals the raw data plus `Revenue_Proxy = Price x Sales`.
- **Fully reproducible:** all three scripts run without errors from a clean copy, and every saved result file matches (largest difference 0.00).
- **Valid design:** Region_1 is the only treated region; treatment starts 2025-03-10 in all files; before the price change Region_1 tracks the donor average closely (correlation 0.85).
- **Good pre-treatment fit:** RMSE is 1.9 % of the average level for both outcomes.
- **Placebo test supports the effect:** Region_1's post/pre error ratio is 2.99 (revenue) and 2.61 (sales), the highest of all 10 regions; the other nine are between 0.89 and 1.13.
- **No false effect earlier in time:** pretending the price change happened on 2024-07-01 gives an "effect" of only 0.9 % (revenue) and 1.9 % (sales) of the real estimate.
- **Not driven by one donor:** dropping any single donor changes the sales estimate by at most 1.8 % (and the corrected revenue estimate by at most 5.7 %).
- **Two methods agree:** simple difference-in-differences gives -40.1 for sales (synthetic control -39.4).
- **Dashboard API is correct:** all 7 endpoints return success; summary numbers equal the CSV; date, region and outcome filters return the right row counts; a bad date returns HTTP 400.

### Comparison with the true effect

Because the data is simulated, the true effect can be calculated from the generator code (price +15 %, sales fall 2.5 units per 1 unit of price).
Real data never offers this check, so it is the strongest evidence here.

| Outcome | True effect | Team's saved result | Independent re-fit |
|---|---|---|---|
| Sales volume (avg/day) | -40.27 | -39.39 (+2.2 %) | -39.39 (+2.2 %) |
| Revenue proxy (avg/day) | +2,866.84 | +2,684.44 (-6.4 %) | +2,936.67 (+2.4 %) |

## 4. Findings

### Finding 1: Revenue weights were never optimised (HIGH, owner: causal analysis)

**Evidence.** In `results/synthetic_control_weights.csv`, all nine revenue weights are exactly 0.1111, the starting guess, so the "synthetic control"
is just the plain donor average. An independent fit gives a better pre-treatment RMSE (957.19 vs 994.80) and a different effect (+2,937 vs +2,684).
The sales weights are fine (varied, 0 to 0.23).

**Cause.** Revenue values are around 50,000, so the squared-error objective is around 10^9 and the optimiser's default tolerance is met almost immediately.
In my reproduction it stopped after 5 iterations without leaving its starting point. `synthetic_control.py` uses the default tolerance and an unscaled objective; `placebo_test.py` scales its data and sets a tighter tolerance, which is why it does not have this problem. Sales values are around 500, so the sales fit was not affected.

**Impact.** Revenue effect understated by about 9 %. The conclusion (revenue rises) does not change.

**Recommended fix (tested).** In `synthetic_control.py`, scale the objective by the target's standard deviation:

```python
    scale = target.std() or 1.0          # add this line before the objective function

    def objective(weights):
        predictions = donors @ weights
        return np.mean(((target - predictions) / scale) ** 2)   # divide the error by scale
```

After this change, revenue pre-treatment RMSE becomes 957.19, the weights become varied (0.07 to 0.23), and sales results are unchanged.
Then re-run `synthetic_control.py` and `placebo_test.py`, re-run the validation, and refresh the dashboard (it reads the CSVs, so no code change is needed there).

### Finding 2: Two scripts fit weights differently (MEDIUM, owner: causal analysis)

`placebo_test.py` gets a Region_1 sales gap of -31.6, while `synthetic_control.py` gets -39.4 (true value -40.3). The placebo script standardises donor columns
while fitting, then applies the weights to the original values, so its synthetic control is slightly worse. The placebo *conclusion* still holds (Region_1 is by far the most
extreme either way), but the headline number and the comparison should come from one method.
**Fix:** move the weight-fitting function into one shared place and use it in both scripts.

### Finding 3: Frontend cannot start as delivered (MEDIUM, owner: dashboard)

- `dashboard-creation/frontend/` has `App.jsx`, `main.jsx`, `package.json` and CSS, but no `index.html` and no `vite.config.js`. Vite needs `index.html` as its entry page, and the React plugin
  listed in `package.json` is configured in `vite.config.js`.
- `dashboard-creation/README.md` describes `my-app/src/App.jsx` and `my-app/package.json`; the real folder is `frontend/` (the package is still named `my-app`).
- The frontend calls `http://127.0.0.1:5000`, which matches the backend port (checked).

**Not verified:** I could not run `npm install` or the dashboard visually (no internet in my environment). The backend was fully tested; please run the frontend on your own computer and
confirm the charts load. If `npm run dev` shows a blank page or a 404, add the two missing files.

### Finding 4: Double Machine Learning is missing (MEDIUM, owner: whole team)

The problem statement asks for Synthetic Control **and** Double ML. The repository implements Synthetic Control, placebo tests and a dashboard only. The dataset already contains
`Competitor_Price` and `Regional_Google_Trends_Index`, which are the confounders a Double ML step would use. **Decision needed:** add a `double_ml.py` (a natural extension of the causal-analysis part), or state
clearly in the README that the scope is Synthetic Control only. Do not claim Double ML on a CV or in an interview unless it is added.

### Finding 5: Placebo p-value has a floor of 0.10 (INFO)

With 10 regions, ranking first gives p = 1/10 = 0.10, the smallest value possible. It can never pass 0.05, however large the effect. Report it as
"Region_1 was the most extreme of 10 regions", not as "statistically significant".

### Finding 6: Revenue is partly mechanical (INFO)

`Revenue_Proxy = Price x Sales`, so any price increase lifts it by construction. The honest story is: a 15 % price rise cut sales by about 8 %, and revenue still rose by about 5 %.
The demand effect should be read from `Sales_Volume`.

### Finding 7: Housekeeping (LOW)

- The treatment date `2025-03-10` is hard-coded in three files (`synthetic_control.py`, `placebo_test.py`, `backend/app.py`). They agree today; change all three together or move it to one config.
- No root `requirements.txt` (the one in `dashboard-creation/backend/` covers everything) and no `.gitignore` (so `__pycache__` and `node_modules` can be committed by accident).
- The data notebook is named "Experimental" and contains several generators; the dataset comes from the cell containing `treatment_day = 800`, which appears twice with identical code. Consider keeping one.
- The backend runs Flask with `debug=True`; fine for a demo, not for deployment.

## 5. What this validation did not cover

- **Frontend execution and visual layout** (see Finding 3).
- **The true effect is calculated from the generator's formulas**; if the generator is changed, the ground-truth check in `validate_project.py` must be updated (constants `TRUE_PRICE_JUMP` and `TRUE_PRICE_COEF`).
- **Real-world validity:** the data is simulated, so results show the method works, not how a real market behaves.
- **Statistical significance:** with one treated region, no formal confidence interval exists (see Finding 5).

## 6. How to re-run this validation

```powershell
py .\validation\validate_project.py            # full run (about 1 to 2 minutes)
py .\validation\validate_project.py --skip-rerun   # faster, skips re-running the analysis scripts
```

The script only reads the repository (it re-runs the analysis scripts inside a temporary copy) and writes one file: `validation/validation_results.csv`.
After the team applies the fixes, the two FAIL lines (C2, C4) and the revenue WARN (E5) should turn to PASS.

## 7. Sign-off checklist

| Done | Item |
|---|---|
| [ ] | Finding 1 fixed; `synthetic_control.py` and `placebo_test.py` re-run; results pushed |
| [ ] | Finding 2: one shared weight-fitting method |
| [ ] | Finding 3: frontend runs with `npm run dev`; charts load; README paths corrected |
| [ ] | Finding 4: Double ML added, or scope statement added to the README |
| [ ] | Validation re-run: no FAIL lines remaining |
| [ ] | Final numbers in the README refreshed from the new results |
