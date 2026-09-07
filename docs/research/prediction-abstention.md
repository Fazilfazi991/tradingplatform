# Prediction abstention and OOD

V1 abstains when maximum calibrated probability is below 0.45, the top-two separation is below 0.08, model disagreement exceeds 0.18, the row is strongly out of distribution, history is insufficient, or data/corporate-action quality blocks use. These thresholds are frozen before holdout.

OOD is deterministic and train-relative. Each feature is compared with training-only location and scale: at least two values beyond four standard deviations is `WEAK_OOD`; at least four is `STRONG_OOD`; otherwise it is `IN_DISTRIBUTION`. Missing or unusable diagnostics return `UNKNOWN`.

Reports show coverage, abstention rate, covered-set metrics, and reason counts. Abstention is not silently scored as a directional class.
