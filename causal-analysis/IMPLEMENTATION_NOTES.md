# Member 2 – Causal Analysis: Implementation Notes

## 1. Overview

This module implements data preparation, Synthetic Control analysis and placebo diagnostics for the synthetic pricing dataset.

The analysis focuses on Region_1, where a price intervention was introduced on 10 March 2025.

Two outcomes are evaluated:
- Revenue_Proxy (primary outcome)
- Sales_Volume (secondary outcome)

## 2. Data Preparation

The `prepare_data.py` script loads the original dataset from `data-preparation/synthetic_pricing_data.csv`.

It performs the following validation checks:

- Verifies that the input dataset exists.
- Checks for all required columns.
- Converts date and numeric columns into appropriate data types.
- Checks for missing values in required columns.
- Detects duplicate Date–Region_ID combinations.
- Ensures Price is greater than zero.
- Ensures Sales_Volume is non-negative.
- Validates the Treatment_Effect indicator against Treated multiplied by Post_Treatment.

### Revenue Proxy Feature

Since the original dataset does not contain a revenue column, the following derived feature is created:

Revenue_Proxy = Price × Sales_Volume

The prepared dataset is saved separately as `analysis_ready_data.csv`. The original dataset remains unchanged.

Revenue_Proxy is an analytical proxy, not verified real-world financial revenue.

## 3. Synthetic Control Implementation

The `synthetic_control.py` script implements the Synthetic Control Method.

### Treated and Donor Regions

- Treated region: Region_1
- Donor regions: Region_2 to Region_10
- Treatment date: 10 March 2025

### Donor Weight Optimisation

The implementation uses the SciPy SLSQP optimisation algorithm to calculate donor-region weights.

The objective is to minimise the mean squared difference between the treated region's actual pre-treatment outcomes and the weighted donor-region outcomes.

The optimisation follows these constraints:

- Each donor weight must be between 0 and 1.
- All donor weights must be non-negative.
- The sum of all donor weights must equal 1.

The weights are fitted using pre-treatment observations and then applied across the complete analysis period.

### Synthetic Counterfactual

The synthetic outcome is calculated as a weighted combination of the nine donor regions.

It represents the estimated outcome for Region_1 in the absence of the price intervention, under the Synthetic Control assumptions.

The treatment gap is calculated as:

Gap = Actual Outcome − Synthetic Outcome

## 4. Treatment Gap Evaluation

The implementation evaluates two outcomes: Revenue_Proxy and Sales_Volume.

The following metrics are calculated:

**Pre-treatment RMSE:** Measures the difference between actual and synthetic outcomes before the intervention.

**Average post-treatment gap:** Calculates the average daily difference between actual and synthetic outcomes after the intervention.

**Cumulative post-treatment gap:** Calculates the sum of the daily post-treatment differences.

The analysis generates actual-versus-synthetic graphs. A vertical dashed line identifies the intervention date.

## 5. Placebo Testing

The `placebo_test.py` script performs diagnostic placebo comparisons.

Region_1 is evaluated as the actual treated region. Each of the other nine regions is then evaluated as a placebo-treated region.

For placebo comparisons, Region_1 is excluded from the donor pool.

### Optimisation and Diagnostics

The placebo implementation:

- Standardises the target and donor observations before optimisation.
- Uses multiple starting points for SLSQP optimisation.
- Checks whether the resulting weights are finite and satisfy the optimisation constraints.
- Selects the valid solution with the lowest objective value.

The following diagnostic metrics are calculated:

- Pre-treatment RMSE
- Post-treatment RMSE
- Post/pre RMSE ratio
- Average post-treatment gap

The results are saved in `placebo_test_results.csv`.

Placebo comparisons help assess whether the treated region's observed pattern is unusual relative to other regions. They are diagnostic and do not independently establish statistical significance or prove causality.

## 6. Generated Outputs

The implementation generates the following outputs inside `causal-analysis/results/`:

- `Revenue_Proxy_synthetic_control.csv`
- `Sales_Volume_synthetic_control.csv`
- `synthetic_control_weights.csv`
- `synthetic_control_summary.csv`
- `placebo_test_results.csv`
- `Revenue_Proxy_synthetic_control.png`
- `Sales_Volume_synthetic_control.png`

## 7. Implementation Limitations

The current Member 2 implementation focuses on data validation, Synthetic Control estimation and placebo diagnostics.

The following broader project components are not implemented in this module:

- DoWhy-based causal DAG mapping and validation.
- Double Machine Learning (DML).
- Full ATE and CATE estimation.
- Full sensitivity analysis and cross-validation.

The calculated treatment gaps are estimates based on the Synthetic Control approach. Their interpretation depends on pre-treatment fit, donor-pool suitability and the assumptions of the method.

The dataset is synthetic, so the findings should not be interpreted as verified real-world pricing effects.

## 8. Module Handoff

The analysis-ready dataset, result tables, donor weights, summary metrics and graphs are available for integration by the other project members.

Existing output filenames and formats are retained to support downstream dashboard integration.