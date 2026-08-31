# DR-019 — Codex Autonomous Research

## Decision

Codex is a non-authoritative exploratory research and operations layer. Discoveries are research
candidates, not prediction evidence. Platform operation must not depend on Codex availability.

Codex cannot promote evidence, modify prediction state, write Fusion, or bypass source-rights
controls. Scheduled research may search broadly within bounded budgets, but findings must pass
through schema validation, source verification, deduplication, rights review, causal timestamps, and
the standard evidence pipeline.

Scheduled repair is limited to a clearly broken parser or deterministic selector for an already
approved source with an unchanged contract. Repairs use a dedicated branch, tests, and
`PREPARE_FIX_ONLY`; no scheduled task auto-merges into `main`.

## Consequences

The operator improves discovery, contradiction investigation, source maintenance, and visibility of
gaps without becoming a hidden evidence source. It may miss events or remain disabled while the core
platform continues normally. New source activation and semantic methodology changes require review.
