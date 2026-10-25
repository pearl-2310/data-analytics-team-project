# Member 2 – Causal Analysis

## 1. Purpose

This module performs causal analysis on the synthetic pricing dataset prepared by Member 1.

It uses the **Synthetic Control Method** to compare the treated region, `Region_1`, with a synthetic comparison region created using the other regions. It also performs placebo tests to assess whether the observed post-treatment differences stand out from those of other regions.

## 2. Input Data

The original dataset is located at:

`data-preparation/synthetic_pricing_data.csv`

The data preparation script creates:

`causal-analysis/analysis_ready_data.csv`

The analysis-ready dataset includes a derived column:

- `Revenue_Proxy`: calculated as `Price × Sales_Volume`.

**Important:** `Revenue_Proxy` is a proxy for revenue, not verified real-world financial revenue.

The original dataset is preserved; the preparation script writes a separate analysis-ready file.

## 3. Files in This Module

| File | Purpose |
|---|---|
| `prepare_data.py` | Validates the input dataset and creates the analysis-ready dataset. |
| `synthetic_control.py` | Runs Synthetic Control analysis for `Revenue_Proxy` and `Sales_Volume`. |
| `placebo_test.py` | Runs placebo comparisons across regions. |
| `analysis_ready_data.csv` | Prepared dataset used by the analysis scripts. |
| `results/` | Contains result tables, weights, summaries, and graphs. |

## 4. How to Run

Run these commands from the repository's root folder in PowerShell.

### Step 1: Prepare the data

```powershell
py .\causal-analysis\prepare_data.py
```

### Step 2: Run Synthetic Control

```powershell
py .\causal-analysis\synthetic_control.py
```

### Step 3: Run placebo tests

```powershell
py .\causal-analysis\placebo_test.py
```

Run the scripts in this order because the analysis scripts use the prepared dataset.

## 5. Output Files

The scripts generate or update these files inside `causal-analysis/results/`:

- `Revenue_Proxy_synthetic_control.csv` – actual and synthetic revenue-proxy values and their differences over time.
- `Sales_Volume_synthetic_control.csv` – actual and synthetic sales-volume values and their differences over time.
- `synthetic_control_weights.csv` – weights assigned to comparison regions.
- `synthetic_control_summary.csv` – summary metrics for the Synthetic Control analysis.
- `placebo_test_results.csv` – placebo comparison results for the regions.
- `Revenue_Proxy_synthetic_control.png` – actual versus synthetic revenue-proxy graph.
- `Sales_Volume_synthetic_control.png` – actual versus synthetic sales-volume graph.

## 6. How to Interpret the Results

- **Actual outcome:** The observed outcome for the treated region.
- **Synthetic outcome:** The estimated comparison outcome constructed from other regions.
- **Gap:** Actual outcome minus synthetic outcome.
- **Pre-treatment RMSE:** Measures the typical difference between actual and synthetic outcomes before treatment. Lower values indicate a closer pre-treatment fit.
- **Average post-treatment gap:** The average difference between actual and synthetic outcomes after treatment.
- **Cumulative post-treatment gap:** The sum of daily post-treatment differences; interpret it in the outcome's units.

A positive gap means the actual outcome is above the synthetic estimate. A negative gap means it is below the estimate.

## 7. Placebo-Test Caution

Placebo tests apply the same general comparison to other regions. They help assess whether the treated region's result is unusual compared with the placebo results.

These tests are diagnostic and do not, by themselves, prove that the treatment caused the observed change. Interpret results alongside pre-treatment fit and the assumptions of the Synthetic Control Method.

## 8. Handoff to Other Members

This folder contains Member 2's data-preparation-for-analysis and causal-analysis outputs. Later team members can use the analysis-ready dataset, result CSV files, summary metrics, and graphs as inputs for their assigned tasks.

The original data-preparation files belong to the existing data-preparation module and should not be modified as part of this module unless the team agrees to a change.