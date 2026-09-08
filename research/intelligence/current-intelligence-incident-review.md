# Current Intelligence Incident Review

Updated at 2026-09-08T08:58:03Z from the supervised post-soak runtime. The historical
24-hour soak report remains unchanged.

| Historical incident | Type | Historical status | Current status | Evidence |
|---|---|---|---|---|
| `dd7b1eaf-ed6a-4192-b27c-f7165444d7ab` | `LLM_HALLUCINATION_QUARANTINE` | OPEN | OPEN — ACTIVE RECURRENCE | Two current RBI events reached terminal quarantine; fingerprints, cost, tombstones and downstream exclusion were preserved. |
| `4a65e821-504b-45be-8b78-cf75c401a4ff` | `LLM_SCHEMA_FAILURE_SPIKE` | OPEN | OPEN — ACTIVE RECURRENCE | Current frozen path produced 8 validation failures in 20 attempts (40%) against a 5% threshold. Transport had zero failures. |
| `0472a14f-f01f-482f-8737-0ee2ca4eaa43` | `SOURCE_COLLECTION_FAILURE` | OPEN | RESOLVED | The historical RBI `ReadError` recovered on the next soak cycle. Recovery added three scheduled RBI successes with zero failures and no observed data loss. |

Containment remains effective: unsupported numeric claims do not enter the success cache, terminal
invalid results create tombstones, and quarantined results remain excluded from specialist/Fusion
handoff. This containment is not a reason to call semantic health healthy.

Current transport is `HEALTHY`; current-policy semantic validation is `INSUFFICIENT_SAMPLE`. Three current HIGH
incidents remain open: two `LLM_HALLUCINATION_QUARANTINE` incidents and one
`LLM_SCHEMA_FAILURE_SPIKE`. RBI and SEBI collection are current after three scheduled cycles each.
Forward Paper remains `DISABLED`.

The numeric-grounding root cause was repaired without weakening quarantine: HTML
attributes/scripts/styles are no longer evidence, harmless numeric formatting is normalized with
`Decimal`, and signs plus bounded units remain mandatory. A subsequent 10-attempt production-path
window under `event-grounding-v2` had no validation failures, but inspection exposed a separate
schema defect: `event_type` was an unrestricted string and accepted values outside the declared
taxonomy. Those attempts remain immutable evidence but do not qualify the final semantic window.

The frozen replacement is `event-grounding-v3-taxonomy` with schema
`llm-analysis-result-v2-taxonomy` and grounding policy `visible-text-signed-decimal-v2`. Policy
identity now includes the closed event taxonomy; prior terminal results are boundedly re-evaluated
when that identity changes, while an unchanged successful policy is not repeatedly billed. Events
deferred by the daily budget return to the pending queue on a later eligible cycle. One bounded v3
canary passed transport and structured/grounding validation at an estimated cost of `$0.0004614`.
The historical ledger contains 42 attempts and 8 validation failures. Current health requires 40
non-canary operational attempts under the exact v3 identity before it can report semantic health as
healthy or resolve the incidents. The v3 operational sample is 0/40.

The incidents remain open. One canary is not the representative frozen window required by their
closure criteria; the platform-owned hourly semantic job will provide the next bounded production
path evidence.

Decision: **INTELLIGENCE OPERATIONS RECOVERY NEEDS WORK**.
