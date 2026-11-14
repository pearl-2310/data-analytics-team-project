# Data Dictionary

All dates are daily, from **2023-01-01 to 2025-12-30** (1,095 days). There are **10 regions** (`Region_1` to `Region_10`).
The data is **simulated**; it was created by the notebook in `data-preparation/`.

## 1. Raw dataset: `data-preparation/synthetic_pricing_data.csv`

10,950 rows (10 regions x 1,095 days), 9 columns.

| Column | Type | Meaning | Typical values |
|---|---|---|---|
| `Date` | date | Calendar day | 2023-01-01 to 2025-12-30 |
| `Region_ID` | text | Region name. `Region_1` is the treated region; the rest are donors | Region_1 ... Region_10 |
| `Price` | number | Selling price. Starts near 100 (each region differs slightly) and drifts up by 0.01 per day. **Region_1 is multiplied by 1.15 from 2025-03-10** | about 98 to 125 |
| `Sales_Volume` | number | Units sold that day. Built from a demand model: falls 2.5 units per 1 unit of price, rises with competitor price, search interest and season, plus random noise | about 413 to 551 |
| `Competitor_Price` | number | Price charged by competitors (a confounder). Around 98, with a slow cycle and noise | about 91 to 106 |
| `Regional_Google_Trends_Index` | number | Search interest in the region, a proxy for demand (a confounder). Around 50, with a yearly cycle, slight growth and noise | about 39 to 68 |
| `Treated` | 0 / 1 | `1` for every row of Region_1, `0` otherwise | 0 or 1 |
| `Post_Treatment` | 0 / 1 | `1` from 2025-03-10 onward, **for all regions** (a calendar flag) | 0 or 1 |
| `Treatment_Effect` | 0 / 1 | `Treated x Post_Treatment`: `1` only for Region_1 after 2025-03-10 | 0 or 1 |

Row counts: before the price change = 799 days per region, after = 296 days per region.

## 2. Analysis-ready dataset: `causal-analysis/analysis_ready_data.csv`

The raw dataset plus one column, created by `prepare_data.py`:

| Column | Type | Meaning |
|---|---|---|
| `Revenue_Proxy` | number | `Price x Sales_Volume`. A stand-in for daily revenue. Because it includes price, a price increase raises it by construction |

## 3. Result files: `causal-analysis/results/`

### `synthetic_control_summary.csv` (2 rows, one per outcome)

| Column | Meaning |
|---|---|
| `Outcome` | `Revenue_Proxy` or `Sales_Volume` |
| `Pre_Treatment_RMSE` | Typical size of the error between real and synthetic Region_1 **before** 2025-03-10 (smaller = better fit) |
| `Average_Post_Treatment_Gap` | Average daily difference (real minus synthetic) **after** 2025-03-10. This is the estimated effect per day |
| `Cumulative_Post_Treatment_Gap` | Sum of the daily gaps over the 296 days after the change |

### `synthetic_control_weights.csv` (18 rows = 2 outcomes x 9 donors)

| Column | Meaning |
|---|---|
| `Outcome` | `Revenue_Proxy` or `Sales_Volume` |
| `Donor_Region` | One of the nine untreated regions (Region_2 to Region_10) |
| `Weight` | Share of that donor in the synthetic Region_1. Between 0 and 1; each outcome's nine weights add up to 1 |

### `Sales_Volume_synthetic_control.csv` and `Revenue_Proxy_synthetic_control.csv` (1,095 rows each, one per day)

| Column | Meaning |
|---|---|
| `Date` | Calendar day |
| `Outcome` | Which outcome the row is about |
| `Actual` | Real Region_1 value |
| `Synthetic` | Weighted average of donors (the "no price change" estimate) |
| `Gap` | `Actual - Synthetic` |
| `Period` | `Pre-treatment` or `Post-treatment` |

### `placebo_test_results.csv` (20 rows = 2 outcomes x 10 regions)

| Column | Meaning |
|---|---|
| `Outcome` | `Revenue_Proxy` or `Sales_Volume` |
| `Target_Region` | The region treated *as if* it were the treated one (Region_1 is the real one) |
| `Pre_Treatment_RMSE` | Fit error before 2025-03-10 |
| `Post_Treatment_RMSE` | Fit error after 2025-03-10 |
| `Post_Pre_RMSE_Ratio` | `Post / Pre`. Near 1 = nothing unusual; much larger than 1 = a real effect |
| `Average_Post_Treatment_Gap` | Average daily gap after 2025-03-10 for that region |

The `.png` files in the same folder are charts of the two synthetic-control results.

## 4. Dashboard API: `dashboard-creation/backend/app.py`

The Flask backend runs on `http://127.0.0.1:5000` and serves the result files as JSON. All endpoints use `GET`.

| Endpoint | Returns | Optional filters |
|---|---|---|
| `/api/health` | Backend status and whether all 6 data files were found | none |
| `/api/summary` | Summary metrics for both outcomes | none |
| `/api/revenue` | Daily actual / synthetic / gap for revenue | `start`, `end` (dates, `YYYY-MM-DD`) |
| `/api/sales` | Daily actual / synthetic / gap for sales | `start`, `end` |
| `/api/weights` | Donor weights | `outcome` |
| `/api/placebo` | Placebo-test table | none |
| `/api/data` | Rows of the analysis-ready dataset | `region`, `start`, `end`, `limit` |

An invalid date returns HTTP 400 with an error message.

## 5. Units and caution

- `Price`, `Revenue_Proxy`: no currency is defined because the data is simulated.
- `Sales_Volume`: units sold per day per region.
- "Gap" values are **per day**, so an average gap of -39.4 for sales means about 39 fewer units per day.
