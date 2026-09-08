# Current Intelligence Incident Review

Updated at 2026-09-08T07:58:30Z from the supervised post-soak runtime. The historical
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

The root cause was repaired without weakening quarantine: HTML attributes/scripts/styles are no
longer evidence, harmless numeric formatting is normalized with `Decimal`, and signs plus bounded
units remain mandatory. The worker now loads `event-grounding-v2` and
`visible-text-signed-decimal-v2`; both are included in semantic/cache identity. Historical attempts
and tombstones remain unchanged. Offline verification passed 382 backend tests, and one bounded live
canary passed transport and structured/grounding validation at an estimated cost of `$0.000542`.
The health model now retains the legacy 31-attempt/8-failure history separately and requires 40
non-canary attempts under one exact frozen policy identity before it can report current semantic
health as healthy or resolve the incident. The current operational sample is 0/40.

The incidents remain open. One canary is not the representative frozen window required by their
closure criteria; the platform-owned hourly semantic job will provide the next bounded production
path evidence.

Decision: **INTELLIGENCE OPERATIONS RECOVERY NEEDS WORK**.
