# Current Intelligence Incident Review

Updated at 2026-09-08T09:49:09Z from the supervised post-soak runtime. The historical
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

`event-grounding-v3-taxonomy` closed the schema taxonomy. Its first scheduled production batch
completed 10/10 automated validations with zero transport failures at `$0.0053848` (12,794 input and
2,355 output tokens). Mandatory review of its only HIGH-materiality result found an unsupported
logical strengthening: the Nasik cooperative-bank source said an extension should not be construed
to imply RBI satisfaction with the bank's financial position, while the accepted summary asserted
that the position had not been deemed satisfactory. The result fingerprint is
`f79c9e19afc7e16f5635a01ec6bd858ba9211eef778e782a7be6561244736f4e`; its disposition recorded
`NOT_HANDED_OFF`, and no specialist or Fusion consumer used it. The v3 window is therefore
non-qualifying despite a 0% automated failure rate.

Per the frozen-window rule, v3 was terminated. The replacement is
`event-grounding-v4-logical-modality` with schema `llm-analysis-result-v2-taxonomy` and grounding
policy `visible-text-signed-decimal-inference-v3`. It preserves the closed taxonomy, adds an explicit
logical-modality instruction, deterministically rejects this confirmed non-implication failure as
`EVIDENCE_GROUNDING_FAILURE`, and includes a regression fixture. Current health requires a new 40
non-canary operational-attempt window under the exact v4 identity. The v4 sample is 0/40.

The incidents remain open. Three genuine post-restart scheduled RBI and SEBI cycles have completed
without collection failure, satisfying the collection-observation gate, but semantic closure now
requires the new v4 canary and representative platform-owned window.

Decision: **INTELLIGENCE OPERATIONS RECOVERY NEEDS WORK**.
