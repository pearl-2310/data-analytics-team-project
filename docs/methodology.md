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
