# Prediction Engine V1 final research report

> INTERNAL EXPLORATORY RESEARCH — NOT FOR CUSTOMER USE OR TRADING

## Decision

`HOLDOUT_PASS / FORWARD_VALIDATION_REQUIRED`. All preregistered holdout criteria passed: `true`. This is not verified edge. Forward paper validation is mandatory and has not started.

## Dataset and registration

- Dataset: `7ce7f964ca6aa8b551c68749e5f2d8a5a95e5e6c7b08005350807431fd866e6b`; 442,837 rows, 200 current-universe symbols, 2016-09-07 through 2026-09-04.
- Registration: `ec4f05506d933cbcf6e0ebb8b2c7950167983e5c20397c02d52f8c3f03bf0e45`.
- Holdout: 2025-01-01 through 2026-09-04; slice `ded857e94076cbae260fabd8dd457cb8190b6bf79dcfa6275661c25450a6bb48`; access count `1`.
- Universe: `SURVIVORSHIP_BIASED_CURRENT_UNIVERSE`. Point-in-time membership is unavailable.
- Structural actions: 10 events and 410 surrounding rows excluded. Adjustment semantics remain unverified.

## Walk-forward and sealed holdout

| Horizon | Candidate | Validation Brier | Holdout Brier | Baseline Brier | Holdout ECE | Coverage |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1D | logistic | 0.6495 | 0.6472 | 0.6518 | 0.0073 | 0.32% |
| 3D | regularized_logistic | 0.6446 | 0.6428 | 0.6482 | 0.0074 | 0.37% |
| 5D | logistic | 0.6420 | 0.6433 | 0.6484 | 0.0067 | 0.21% |
| 10D | logistic | 0.6400 | 0.6433 | 0.6463 | 0.0257 | 22.91% |

Thirty-six preregistered model/fold evaluations were retained. The models were fitted on expanding history, calibrated on the preceding 126 sessions, and purged by the horizon. Rows are a temporally and cross-sectionally dependent panel, not IID observations.

## Calibration, abstention, and OOD

Sigmoid calibration was selected before holdout. Probability means estimated target-class probability—not confidence and not profit probability. The frozen abstention rule uses 0.45 maximum probability, 0.08 top-two separation, model-disagreement, data-quality, and train-relative OOD gates.

Coverage is extremely low for 1D, 3D, and 5D. That materially limits usefulness even though unconditional holdout metrics improved. Thresholds were not retuned after seeing this result.

## Null controls and multiplicity

Date-block circular label permutations were used instead of row shuffling. Four selected horizon hypotheses remained below 0.05 after BH and Holm adjustment. Experiment count: 36.

## Baselines and unsupported outputs

Unconditional class probability is the scored primary baseline. Market-direction, momentum, and mean-reversion rules are retained as research comparators in the architecture; sector-relative evaluation is unavailable because validated point-in-time sector membership is absent. Expected return, future range, and barrier probabilities remain nullable/disabled because no preregistered regression candidate was promoted in V1.

## Economic sanity

No execution or strategy backtest was built. Low/moderate/high friction assumptions of 10/25/50 bps are recorded only as sensitivity boundaries; the small discrimination improvements and low coverage do not support an economic edge claim.

## False-positive and stability warnings

- `SURVIVORSHIP_BIAS`
- `CORPORATE_ACTION_UNCERTAINTY`
- `MULTIPLE_TESTING_RISK`
- `VERY_LOW_COVERAGE_1D_3D_5D`
- `SINGLE_PROVIDER_INTERNAL_RESEARCH`
- `INTELLIGENCE_FEATURE_HISTORY_INSUFFICIENT`

No LLM generated a probability. Intelligence engines were excluded from training. No public output, BUY/SELL, target price, sizing, execution, or forward prediction was activated.
