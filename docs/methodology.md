# Methodology

This document explains, in plain English, what the project does and why. No advanced statistics is assumed.

## 1. The question

In March 2025, **Region_1 raised its price by 15 %**. Nine other regions did not. We want to know what the price rise did to
**sales volume** and to **revenue**.

A simple before/after comparison is misleading. Between "before" and "after", the season changed, the market moved and competitors changed their prices.
Those things affect every region, so they get mixed into the result. We need to know what Region_1 would have done **if the price had not changed**.
That "what if" is called the **counterfactual**, and we can never observe it directly. We have to estimate it.

## 2. The data

A simulated panel: **10 regions x 1,095 days** (1 Jan 2023 to 30 Dec 2025).

- **Treated unit:** Region_1 (price rises 15 % from 2025-03-10, day 800).
- **Donor pool:** the other nine regions, whose prices follow only the normal slow upward drift.
- **Before period:** 799 days. **After period:** 296 days.

The data is built from a demand model in which sales fall by 2.5 units for every 1 unit of price, and rise with competitor price, search interest (Google Trends index) and season.
All regions share the same season and trend, which is what makes the donors good comparisons. Column details are in [`data_dictionary.md`](data_dictionary.md).

Because we wrote the data-generating rules, we know the true effect. That lets us check the method against the truth, which is impossible with real data.

## 3. Synthetic Control Method

**Idea:** no single region looks exactly like Region_1, but a *weighted mixture* of regions might.

1. Look only at the **before period**.
2. Find a weight for each donor so that the weighted average of donor sales follows Region_1's sales as closely as possible.
   - Weights cannot be negative.
   - Weights add up to 100 %.
   - "As closely as possible" means the smallest average squared difference (an optimisation problem solved with `scipy`'s SLSQP method).
3. Keep those weights fixed and apply them to the **after period**. The weighted average is the **synthetic Region_1**, an estimate of what Region_1 would have done without the price rise.
4. **Gap = real Region_1 - synthetic Region_1.** After the price change, the average gap is the estimated effect, and the sum of the gaps is the cumulative effect.

Example from the results: for sales, the synthetic Region_1 is roughly 23 % Region_10, 22 % Region_2, 22 % Region_6, 16 % Region_8, 10 % Region_9, 4 % Region_3, 3 % Region_7, and 0 % for Regions 4 and 5.

The method is run twice: once for **Sales_Volume** and once for **Revenue_Proxy** (Price x Sales).

**Pre-treatment RMSE** (root mean squared error before the price change) measures how well the synthetic region matches the real one. Small is good: here it is about 1.9 % of the average level.

## 4. Placebo test (is the gap really unusual?)

If we ran the same method on a region that did *not* change its price, we would expect a gap of about zero. So we do exactly that, for every untreated region in turn, as if each were the treated one.

For each region we compute the **post/pre RMSE ratio**: how big the error is after the date compared with before it. A ratio near 1 means "nothing happened".
Region_1's ratio is 2.99 for revenue and 2.61 for sales; all nine placebo regions are between 0.89 and 1.13. Region_1 is the clear outlier.

With 10 regions the smallest possible p-value is 1/10 = 0.10, so the result is described as "most extreme of 10 regions", not as significant at 5 %.

## 5. Extra checks used in validation

| Check | What it tests | Result |
|---|---|---|
| **In-time placebo** | Pretend the price change happened on 2024-07-01. Do we find an effect? We should not. | About 1 to 2 % of the real estimate |
| **Leave-one-donor-out** | Remove each donor in turn and re-estimate. Is the answer stable? | Sales changes by at most 1.8 % |
| **Difference-in-differences** | A simpler, different method: (change in Region_1) minus (change in donor average) | -40.1 vs -39.4 for sales |
| **Comparison with the truth** | Compare estimates with the effect computed from the data generator | Sales within 2.2 % |

## 6. Reading the results

- **Sales:** about -39 units/day (-8 %). Customers bought fewer units at the higher price.
- **Revenue:** about +2,700 to +2,900/day (+5 %). Fewer units, but each one sold for 15 % more.
- **Rough price elasticity:** -8.1 % / +15 % = about -0.54. A 1 % price rise is associated with about 0.5 % fewer sales.
- `Revenue_Proxy` is Price x Sales, so a price rise lifts it by construction. Treat **sales** as the cleaner measure of the demand response.

## 7. Limitations

- **Simulated data.** Real markets are messier; the true effect is known only because we created it.
- **One treated region, nine donors.** Results depend on the donors being good comparisons, and no confidence interval is available.
- **No spillovers modelled.** The method assumes the other regions were not affected by Region_1's price change.
- **Double Machine Learning is not implemented**, although the data contains the confounders (`Competitor_Price`, `Regional_Google_Trends_Index`) it would need.

## 8. Glossary

| Term | Meaning |
|---|---|
| Treated unit | The region that received the intervention (Region_1) |
| Donor pool | Untreated regions used to build the comparison |
| Counterfactual | What would have happened without the intervention |
| Synthetic control | Weighted mix of donors that imitates the treated unit before the intervention |
| Gap | Real value minus synthetic value |
| RMSE | Typical size of the error between real and synthetic series |
| Placebo test | Applying the method to units that were not treated, to see how large "fake" effects can be |
| Confounder | A factor (season, trend, competitor price) that influences both price and sales |
