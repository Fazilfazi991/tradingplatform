# Codex Live Intelligence Audit

The finalized SQLite ledger, cost ledger, cache, executions, canonical events, incident records, manifest, and generated reports were reconciled after the window.

- Validation failures recorded as `ValueError`: 76 attempts across 10 events
- Recovered events: 8
- Permanently failed events: 2
- Provider transport failures: none evidenced
- Provider-down warning: false positive from cumulative validation-error counting
- Mean latency: 4,471.65 ms
- P50 latency: 4,149.22 ms
- P95 latency: 6,994.54 ms
- Maximum latency: 15,875.96 ms
- Source failures: one SEBI ConnectTimeout, recovered on the next cycle
- Invalid cache payloads: zero
- Snapshots generated: zero
- Fusion attempts: zero; state remained ABSTAIN / PARTIAL_LIVE
- Full-content limitation: TITLE_METADATA_ONLY

Invalid results did not enter cache, evidence, snapshots, or Fusion. However, rejected response bodies, error categories, tokens, and cost were discarded. Consequently `$0.2107464` is a lower bound rather than a reconciled final cost.

## Recommendation

Retain ABSTAIN and repair forensic telemetry, provider-health classification, and handler-failure aggregation before another qualifying soak. Do not merge or activate the autonomous Research Operator.

### 24H LIVE INTELLIGENCE SOAK NEEDS WORK
