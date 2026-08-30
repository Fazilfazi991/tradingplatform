# Prediction research engine architecture

## Scope and lock

`services/research-core` builds prediction-research machinery without claiming market edge. Its
runtime policy permits `ENGINEERING_FIXTURE` only. Formal discovery fails unless live data,
PostgreSQL runtime, point-in-time universe, corporate actions, and second-source gates all pass.

## Flow

Immutable observations flow through a causal cutoff (`available_at <= T`) into deterministic,
versioned feature matrices. Target generation is a separate module and uses future bars only for
training/evaluation labels. Chronological partitions fit imputation, scaling, models, and
calibration exclusively on their assigned past partitions. Evaluation compares models with frozen
baselines, calibration diagnostics, economic deciles, uncertainty intervals, and sanity tests.

Historical analogues standardize candidate states using prior candidates and support Euclidean or
cosine comparison. Candidates must predate the query; optional exclusion windows prevent same-event
and overlapping-window dominance. Technical and historical evidence engines emit a common research
contract. Fusion types exist, but no production fusion model exists.

Experiment configuration hashes bind dataset, feature set, target, model, partitions, code SHA, and
parameter budget. Registry and result artifacts are immutable. Reports state hypotheses, data,
partitions, calibration, sanity checks, limitations, and hashes.

## Research doctrine

1. Prediction accuracy alone is insufficient.
2. Probability calibration matters.
3. A model must beat reasonable baselines.
4. Results must survive chronological evaluation.
5. Prediction quality must remain stable across time.
6. Model confidence is not the same as probability.
7. Historical analogues are evidence, not certainty.
8. More features are not automatically better.
9. A failed model is an acceptable result.
10. No model becomes customer-visible merely because its backtest looks good.
