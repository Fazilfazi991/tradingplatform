# Sealed holdout policy

The recent contiguous interval 2025-01-01 through 2026-09-04 is sealed by date boundaries and a dataset-slice hash. Feature design, candidate selection, hyperparameters, calibration, abstention, and pass criteria use discovery and walk-forward validation only.

Before access, `prediction-v1-pre-holdout-decision.json` must identify every selected candidate and match the immutable registration hash. The holdout command fails closed without it or on slice-hash mismatch. The batch permits one evaluation. Any model change after results creates a new experiment version and requires future validation; the same holdout cannot be relabelled as fresh validation.
