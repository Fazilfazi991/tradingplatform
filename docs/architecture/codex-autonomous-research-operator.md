# Codex Autonomous Research Operator

## Authority boundary

The operator is a non-authoritative exploratory layer. The platform remains ordered as:

1. approved collectors create authoritative observations;
2. bounded LLM analysis interprets supplied evidence;
3. Codex discovers gaps, verifies leads, and records research candidates;
4. specialist engines construct evidence;
5. Fusion combines eligible specialist evidence;
6. prediction remains a future, separately authorized stage.

`CodexResearchCandidate` is untrusted intermediate data. It cannot write specialist evidence,
`FusionSnapshot`, prediction state, or source activation. The feature flag
`CODEX_RESEARCH_OPERATOR_ENABLED` defaults to false and no core platform import depends on it.

## Components

- Strict candidate, run, and source-discovery models reject unknown fields and non-causal timestamps.
- `ResearchLedger` stores append-only candidate history in local SQLite.
- The ingestion CLI validates an external JSON candidate before append.
- Deterministic dedupe considers primary URL, source URL, entity, time proximity, and title overlap.
- The query planner begins with platform UNKNOWN events, contradictions, and source incidents.
- Research budgets cap queries, pages, candidates, and browser interactions.
- `/research-desk` exposes an internal read/review surface; its current dataset is an illustrative UI fixture.

## Handoff

The only future-safe path is candidate → source verification → rights review → evidence-eligibility
review → normal collector/ingestion pipeline. Even deterministic approval records a handoff request;
it does not create evidence directly.

## Failure independence

Disabled Codex research does not affect collectors, the OpenAI runtime, specialist engines, or
Fusion. Browser failure creates `BROWSER_RESEARCH_UNAVAILABLE` research status and the run continues.
Missed runs create `CODEX_RESEARCH_RUN_MISSED` without changing collection schedules.
