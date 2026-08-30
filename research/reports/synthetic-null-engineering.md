# SYNTHETIC ENGINEERING EXPERIMENT — NOT MARKET EVIDENCE

## Hypothesis
No stable out-of-sample relationship

## Dataset and universe
Deterministic five-instrument fixture; dataset `bdee1b38be28b513d2a67a22580d78efa007c66b9e7a40e5a1aaba179a700802`. No real-market universe.

## Target and features
Five-session direction target. Feature set `f4e708f683f3737c6ba6eda3464b012f9d09beece186a897e35cbed06e7cccd6`. Information boundary is after session close.

## Partitions / purge / embargo
Chronological training, calibration, and test partitions: `{"calibration_end": "2025-01-10 00:00:00+00:00", "chronological": true, "test_end": "2025-03-17 00:00:00+00:00", "train_end": "2024-11-12 00:00:00+00:00"}`. Formal target-overlap controls are provided by the partition engine.

## Model and baselines
Logistic regression with train-only imputation/scaling; unconditional base-rate baseline. Parameter budget: `{"model_configurations": 1, "feature_sets": 1, "thresholds": 1}`.

## Results and calibration
Metrics: `{"accuracy": 0.5304347826086957, "balanced_accuracy": 0.5692989832581608, "brier": 0.24876379775049828, "calibration_error": 0.0685673061917127, "f1": 0.6423841059602649, "log_loss": 0.6906719720026113, "pr_auc": 0.5495781649069307, "precision": 0.48743718592964824, "recall": 0.941747572815534, "roc_auc": 0.6405473587646204}`. Baseline: `{"accuracy": 0.5521739130434783, "balanced_accuracy": 0.5, "brier": 0.24782383664541616, "calibration_error": 0.023365655301845367, "f1": 0.0, "log_loss": 0.6888055012790741, "pr_auc": 0.44782608695652176, "precision": 0.0, "recall": 0.0, "roc_auc": 0.5}`.

## Feature importance / stability
Standardized linear coefficients: `{"atr_price_14": 0.06256165443179851, "drawdown_60": 0.17037968140700135, "return_1": -0.01738735100416244, "return_20": -0.3584106258938601, "return_5": -0.1300395968452457, "rsi_14": -0.07681701153980212, "sma_distance_pct_20": 0.558580165231071, "volume_median_ratio_20": -0.04030563285206995}`.

## Sanity and leakage checks
Shuffled-target metrics: `{"accuracy": 0.5434782608695652, "balanced_accuracy": 0.4985475116581301, "brier": 0.2553782287721438, "calibration_error": 0.09558598245080863, "f1": 0.11764705882352941, "log_loss": 0.7045832555335448, "pr_auc": 0.44904262766957126, "precision": 0.4375, "recall": 0.06796116504854369, "roc_auc": 0.4189282164972097}`. Future/target-derived feature names are rejected separately by the feature contract.

## Limitations and decision
This run validates machinery only. It is not evidence of market edge and cannot become customer-visible. Formal research remains blocked.

## Artifact hashes
Model: `f18c9778387717fd1dae95d6b4dae1c90b33de99fa5b3bbac9f2bd7460a3f8b9`.
