# Prediction V1 methodology

The immutable registration in `research/prediction-v1/prediction-v1-registration.json` owns the dataset, features, targets, candidates, splits, seeds, calibration, abstention, multiple-testing policy, and holdout criteria. Results cannot amend it.

Discovery ends in 2021. Walk-forward validation uses expanding histories and annual 2022, 2023, and 2024 blocks. Each fold reserves the preceding 126 sessions for sigmoid calibration and purges at least the forecast horizon between training and calibration. The contiguous 2025-01-01–2026-09-04 slice is sealed and evaluated once, after the selected candidates are written and committed.

V1 evaluates three preregistered classifiers over four horizons. Metrics prioritize multiclass Brier, log loss, and ECE; balanced accuracy and same-date cross-sectional Spearman IC are secondary. Rows are not IID. Fold, year, regime, horizon, and panel dependence qualify every aggregate.

Date-block circular permutations preserve clusters better than row shuffling. BH and Holm adjustments expose search breadth. Negative experiments remain in the report. A holdout pass only yields `FORWARD_VALIDATION_REQUIRED`.
