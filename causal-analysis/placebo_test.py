
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize


PROJECT_DIR = Path(__file__).resolve().parent
INPUT_FILE = PROJECT_DIR / "analysis_ready_data.csv"
OUTPUT_DIR = PROJECT_DIR / "results"

TREATMENT_DATE = pd.Timestamp("2025-03-10")
TREATED_REGION = "Region_1"
OUTCOMES = ["Revenue_Proxy", "Sales_Volume"]


def fit_weights(pre_data, target_region, donor_regions):
    """Fit non-negative donor weights that sum to one."""

    target = pre_data[target_region].to_numpy(dtype=float)
    donors = pre_data[donor_regions].to_numpy(dtype=float)

    # Scale columns to improve numerical conditioning.
    target_mean = target.mean()
    target_scale = target.std()
    if target_scale == 0:
        target_scale = 1.0

    donor_means = donors.mean(axis=0)
    donor_scales = donors.std(axis=0)
    donor_scales[donor_scales == 0] = 1.0

    target_scaled = (target - target_mean) / target_scale
    donors_scaled = (donors - donor_means) / donor_scales

    def objective(weights):
        residual = target_scaled - donors_scaled @ weights
        return float(np.mean(residual ** 2))

    n_donors = len(donor_regions)
    initial = np.full(n_donors, 1.0 / n_donors)

    constraints = [
        {"type": "eq", "fun": lambda weights: weights.sum() - 1}
    ]
    bounds = [(0.0, 1.0)] * n_donors

    # Try several valid starting points.
    starts = [
        initial,
        *[
            np.eye(n_donors)[i] * 0.9
            + np.full(n_donors, 0.1 / n_donors)
            for i in range(n_donors)
        ],
    ]

    candidates = []

    for start in starts:
        result = minimize(
            objective,
            start,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 3000, "ftol": 1e-10},
        )

        # Accept only valid, finite solutions.
        if (
            np.isfinite(result.fun)
            and np.all(np.isfinite(result.x))
            and np.all(result.x >= -1e-6)
            and np.all(result.x <= 1 + 1e-6)
            and abs(result.x.sum() - 1) <= 1e-5
        ):
            candidates.append(result)

    if not candidates:
        raise RuntimeError(
            f"No valid optimization solution for {target_region}. "
            "Try inspecting the data for unusual values."
        )

    best = min(candidates, key=lambda result: result.fun)
    weights = np.clip(best.x, 0.0, 1.0)
    weights = weights / weights.sum()

    return weights


def evaluate_region(panel, target_region, donor_regions, outcome):
    """Estimate pre-treatment weights and calculate fit diagnostics."""

    pre = panel.loc[panel.index < TREATMENT_DATE]
    post = panel.loc[panel.index >= TREATMENT_DATE]

    if pre.empty or post.empty:
        raise ValueError(f"Missing pre/post data for {target_region}.")

    weights = fit_weights(pre, target_region, donor_regions)

    synthetic = panel[donor_regions].to_numpy() @ weights
    actual = panel[target_region].to_numpy()
    gap = actual - synthetic

    pre_mask = panel.index < TREATMENT_DATE
    post_mask = panel.index >= TREATMENT_DATE

    pre_rmse = np.sqrt(np.mean(gap[pre_mask] ** 2))
    post_rmse = np.sqrt(np.mean(gap[post_mask] ** 2))
    average_gap = np.mean(gap[post_mask])

    return {
        "Outcome": outcome,
        "Target_Region": target_region,
        "Pre_Treatment_RMSE": pre_rmse,
        "Post_Treatment_RMSE": post_rmse,
        "Post_Pre_RMSE_Ratio": (
            post_rmse / pre_rmse if pre_rmse > 0 else np.nan
        ),
        "Average_Post_Treatment_Gap": average_gap,
    }


def main():
    print("Loading analysis-ready dataset...")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE, parse_dates=["Date"])
    results = []

    for outcome in OUTCOMES:
        panel = df.pivot(
            index="Date",
            columns="Region_ID",
            values=outcome,
        ).sort_index()

        if panel.isna().any().any():
            raise ValueError(f"Missing values in {outcome}.")

        regions = list(panel.columns)

        if TREATED_REGION not in regions:
            raise ValueError(f"{TREATED_REGION} not found.")

        # Evaluate the actual treated region first.
        donors = [r for r in regions if r != TREATED_REGION]
        results.append(
            evaluate_region(panel, TREATED_REGION, donors, outcome)
        )

        # Evaluate each untreated region as a placebo.
        # Exclude Region_1 from the placebo donor pool.
        for placebo in regions:
            if placebo == TREATED_REGION:
                continue

            placebo_donors = [
                r for r in regions
                if r not in (placebo, TREATED_REGION)
            ]

            results.append(
                evaluate_region(
                    panel, placebo, placebo_donors, outcome
                )
            )

    results_df = pd.DataFrame(results)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "placebo_test_results.csv"
    results_df.to_csv(output_file, index=False)

    print("\nPlacebo diagnostic results:")
    print(results_df.round(3).to_string(index=False))
    print(f"\nResults saved to: {output_file}")
    print(
        "\nThese are diagnostic placebo comparisons, "
        "not definitive significance tests."
    )


if __name__ == "__main__":
    main()
