# DR-010: Autonomous intelligence operations

Status: Accepted for internal operations  
Date: 2026-08-30

## Decision

The intelligence platform runs through persistent platform-owned workers. Codex is permitted to
inspect, research, propose, implement, and test maintenance changes but cannot become the authoritative
data collector or autonomously change production prediction behavior.

The maximum current intelligence mode is `INTERNAL_LIVE`; customer-visible promotion is blocked. RBI
and SEBI official RSS metadata may be collected internally under the approved source policy. No source
content or intelligence is customer-visible. Local SQLite state is temporary until the project
PostgreSQL runtime is available.

Forward collection provenance, system-observed time, incidents, universe staging, deterministic replay,
and immutable daily archives are mandatory. Research mode remains `ENGINEERING_FIXTURE`.
