# DR-009: Intelligence acquisition network

Status: Accepted for fixture and approved internal-source engineering  
Date: 2026-08-30

## Decision

Production intelligence collection is implemented by our workers and services. Codex acts as
research and maintenance automation and must not be the authoritative production collector.

All intelligence is source-registered, entitlement-aware, append-only, causally timestamped,
idempotent, replayable, health-gated, and reconstructable at historical cutoffs. Official structured
access is preferred. Unclear access or retention rights block activation. LLM output is derived and
non-authoritative; unsupported extraction returns `UNKNOWN`.

Codex maintenance roles may discover sources, propose integrations, repair collectors, review QA,
audit classifications, and propose hypotheses. They cannot activate sources, promote models/features,
change validation thresholds or compliance gates, or publish predictions. Feature proposals must pass
proposal → hypothesis → registry → discovery → validation → holdout → forward review.

Research mode remains `ENGINEERING_FIXTURE`; DR-005 through DR-008 remain unchanged.
