
from pathlib import Path

import pandas as pd


# 1. Find the project folders
PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data-preparation"
    / "synthetic_pricing_data.csv"
)

OUTPUT_FILE = (
    Path(__file__).resolve().parent
    / "analysis_ready_data.csv"
)


def prepare_data():
    """Load, validate, and prepare data for causal analysis."""

    print("Loading the synthetic pricing dataset...")

    # 2. Check that the original dataset exists
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    # 3. Load the original CSV
    df = pd.read_csv(INPUT_FILE)

    # 4. Check that the required columns exist
    required_columns = [
        "Date",
        "Region_ID",
        "Price",
        "Sales_Volume",
        "Competitor_Price",
        "Regional_Google_Trends_Index",
        "Treated",
        "Post_Treatment",
        "Treatment_Effect",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # 5. Convert dates and validate numeric values
    df["Date"] = pd.to_datetime(df["Date"], errors="raise")

    numeric_columns = [
        "Price",
        "Sales_Volume",
        "Competitor_Price",
        "Regional_Google_Trends_Index",
        "Treated",
        "Post_Treatment",
        "Treatment_Effect",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise",
        )

    # 6. Check basic data quality
    if df[required_columns].isnull().any().any():
        raise ValueError(
            "Missing values detected in required columns."
        )

    if df.duplicated(["Date", "Region_ID"]).any():
        raise ValueError(
            "Duplicate Date and Region_ID combinations detected."
        )

    if (df["Price"] <= 0).any():
        raise ValueError("Price must be greater than zero.")

    if (df["Sales_Volume"] < 0).any():
        raise ValueError("Sales_Volume cannot be negative.")

    # 7. Verify the treatment indicators
    expected_treatment = (
        df["Treated"] * df["Post_Treatment"]
    )

    if not df["Treatment_Effect"].equals(expected_treatment):
        raise ValueError(
            "Treatment_Effect does not match "
            "Treated multiplied by Post_Treatment."
        )

    # 8. Calculate the synthetic revenue proxy
    df["Revenue_Proxy"] = df["Price"] * df["Sales_Volume"]

    # 9. Save a separate analysis-ready dataset
    df.to_csv(OUTPUT_FILE, index=False)

    # 10. Display a summary
    print("\nData preparation completed successfully.")
    print(f"Rows: {len(df)}")
    print(f"Regions: {df['Region_ID'].nunique()}")
    print(f"Date range: {df['Date'].min().date()} to "
          f"{df['Date'].max().date()}")
    print(f"Missing values: {df.isnull().sum().sum()}")
    print(f"Revenue proxy created: "
          f"{'Revenue_Proxy' in df.columns}")
    print(f"Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    prepare_data()
