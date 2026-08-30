# Prediction validation methodology

Primary evaluation is chronological. Random train/test splitting is prohibited. Walk-forward
partitions can expand or roll; target horizons automatically impose purge windows, and configured
embargo sessions remove observations immediately after validation begins. Partition manifests are
sealed and hash the dataset, universe, feature set, target, dates, rules, and code.

Classification reports accuracy, balanced accuracy, precision, recall, F1, ROC AUC, PR AUC, Brier,
log loss, and calibration error. Regression reports MAE, RMSE, R², rank correlation, direction, and
prediction/actual correlation. Economic diagnostics use prediction deciles rather than simulated
customer trades. Bootstrap intervals expose sampling uncertainty.

Calibration uses a dedicated chronological calibration partition and supports sigmoid and isotonic
methods. Final test data is never used to fit the calibrator. Scaling and imputation live inside
scikit-learn pipelines and are fitted only on training data.

Every study records parameter budget and attempted hypotheses. Benjamini–Hochberg and Holm utilities
support later family-level multiplicity control. Planted-edge, null, shuffled-target, leakage-attack,
and deterministic replay tests are mandatory engineering checks—not evidence of market performance.
