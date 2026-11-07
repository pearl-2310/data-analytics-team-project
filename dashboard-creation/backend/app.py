from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Project paths
BACKEND_DIR = Path(__file__).resolve().parent
APP_DIR = BACKEND_DIR.parent
PROJECT_DIR = APP_DIR.parent

TREATMENT_DATE = pd.Timestamp("2025-03-10")
TREATED_REGION = "Region_1"

# Find the causal-analysis directory
ANALYSIS_DIR_CANDIDATES = [
    APP_DIR / "causal-analysis",
    PROJECT_DIR / "causal-analysis",
    APP_DIR / "causal_analysis",
    PROJECT_DIR / "causal_analysis",
]

def first_existing_dir(candidates):
    return next(
        (path for path in candidates if path.is_dir()),
        candidates[0]
    )


ANALYSIS_DIR = first_existing_dir(ANALYSIS_DIR_CANDIDATES)

# Results folders
RESULTS_DIR_CANDIDATES = [
    ANALYSIS_DIR / "results",
    APP_DIR / "results",
    PROJECT_DIR / "results",
]

# Search locations for the main dataset
DATA_DIR_CANDIDATES = [
    ANALYSIS_DIR,
    ANALYSIS_DIR / "results",
    APP_DIR / "data-preparation",
    PROJECT_DIR / "data-preparation",
    APP_DIR,
    PROJECT_DIR,
]


def find_file(filename):
    """Find a CSV file in the configured project directories."""

    if filename == "analysis_ready_data.csv":
        candidates = [
            folder / filename
            for folder in DATA_DIR_CANDIDATES
        ]
    else:
        candidates = [
            folder / filename
            for folder in RESULTS_DIR_CANDIDATES
        ]

        candidates.extend([
            ANALYSIS_DIR / filename,
            APP_DIR / filename,
            PROJECT_DIR / filename,
        ])

    seen = set()

    for path in candidates:
        path = path.resolve()

        if path not in seen:
            seen.add(path)

            if path.is_file():
                return path

    return None


def load_csv(filename):
    """Load a CSV file and return its DataFrame."""

    path = find_file(filename)

    if path is None:
        if filename == "analysis_ready_data.csv":
            searched = [
                folder / filename
                for folder in DATA_DIR_CANDIDATES
            ]
        else:
            searched = [
                folder / filename
                for folder in RESULTS_DIR_CANDIDATES
            ]

            searched.extend([
                ANALYSIS_DIR / filename,
                APP_DIR / filename,
                PROJECT_DIR / filename,
            ])

        message = (
            f"{filename} was not found. Searched: "
            + " | ".join(str(p) for p in searched)
        )

        return None, message

    try:
        df = pd.read_csv(path)
        return df, None

    except Exception as exc:
        return None, (
            f"Could not read {filename} at {path}: {exc}"
        )


def clean_records(df):
    """Convert DataFrame records into JSON-safe values."""

    safe_df = df.copy()

    for column in safe_df.columns:
        if pd.api.types.is_datetime64_any_dtype(
            safe_df[column]
        ):
            safe_df[column] = (
                safe_df[column].dt.strftime("%Y-%m-%d")
            )

    safe_df = safe_df.astype(object).where(
        pd.notna(safe_df),
        None
    )

    return safe_df.to_dict(orient="records")


def error_response(message, status=404):
    return jsonify({
        "success": False,
        "error": message
    }), status


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": (
            "Causal Inference & Synthetic Control API "
            "is running."
        ),
        "analysis_directory": str(ANALYSIS_DIR),
        "results_directories": [
            str(path)
            for path in RESULTS_DIR_CANDIDATES
        ],
        "endpoints": [
            "/api/health",
            "/api/summary",
            "/api/revenue",
            "/api/sales",
            "/api/weights",
            "/api/placebo",
            "/api/data",
        ],
    })


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    filenames = [
        "analysis_ready_data.csv",
        "Revenue_Proxy_synthetic_control.csv",
        "Sales_Volume_synthetic_control.csv",
        "synthetic_control_weights.csv",
        "synthetic_control_summary.csv",
        "placebo_test_results.csv",
    ]

    file_status = {}
    file_paths = {}

    for filename in filenames:
        path = find_file(filename)

        file_status[filename] = path is not None
        file_paths[filename] = (
            str(path) if path else None
        )

    return jsonify({
        "success": True,
        "backend": "running",
        "treated_region": TREATED_REGION,
        "treatment_date": (
            TREATMENT_DATE.strftime("%Y-%m-%d")
        ),
        "analysis_directory": str(ANALYSIS_DIR),
        "files_found": file_status,
        "file_paths": file_paths,
    })


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

@app.route("/api/summary", methods=["GET"])
def summary():
    df, error = load_csv(
        "synthetic_control_summary.csv"
    )

    if error:
        return error_response(error)

    required = [
        "Outcome",
        "Pre_Treatment_RMSE",
        "Average_Post_Treatment_Gap",
        "Cumulative_Post_Treatment_Gap",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        return error_response(
            f"Summary CSV is missing required columns: {missing}",
            422
        )

    return jsonify({
        "success": True,
        "treatment_date": (
            TREATMENT_DATE.strftime("%Y-%m-%d")
        ),
        "treated_region": TREATED_REGION,
        "donor_region_count": 9,
        "outcomes": clean_records(df),
    })


# --------------------------------------------------
# REVENUE
# --------------------------------------------------

@app.route("/api/revenue", methods=["GET"])
def revenue():
    return outcome_data(
        "Revenue_Proxy_synthetic_control.csv",
        "Revenue_Proxy"
    )


# --------------------------------------------------
# SALES
# --------------------------------------------------

@app.route("/api/sales", methods=["GET"])
def sales():
    return outcome_data(
        "Sales_Volume_synthetic_control.csv",
        "Sales_Volume"
    )


# --------------------------------------------------
# OUTCOME DATA
# --------------------------------------------------

def outcome_data(filename, outcome_name):
    df, error = load_csv(filename)

    if error:
        return error_response(error)

    required = [
        "Date",
        "Actual",
        "Synthetic",
        "Gap"
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        return error_response(
            f"{filename} is missing required columns: {missing}",
            422
        )

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["Date"]
    ).sort_values("Date")

    try:
        start = request.args.get("start")
        end = request.args.get("end")

        if start:
            df = df[
                df["Date"] >= pd.to_datetime(
                    start,
                    errors="raise"
                )
            ]

        if end:
            df = df[
                df["Date"] <= pd.to_datetime(
                    end,
                    errors="raise"
                )
            ]

    except (ValueError, TypeError):
        return error_response(
            "Invalid start/end date. Use YYYY-MM-DD.",
            400
        )

    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    return jsonify({
        "success": True,
        "outcome": outcome_name,
        "treatment_date": (
            TREATMENT_DATE.strftime("%Y-%m-%d")
        ),
        "records": clean_records(df),
    })


# --------------------------------------------------
# SYNTHETIC CONTROL WEIGHTS
# --------------------------------------------------

@app.route("/api/weights", methods=["GET"])
def weights():
    df, error = load_csv(
        "synthetic_control_weights.csv"
    )

    if error:
        return error_response(error)

    required = [
        "Outcome",
        "Donor_Region",
        "Weight"
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        return error_response(
            f"Weights CSV is missing required columns: {missing}",
            422
        )

    outcome = request.args.get("outcome")

    if outcome:
        df = df[
            df["Outcome"].astype(str) == outcome
        ]

    return jsonify({
        "success": True,
        "records": clean_records(df),
    })


# --------------------------------------------------
# PLACEBO TEST
# --------------------------------------------------

@app.route("/api/placebo", methods=["GET"])
def placebo():
    df, error = load_csv(
        "placebo_test_results.csv"
    )

    if error:
        return error_response(error)

    return jsonify({
        "success": True,
        "note": (
            "Placebo comparisons are diagnostic results "
            "and are not, by themselves, definitive "
            "significance tests."
        ),
        "records": clean_records(df),
    })


# --------------------------------------------------
# DATA EXPLORER
# --------------------------------------------------

@app.route("/api/data", methods=["GET"])
def data_explorer():
    df, error = load_csv(
        "analysis_ready_data.csv"
    )

    if error:
        return error_response(error)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        )

        try:
            start = request.args.get("start")
            end = request.args.get("end")

            if start:
                df = df[
                    df["Date"] >= pd.to_datetime(
                        start,
                        errors="raise"
                    )
                ]

            if end:
                df = df[
                    df["Date"] <= pd.to_datetime(
                        end,
                        errors="raise"
                    )
                ]

        except (ValueError, TypeError):
            return error_response(
                "Invalid start/end date. Use YYYY-MM-DD.",
                400
            )

        region = request.args.get("region")

        if region:
            region_column = next(
                (
                    column
                    for column in [
                        "Region_ID",
                        "Region",
                        "Region_Name"
                    ]
                    if column in df.columns
                ),
                None
            )

            if region_column:
                df = df[
                    df[region_column].astype(str) == region
                ]

        df["Date"] = df["Date"].dt.strftime(
            "%Y-%m-%d"
        )

    limit = request.args.get(
        "limit",
        default=500,
        type=int
    )

    if limit is None:
        limit = 500

    limit = max(1, min(limit, 5000))

    return jsonify({
        "success": True,
        "total_returned": min(len(df), limit),
        "total_matching": len(df),
        "records": clean_records(df.head(limit)),
    })


# --------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": (
            "Invalid request. Check the supplied date "
            "or filter values."
        ),
    }), 400


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "An unexpected server error occurred.",
    }), 500


# --------------------------------------------------
# RUN FLASK SERVER
# --------------------------------------------------

if __name__ == "__main__":
    print("Starting Causal Inference API...")
    print(f"App directory: {APP_DIR}")
    print(f"Analysis directory: {ANALYSIS_DIR}")
    print(
        f"Results directories: {RESULTS_DIR_CANDIDATES}"
    )
    print("API address: http://127.0.0.1:5000")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
