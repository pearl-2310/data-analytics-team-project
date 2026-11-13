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
