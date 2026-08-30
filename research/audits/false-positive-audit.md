# FALSE-POSITIVE ROBUSTNESS AUDIT — NOT MARKET EVIDENCE

## Decision summary

The 1,000-seed IID null distribution centered at ROC AUC 0.5013. The original 0.6405 result is at
the 99.9th percentile (empirical p 0.002) of this implemented null and is therefore unusual, not an
ordinary central result. It remains `NO_EDGE` because its preregistered Brier improvement was negative.
The audit found no hidden target leakage; it found a rare one-off secondary metric that the prior
report did not contextualize strongly enough.

## Primary null Monte Carlo

- Runs: 1,000 deterministic seeds; 195 chronological test observations per run.
- AUC mean/median/std: 0.5013 / 0.5025 / 0.0414.
- AUC 2.5%–97.5%: 0.4184–0.5828; minimum/maximum: 0.3493–0.6436.
- P(AUC ≥ 0.60): 0.006; ≥0.64: 0.001; ≥0.65: 0; ≥0.70: 0.
- Mean Brier improvement: -0.00104; only 39.7% of null runs beat the Brier baseline.
- Mean ECE: 0.0426; 95th percentile ECE: 0.1044.

## Size and dependence

AUC standard deviation fell from 0.0600 at 500 observations to 0.0129 at 10,000. IID,
autocorrelated-feature, market-factor, volatility-clustered, regime-looking, and cross-sectional nulls
all centered between 0.4950 and 0.5016. Panels with 5, 20, 100, and 200 instruments centered between
0.4987 and 0.5036. A 1,000-row, five-instrument, five-session-horizon example has conservative
effective N 38 and triggers overlap, cross-sectional-dependence, and insufficient-sample warnings.

## Permutation and uncertainty

Five-row block permutation gave null AUC 0.4990, empirical p 0.537, and moving-block 95% CI
0.4615–0.5367. A planted case gave AUC 0.6801, empirical p 0.002, and CI 0.6455–0.7127.

## Researcher degrees of freedom

Selecting the best of 1, 5, 10, 25, 50, and 100 null models raised median apparent AUC from 0.5006
to 0.5911. Selecting among 10, 50, 100, 500, and 1,000 noise features raised it from 0.5545 to
0.6159. These are selection artifacts, not edge.

All-null simulations produced at least one false discovery in 6.0% of Benjamini–Hochberg families
and 5.4% of Holm families at alpha 0.05, consistent with finite Monte Carlo variation around the
intended family error behavior.

## Stability and planted recovery

Null walk-forward fold AUCs were 0.4335, 0.4708, 0.5004, 0.5377, and 0.4921. Planted fold AUCs
were 0.7870, 0.7684, 0.7966, 0.7244, and 0.7411. Across 250 planted seeds, every run beat the Brier
baseline; median Brier improvement was 0.0353 and median AUC was 0.7323.

Signal-strength mean AUC rose monotonically: 0.5049 at zero, 0.5155 very weak, 0.5605 weak,
0.6488 medium, and 0.7314 strong.

## Historical analogues

Across 250 null queries, analogue outcome bias remained near zero. Mean bias ranged from 0.00008 at
K=10 to -0.0030 at K=200. Standard deviation fell from 0.1543 to 0.0306, demonstrating why low-K
analogue narratives require minimum-sample warnings.

## Controls

Reports now reserve an automatic null-context section. The registry validates the primary metric,
requires positive core attempt budgets, and includes primary metric, testing family, and budgets in
the immutable configuration hash. Warnings cover overconfidence, poor calibration, insufficient
samples, fold instability, no baseline improvement, and multiple-testing risk. Formal research modes
remain blocked; all results here are `ENGINEERING_FIXTURE` evidence only.
