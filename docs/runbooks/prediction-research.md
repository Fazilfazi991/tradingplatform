# Prediction research runbook

1. Confirm Git HEAD and a clean working tree. Verify the manifest dataset hash is exactly `7ce7f964ca6aa8b551c68749e5f2d8a5a95e5e6c7b08005350807431fd866e6b`.
2. Run `scripts/register_prediction_v1.py` once and commit the sealed registration before evaluation.
3. Run `scripts/run_prediction_v1.py validation ...`. Review every fold, failed candidate, null control, correction, and selection. Commit the pre-holdout decision.
4. Confirm its registration and holdout-slice hashes. Run `scripts/run_prediction_v1.py holdout ...` once.
5. Run backend, Ruff, Mypy, dependency, secret, frontend, and diff checks. Commit reports only when they contain no source dataset or secret.

Never delete negative results, rerun the same holdout as a new validation, change the frozen registration, publish forecast output, or initiate paper predictions. A critical methodology defect invalidates the experiment version; record it and start a newly registered future experiment.

## Forward-paper activation boundary

`config/forward-paper.json` is deliberately disabled. Enabling it is not sufficient to start
issuance: an approved, hash-sealed `FrozenForwardPackage` must also identify the exact dataset,
model artifact, feature configuration, registration, holdout report, horizons, code SHA, and blocked
public destination. The issuer accepts only an explicit batch whose records match that package.

Outcome resolution is a separate operation. It accepts an ordered completed-session window beginning
at the prediction cutoff, requires exactly `horizon + 1` closes, derives the return and neutral-band
class deterministically, and appends one outcome only after its causal availability time. Abstentions
cannot receive outcomes. Do not activate until the frozen deployable model artifact has been built,
independently reproduced, approved, and covered by a versioned forward protocol. Activating a model
or manufacturing current predictions is outside this runbook.

Inspect the gate without creating a ledger:

```powershell
.\.venv\Scripts\python.exe scripts\run_forward_paper.py --status
```

After a separately approved package and protocol exist, the same entrypoint supports explicit
`--issue <json>` and `--resolve <json>` jobs. They are intentionally separate invocations and can
write a sanitized ledger summary with `--report`. The committed configuration keeps both disabled.
