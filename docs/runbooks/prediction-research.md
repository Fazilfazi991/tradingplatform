# Prediction research runbook

1. Confirm Git HEAD and a clean working tree. Verify the manifest dataset hash is exactly `7ce7f964ca6aa8b551c68749e5f2d8a5a95e5e6c7b08005350807431fd866e6b`.
2. Run `scripts/register_prediction_v1.py` once and commit the sealed registration before evaluation.
3. Run `scripts/run_prediction_v1.py validation ...`. Review every fold, failed candidate, null control, correction, and selection. Commit the pre-holdout decision.
4. Confirm its registration and holdout-slice hashes. Run `scripts/run_prediction_v1.py holdout ...` once.
5. Run backend, Ruff, Mypy, dependency, secret, frontend, and diff checks. Commit reports only when they contain no source dataset or secret.

Never delete negative results, rerun the same holdout as a new validation, change the frozen registration, publish forecast output, or initiate paper predictions. A critical methodology defect invalidates the experiment version; record it and start a newly registered future experiment.
