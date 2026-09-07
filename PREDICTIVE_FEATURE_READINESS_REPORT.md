# Predictive Feature Readiness Report

Status date: 2026-09-08  
Decision: **HOLDOUT VALIDATED — FORWARD REQUIRED**

## Completed evidence

- Fixed dataset and registration hashes.
- Causal feature/target controls and deterministic manifests.
- Chronological walk-forward evaluation with purge/embargo controls.
- Simple baselines, probability calibration, abstention, out-of-distribution checks, and corrected null controls.
- Sealed holdout completed with the limitations preserved in the authoritative research artifact.
- Internal-only destination enforcement for predictive outputs.
- Append-only forward issuance and outcome ledgers with uniqueness, causal availability,
  integrity hashes, and database-enforced update/delete rejection.
- A fail-closed forward-paper runtime now requires an explicitly approved hash-sealed package,
  atomically validates issuance batches against dataset/model/feature/code/horizon identities, and
  derives outcomes only from exact completed-session observations. Abstentions cannot receive
  outcomes. The committed runtime remains disabled and no package is configured.
- Forward reports expose coverage, abstention rate, multiclass Brier, and log loss only after real
  outcomes exist; otherwise metrics remain `INSUFFICIENT_FORWARD_OUTCOMES`.

## Material limitations

- `forward_predictions_started` is false in the authoritative holdout report.
- No eligible frozen deployable model artifact or approved package exists. Issuance and resolution
  entrypoints are implemented but disabled; no platform supervisor or live forward schedule operates.
- Coverage is very low at the 1D, 3D, and 5D horizons.
- Current-universe survivorship bias remains; point-in-time membership is unavailable.
- Corporate-action adjustment semantics and independent market-data reconciliation remain unresolved.
- No sufficient immutable forward sample, elapsed outcome window, regime coverage, drift record, or prospective calibration evidence exists.

## Required forward evidence

Predictions must be committed before their outcomes with issued-at time, eligible universe, horizon, model/dataset/config hashes, probabilities, abstention/OOD state, and immutable storage. Outcomes must be resolved separately after the horizon. Evaluation must report coverage, proper scoring, calibration, baselines, abstention utility, regimes, drift, incidents, and all failures without changing the sealed method during a measurement window.

## Public boundary

No public prediction, BUY/SELL, target price, return probability, performance claim, order, or broker connection is authorized.

## Gate

### PREDICTIVE FEATURE NOT READY — FORWARD VALIDATION REQUIRED
