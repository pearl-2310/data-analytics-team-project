
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib.pyplot as plt


# 1. Locate project files
PROJECT_DIR = Path(__file__).resolve().parent

INPUT_FILE = PROJECT_DIR / "analysis_ready_data.csv"
OUTPUT_DIR = PROJECT_DIR / "results"

TREATMENT_DATE = pd.Timestamp("2025-03-10")
TREATED_REGION = "Region_1"

OUTCOMES = ["Revenue_Proxy", "Sales_Volume"]


def fit_synthetic_control(pre_treatment, donor_regions, outcome):
    """Find non-negative donor weights that sum to one."""

    target = pre_treatment[TREATED_REGION].to_numpy()
    donors = pre_treatment[donor_regions].to_numpy()

    # Each column represents one donor region.
    def objective(weights):
        predictions = donors @ weights
        return np.mean((target - predictions) ** 2)

    initial_weights = np.full(
        len(donor_regions),
        1 / len(donor_regions),
    )

    constraints = [
        {
            "type": "eq",
            "fun": lambda weights: weights.sum() - 1,
        }
    ]

    bounds = [(0, 1)] * len(donor_regions)

    result = minimize(
        objective,
        initial_weights,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )

    if not result.success:
        raise RuntimeError(
            f"Weight optimization failed for {outcome}: "
            f"{result.message}"
        )

    return result.x


def main():
    print("Loading analysis-ready dataset...")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {INPUT_FILE}. "
            "Run prepare_data.py first."
        )

    df = pd.read_csv(INPUT_FILE, parse_dates=["Date"])

    required_columns = [
        "Date",
        "Region_ID",
        "Revenue_Proxy",
        "Sales_Volume",
    ]

    if not set(required_columns).issubset(df.columns):
        raise ValueError("Required columns are missing.")

    if df.duplicated(["Date", "Region_ID"]).any():
        raise ValueError("Duplicate region-date records found.")

    wide_data = {}

    # 2. Convert panel data into one column per region.
    for outcome in OUTCOMES:
        wide_data[outcome] = df.pivot(
            index="Date",
            columns="Region_ID",
            values=outcome,
        ).sort_index()

    revenue_panel = wide_data["Revenue_Proxy"]

    if TREATED_REGION not in revenue_panel.columns:
        raise ValueError(
            f"Treated region {TREATED_REGION} not found."
        )

    donor_regions = sorted(
        region
        for region in revenue_panel.columns
        if region != TREATED_REGION
    )

    if len(donor_regions) != 9:
        raise ValueError(
            f"Expected 9 donor regions; found {len(donor_regions)}."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_effects = []
    all_weights = []

    # 3. Fit weights before the intervention.
    for outcome in OUTCOMES:
        panel = wide_data[outcome]

        pre = panel.loc[panel.index < TREATMENT_DATE]
        post = panel.loc[panel.index >= TREATMENT_DATE]

        if pre.empty or post.empty:
            raise ValueError(
                f"Missing pre- or post-treatment data for {outcome}."
            )

        if pre.isna().any().any() or post.isna().any().any():
            raise ValueError(
                f"Missing observations found for {outcome}."
            )

        weights = fit_synthetic_control(
            pre,
            donor_regions,
            outcome,
        )

        # 4. Apply the pre-treatment weights to all dates.
        synthetic = panel[donor_regions].to_numpy() @ weights
        actual = panel[TREATED_REGION].to_numpy()

        result_df = pd.DataFrame(
            {
                "Date": panel.index,
                "Outcome": outcome,
                "Actual": actual,
                "Synthetic": synthetic,
                "Gap": actual - synthetic,
            }
        )

        result_df["Period"] = np.where(
            result_df["Date"] < TREATMENT_DATE,
            "Pre-treatment",
            "Post-treatment",
        )

        pre_mask = result_df["Date"] < TREATMENT_DATE
        post_mask = result_df["Date"] >= TREATMENT_DATE

        pre_rmse = np.sqrt(
            np.mean(result_df.loc[pre_mask, "Gap"] ** 2)
        )

        post_average_gap = result_df.loc[
            post_mask, "Gap"
        ].mean()

        post_total_gap = result_df.loc[
            post_mask, "Gap"
        ].sum()

        # Save the estimated daily results.
        result_path = OUTPUT_DIR / f"{outcome}_synthetic_control.csv"
        result_df.to_csv(result_path, index=False)

        for region, weight in zip(donor_regions, weights):
            all_weights.append(
                {
                    "Outcome": outcome,
                    "Donor_Region": region,
                    "Weight": weight,
                }
            )

        all_effects.append(
            {
                "Outcome": outcome,
                "Pre_Treatment_RMSE": pre_rmse,
                "Average_Post_Treatment_Gap": post_average_gap,
                "Cumulative_Post_Treatment_Gap": post_total_gap,
            }
        )

        # 5. Plot actual and synthetic outcomes.
        plt.figure(figsize=(12, 5))
        plt.plot(
            result_df["Date"],
            result_df["Actual"],
            label="Region 1: Actual",
        )
        plt.plot(
            result_df["Date"],
            result_df["Synthetic"],
            label="Synthetic Region 1",
        )
        plt.axvline(
            TREATMENT_DATE,
            linestyle="--",
            label="Price intervention",
        )
        plt.title(f"Synthetic Control: {outcome}")
        plt.xlabel("Date")
        plt.ylabel(outcome)
        plt.legend()
        plt.tight_layout()

        plot_path = OUTPUT_DIR / f"{outcome}_synthetic_control.png"
        plt.savefig(plot_path, dpi=150)
        plt.close()

        print(f"\nOutcome: {outcome}")
        print(f"Pre-treatment RMSE: {pre_rmse:.2f}")
        print(
            "Average post-treatment gap: "
            f"{post_average_gap:.2f}"
        )
        print(
            "Cumulative post-treatment gap: "
            f"{post_total_gap:.2f}"
        )
        print(f"Results saved to: {result_path}")
        print(f"Plot saved to: {plot_path}")

    # 6. Save weights and summary metrics.
    weights_path = OUTPUT_DIR / "synthetic_control_weights.csv"
    pd.DataFrame(all_weights).to_csv(weights_path, index=False)

    summary_path = OUTPUT_DIR / "synthetic_control_summary.csv"
    pd.DataFrame(all_effects).to_csv(summary_path, index=False)

    print("\nSynthetic Control run completed.")
    print(f"Weights: {weights_path}")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
