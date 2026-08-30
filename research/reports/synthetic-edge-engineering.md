# SYNTHETIC ENGINEERING EXPERIMENT — NOT MARKET EVIDENCE

## Hypothesis
Recover planted autoregressive relationship

## Dataset and universe
Deterministic five-instrument fixture; dataset `466bd48449b998443285d276f27a926f792beeb5adcdc64083f6ab17fbfe5a1c`. No real-market universe.

## Target and features
Five-session direction target. Feature set `f4e708f683f3737c6ba6eda3464b012f9d09beece186a897e35cbed06e7cccd6`. Information boundary is after session close.

## Partitions / purge / embargo
Chronological training, calibration, and test partitions: `{"calibration_end": "2025-01-10 00:00:00+00:00", "chronological": true, "test_end": "2025-03-17 00:00:00+00:00", "train_end": "2024-11-12 00:00:00+00:00"}`. Formal target-overlap controls are provided by the partition engine.

## Model and baselines
Logistic regression with train-only imputation/scaling; unconditional base-rate baseline. Parameter budget: `{"model_configurations": 1, "feature_sets": 1, "thresholds": 1}`.

## Results and calibration
Metrics: `{"accuracy": 0.6434782608695652, "balanced_accuracy": 0.6402951102739188, "brier": 0.22427489582475243, "calibration_error": 0.12561951929938217, "f1": 0.5858585858585859, "log_loss": 0.6399697490538865, "pr_auc": 0.6472733617839022, "precision": 0.5523809523809524, "recall": 0.6236559139784946, "roc_auc": 0.6968840750333569}`. Baseline: `{"accuracy": 0.5956521739130435, "balanced_accuracy": 0.5, "brier": 0.24147110838073363, "calibration_error": 0.024908768637264156, "f1": 0.0, "log_loss": 0.676008125119748, "pr_auc": 0.4043478260869565, "precision": 0.0, "recall": 0.0, "roc_auc": 0.5}`.

## Feature importance / stability
Standardized linear coefficients: `{"atr_price_14": -0.19555720163335438, "drawdown_60": -0.13783530868908334, "return_1": 1.1387928701016174, "return_20": -0.7533427286853004, "return_5": -0.3240121438163636, "rsi_14": 0.7322824243244568, "sma_distance_pct_20": 0.5914772269659005, "volume_median_ratio_20": -0.06005617029666586}`.

## Sanity and leakage checks
Shuffled-target metrics: `{"accuracy": 0.5782608695652174, "balanced_accuracy": 0.4854014598540146, "brier": 0.2519931573271429, "calibration_error": 0.13258907500460937, "f1": 0.0, "log_loss": 0.6977375757488262, "pr_auc": 0.32521465101323616, "precision": 0.0, "recall": 0.0, "roc_auc": 0.34463542893022525}`. Future/target-derived feature names are rejected separately by the feature contract.

## Limitations and decision
This run validates machinery only. It is not evidence of market edge and cannot become customer-visible. Formal research remains blocked.

## Artifact hashes
Model: `ca6896f19b18830a2f23ba54b8c1f8588911ba98eaf857689fbf8c22826d7c77`.
