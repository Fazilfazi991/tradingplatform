# DR-008: False-positive control

Status: Accepted for fixture engineering  
Date: 2026-08-30

## Decision

No prediction model may progress because of one attractive metric or one successful experiment run.

Probability experiments preregister a primary metric, normally Brier score, and a complete attempt
budget. Results require chronological stability, baseline improvement, null/permutation context,
dependence-aware uncertainty, calibration quality, and immutable accounting. Secondary metrics cannot
override a failed primary metric.

Permitted decisions are `NO_EDGE`, `INCONCLUSIVE`, `CANDIDATE_EDGE`, `VALIDATION_REQUIRED`,
`SYNTHETIC_EXPECTED_EDGE`, and `ENGINEERING_FAILURE`. Formal market-research decisions remain blocked.
`CANDIDATE_EDGE` cannot be assigned solely because AUC exceeds 0.5 or accuracy exceeds baseline.

Abstention as `INCONCLUSIVE` or insufficient evidence is preferred when evidence is weak, unstable,
dependent, poorly calibrated, or exposed to multiple-testing risk.
