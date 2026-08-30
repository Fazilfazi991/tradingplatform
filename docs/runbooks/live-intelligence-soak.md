# Live intelligence soak

The live soak is internal and produces no recommendation. Run the configured scheduler with `INTERNAL_LIVE`, the RBI/SEBI allowlist and a local SQLite operations store. A 24-hour target is configured operationally; never report planned time as completed time.

Record source availability, collection and provider failures, latency, costs, duplicates, unknown rate, entity-resolution outcomes, incidents and snapshot generation. Stop on credential leakage, arbitrary outbound URL use, repeated schema failure, rights-policy uncertainty or budget exhaustion. Budget exhaustion should disable semantic calls while collection and deterministic deduplication continue.

The daily report must state live sources, health, events, canonical events, duplicates, calls, cache hits, cost, unknown rate, entity match rate, material events, contradictions, engine states, Fusion state, missing engines and incidents.

