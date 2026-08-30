# DR-007: Prediction research engine

Status: Accepted for fixture engineering  
Date: 2026-08-30

## Decision

Build the research machinery now while preserving the external-data block. The prediction system
evaluates probabilistic forecasts, not merely trading-strategy P/L. Calibration, chronological
stability, uncertainty, baseline comparison, and leakage resistance are first-class outcomes.

The only currently authorized runtime mode is `ENGINEERING_FIXTURE`. Formal discovery, sealed
validation, holdout, and forward modes require live market-data validation, PostgreSQL runtime
verification, effective-dated universe membership, corporate-action correctness, and an accepted
second-source decision. The policy raises an error when these gates are absent.

Synthetic edge recovery demonstrates that machinery can recover a known planted relationship.
Synthetic null and shuffle tests demonstrate resistance to manufactured edge. Neither is market
evidence, and no result may replace demo customer predictions or change DR-005/DR-006.
