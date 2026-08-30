# False-positive control

Attractive metrics occur under null data. Finite test sets produce sampling variance; overlapping
horizons, shared market shocks, repeated instruments, feature mining, model selection, and metric
choice further reduce the effective amount of independent evidence. One high AUC is not a conclusion.

Verified Edge preregisters Brier score as the default probability-forecast metric. ROC AUC, PR AUC,
accuracy, and economic separation are complementary diagnostics and cannot replace the primary metric
after results are known. Reports must show baseline improvement, dependence-aware uncertainty, null
percentile, empirical p-value, attempt budget, warnings, and a conservative decision.

Null Monte Carlo includes IID, autocorrelated-feature, market-factor, volatility-clustered,
regime-looking, and cross-sectionally correlated panels. Block permutations preserve local temporal
dependence; moving-block bootstrap intervals avoid treating rows as IID. Effective-sample warnings
account for target overlap, serial correlation, and multiple securities observed on the same date.

Trying many models or noise features raises the best observed AUC even when every candidate is null.
The immutable registry therefore hashes model, feature, target, threshold, and parameter budgets.
Additional attempts require a new configuration. Benjamini–Hochberg and Holm adjustments apply to
declared hypothesis families.

Historical analogues are subject to the same rule: similarity is descriptive evidence, not certainty.
Null analogue studies must center on the unconditional outcome, and low K produces a sample warning.
Extreme probabilities with poor reliability trigger `OVERCONFIDENT_MODEL`.

Fast validation: `python -m pytest -m "not stress"`.

Full validation: `python scripts/run_false_positive_audit.py`, then `python -m pytest -m stress`.

All current studies use `ENGINEERING_FIXTURE` data and are not market evidence.
