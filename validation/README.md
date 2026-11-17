# Member 4 – Validation and Documentation

## 1. Purpose

This module independently checks the work of Members 1, 2 and 3 for the **Causal Inference & Synthetic Control Engine for Algorithmic Pricing** project, and documents the project as a whole.

It runs 54 automatic checks on the data, the Synthetic Control and placebo results, and the dashboard backend. It also compares the estimates with the **true effect built into the simulated data**, which shows how accurate the analysis really is.

The module only reads other members' files. It does not modify them.

## 2. Input Data

The validation script reads these files (read-only):

| File | Used for |
|---|---|
| `data-preparation/synthetic_pricing_data.csv` | Data-quality checks on the original dataset |
| `data-preparation/Synthetic_Panel_Generators_Experimental.ipynb` | Confirming that the dataset can be regenerated exactly, and reading the true price effect |
| `causal-analysis/analysis_ready_data.csv` | Checking the prepared dataset and recomputing the Synthetic Control |
| `causal-analysis/results/*.csv` | Checking the saved weights, summaries, daily results and placebo results |
| `dashboard-creation/backend/app.py` | Testing the Flask API endpoints |
| `dashboard-creation/frontend/` and `dashboard-creation/README.md` | Static checks (required files, API address, folder names) |

**Important:** the true effect is known only because the dataset is simulated. Real-world data has no such answer key.

## 3. Files in This Module

| File | Purpose |
|---|---|
| `validate_project.py` | Runs all validation checks and saves the results. |
| `validation_results.csv` | Output of the most recent run: one row per check. |
| `README.md` | This file. |

Project-level documentation written by Member 4:

| File | Purpose |
|---|---|
| `../README.md` | Project overview, key results, how to run everything, open items. |
| `../docs/validation_report.md` | Verdict, findings with evidence and recommended fixes, sign-off checklist. |
| `../docs/methodology.md` | The methods explained in plain English. |
| `../docs/data_dictionary.md` | Every column, result file and API endpoint explained. |

## 4. How to Run

Run these commands from the repository's root folder in PowerShell.

### Step 1: Install the Python packages

```powershell
pip install -r dashboard-creation/backend/requirements.txt
```

This one file covers the analysis scripts, the backend and the validation script.

### Step 2: Make sure the analysis outputs exist

The results are already stored in the repository, so this step is only needed if `causal-analysis/results/` is empty. If it is, run Member 2's scripts first (see `causal-analysis/README.md`).

### Step 3: Run the validation

```powershell
py .\validation\validate_project.py
```

The run takes about 1 to 2 minutes. To skip the slowest part (re-running the analysis scripts), use:

```powershell
py .\validation\validate_project.py --skip-rerun
```

With `--skip-rerun`, the four reproducibility checks (area B) are replaced by one `SKIP`, so the totals change to 40 PASS and 1 SKIP. All other counts stay the same.

## 5. Output Files

- **Terminal output** – one line per check (`PASS`, `WARN`, `FAIL`, `INFO` or `SKIP`) and a count of each at the end.
- `validation/validation_results.csv` – the same table, saved with the columns `ID`, `Area`, `Check`, `Result` and `Detail`.

The script writes only this one file. When it re-runs Member 2's scripts, it does so inside a temporary copy of the repository, so the files in `causal-analysis/` are not touched.

## 6. What Is Checked

| Area | What it covers | Checks |
|---|---|---|
| **A. Data quality** | Missing values, duplicates, balanced daily panel, value ranges, one treated region, treatment flags, analysis-ready file, notebook regenerates the CSV | 13 |
| **B. Reproducibility** | All three analysis scripts re-run from scratch and reproduce every saved result file | 4 |
| **C. Synthetic Control** | Weights valid and optimal, pre-treatment fit, independent re-fit, summary matches daily results, treatment date consistent | 11 |
| **D. Placebo tests** | Rank and p-value of `Region_1`, agreement between scripts, in-time placebo (fake treatment date) | 8 |
| **E. Robustness** | Leave-one-donor-out, difference-in-differences cross-check, comparison with the true effect | 8 |
| **F. Dashboard** | All 7 API endpoints, filters, error handling, frontend files, README paths | 10 |

## 7. How to Interpret the Results

- **PASS:** The check succeeded.
- **WARN:** The item works, but needs attention or a decision.
- **FAIL:** A real problem was found. See `docs/validation_report.md` for the evidence and the recommended fix.
- **INFO:** A fact worth reporting, not a problem.
- **SKIP:** The check could not run on this computer (for example, Flask is not installed).

**Latest full run:** 54 checks – 44 PASS, 4 INFO, 4 WARN, 2 FAIL.

| ID | Result | Meaning | Owner |
|---|---|---|---|
| C2, C4 | FAIL | Revenue weights are all 0.1111: the optimizer never moved from its starting guess | Member 2 |
| E5 | WARN | The revenue estimate (+2,684) is 6.4 % below the true effect (+2,867) | Member 2 |
| D6 | WARN | `placebo_test.py` and `synthetic_control.py` give different gaps for `Region_1` sales (-31.6 vs -39.4) | Member 2 |
| F8 | WARN | The frontend folder has no `index.html` or `vite.config.js` | Member 3 |
| F9 | WARN | The dashboard README refers to `my-app/`; the real folder is `frontend/` | Member 3 |

The **sales** result is validated: -39.4 units per day against a true effect of -40.3 (2.2 % difference), supported by the placebo, leave-one-out and difference-in-differences checks.

After the recommended fix to `synthetic_control.py`, the two FAIL lines and the E5 warning should change to PASS. Re-run this script to confirm.

## 8. Validation Caution

Validation checks are diagnostic. A passing check shows that the work is consistent and reproducible; it does not prove that the real world behaves the same way.

- **The data is simulated.** The ground-truth comparison works only because the data-generating rules are known. If the notebook changes, update `TRUE_PRICE_JUMP` and `TRUE_PRICE_COEF` at the top of `validate_project.py`.
- **Thresholds are judgement calls.** For example, "pre-treatment RMSE below 5 % of the level" and "estimates within 2 % of the re-fit" are reasonable limits chosen for this project, not universal standards.
- **The placebo p-value has a floor of 0.10.** With 10 regions, ranking first means p = 1/10, which can never reach 0.05. Describe it as "most extreme of 10 regions", not "statistically significant".
- **The frontend is not executed.** The script tests the Flask backend fully, but checks the React frontend only by looking at its files. Someone must run `npm install` and `npm run dev` and confirm that the charts load.
- **Double Machine Learning is not checked** because it is not implemented in the repository.

## 9. Handoff to Other Members

Member 4 does not change other members' files. Each owner applies fixes in their own module, then re-runs this script.

| Member | Action requested | Details |
|---|---|---|
| **Member 1 – Data Preparation** | None. All data-quality checks passed and the notebook reproduces the CSV exactly. | Optional: keep one copy of the duplicated data-generation cell in the notebook. |
| **Member 2 – Causal Analysis** | Fix the revenue weights; use one shared weight-fitting method in both scripts. | `docs/validation_report.md`, Findings 1 and 2 (the fix is tested). |
| **Member 3 – Dashboard** | Add `index.html` and `vite.config.js`, confirm the frontend runs, and correct the folder names in the README. | `docs/validation_report.md`, Finding 3. |
| **Whole team** | Decide whether to add Double Machine Learning or state the scope as Synthetic Control only. | `docs/validation_report.md`, Finding 4. |

After the fixes are merged, re-run `validate_project.py`, update the key results in the root `README.md`, and tick the sign-off checklist at the end of `docs/validation_report.md`.
