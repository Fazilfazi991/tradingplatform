# Prediction targets V1

Required horizons are 1, 3, 5, and 10 sessions. Completed historical windows provide forward close return, direction, future-path volatility, maximum favourable excursion, and maximum adverse excursion. The latest incomplete windows remain null.

Direction has three classes: DOWN, NEUTRAL, and UP. The neutral threshold is `0.25 × trailing 20-session daily volatility available at the prior session × sqrt(horizon)`. This past-only volatility-aware band prevents tiny returns from being forced into direction. Barrier definitions and target semantics are versioned by `PredictionTargetVersion`; no target may change after holdout access.

Structural corporate-action windows are excluded rather than treated as predictive outcomes while adjustment semantics remain unverified.
