# Real-data false-positive controls

Controls include immutable preregistration, a small model family, explicit experiment counts, chronological folds, horizon-aware purging, train-only preprocessing, validation-only calibration, same-date panel tracking, date-block null permutations, BH/Holm adjustment, baseline comparison, and single holdout access.

Warnings are retained when applicable: `OVERCONFIDENT_MODEL`, `POOR_CALIBRATION`, `INSUFFICIENT_SAMPLE`, `UNSTABLE_ACROSS_FOLDS`, `NO_BASELINE_IMPROVEMENT`, `MULTIPLE_TESTING_RISK`, `SURVIVORSHIP_BIAS`, `CORPORATE_ACTION_UNCERTAINTY`, `REGIME_INSTABILITY`, and `HOLDOUT_DEGRADATION`.

Current-universe selection and a single market-data provider are structural limitations, not statistical footnotes. A positive holdout is candidate evidence only. Forward paper validation is mandatory.
