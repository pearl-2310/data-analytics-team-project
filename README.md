# Causal Inference & Synthetic Control Engine for Algorithmic Pricing

## 1. Project Overview

The **Causal Inference & Synthetic Control Engine for Algorithmic Pricing** is a team data analytics project that aims to analyze the impact of algorithmic pricing changes using synthetic panel data and causal inference techniques.

The project focuses on comparing a treated region with other regions to understand pricing and sales patterns before and after a pricing intervention. It also includes plans for an interactive dashboard to present analytical findings and visualizations.

## 2. Project Objectives

- Prepare and validate synthetic panel data for analysis.
- Explore pricing and sales trends across multiple regions.
- Analyze the impact of a pricing intervention using causal inference and synthetic control methods.
- Develop visualizations and an interactive dashboard.
- Document the methodology, validation process, and findings.

## 3. Project Structure

```text
data-analytics-team-project/
│
├── data-preparation/
│   ├── synthetic_pricing_data.csv
│   └── Synthetic_Panel_Generators_Experimental.ipynb
│
├── causal-analysis/
│
├── dashboard-creation/
│
└── README.md
```

The `causal-analysis/` and `dashboard-creation/` folders are designated for the respective team components. Their contents will be added as the work progresses.

## 4. Dataset Overview

The project uses a synthetically generated panel dataset containing daily observations across 10 regions from January 2023 to December 2025.

**Dataset details:**

- Number of regions: 10
- Total observations: 10,950
- Observation frequency: Daily
- Treatment region: Region_1
- Treatment date: March 10, 2025
- Data type: Synthetic data generated for educational and analytical purposes

### Key Variables

| Variable | Description |
|---|---|
| `Date` | Date of the observation |
| `Region_ID` | Identifier for each region |
| `Price` | Product price in the region |
| `Sales_Volume` | Sales volume recorded |
| `Competitor_Price` | Competitor pricing information |
| `Regional_Google_Trends_Index` | Regional search interest indicator |
| `Treated` | Indicates whether the region is the treated region |
| `Post_Treatment` | Indicates whether the observation occurs on or after the treatment date |
| `Treatment_Effect` | Interaction indicator for the treated region and post-treatment period |

## 5. Data Preparation

The data preparation component establishes a consistent dataset for subsequent analysis.

The main activities include:

- Loading and inspecting the synthetic dataset.
- Reviewing column names, data types, and dataset dimensions.
- Checking for missing values and duplicate records.
- Validating treatment and post-treatment indicators.
- Reviewing the distribution of observations across regions and time periods.
- Exploring pricing and sales trends through summary statistics and visualizations.
- Saving the prepared dataset in CSV format for use by other team members.

The final dataset contains 10,950 rows and 9 columns, with no missing values or duplicate rows.

## 6. Project Methodology

The project is organized into the following stages:

1. **Data Preparation:** Generate, inspect, and validate the synthetic panel dataset.
2. **Causal Analysis:** Apply suitable causal inference and synthetic control techniques to evaluate the pricing intervention.
3. **Dashboard Development:** Present relevant data patterns and analytical findings through visualizations.
4. **Validation and Documentation:** Review the workflow, validate outputs, and document the methodology and results.

## 7. Team Contributions

The project is divided into four areas of responsibility:

- **Member 1 — Data Preparation:** Dataset generation, inspection, cleaning checks, validation, and exploratory visualizations.
- **Member 2 — Causal Analysis:** Causal inference methodology and synthetic control analysis.
- **Member 3 — Dashboard Creation:** Dashboard development and visualization of analytical findings.
- **Member 4 — Validation and Documentation:** Output validation, project documentation, and reporting.

## 8. How to Access the Files

The `data-preparation/` folder contains the dataset and the notebook used for data generation and preparation.

- **Dataset:** `synthetic_pricing_data.csv`
- **Notebook:** `Synthetic_Panel_Generators_Experimental.ipynb`

The CSV file can be opened using spreadsheet software or Python. The notebook can be opened using Jupyter Notebook or Google Colab.

To use the notebook in a local Python environment, install Python and Jupyter Notebook, then open the notebook from the project directory.

## 9. Tools and Technologies

The project uses the following tools and formats, as applicable to the implemented workflow:

- Python
- Jupyter Notebook
- Pandas and NumPy for data handling
- Matplotlib for data visualization
- CSV for dataset storage
- Git and GitHub for version control and collaboration

Additional libraries and tools may be used for the causal analysis and dashboard components.

## 10. Expected Outcomes

The project aims to provide:

- A structured synthetic panel dataset ready for analysis.
- An analysis of pricing and sales patterns across regions.
- An assessment of the pricing intervention using causal inference methods.
- Visualizations and a dashboard for communicating findings.
- Documentation describing the methodology, validation, and limitations.

The actual findings will depend on the completed analysis and validation.

## 11. Disclaimer

This project uses synthetically generated data for educational and analytical purposes. The dataset does not represent actual company transactions or verified real-world market outcomes.

Any conclusions drawn from the analysis should be interpreted within the limitations of the synthetic data and the assumptions of the methods used. The results should not be treated as verified evidence of real-world pricing effects.