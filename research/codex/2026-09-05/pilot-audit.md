# Batch 12.1 live research pilot audit

Audit timestamp: 2026-09-05 (Asia/Kolkata operating calendar)

## Activation

- Feature flag: enabled only in the ignored local internal environment
- Runtime authority: `RESEARCH_CANDIDATE_ONLY`
- Research mode: `ENGINEERING_FIXTURE`
- Intelligence runtime: `INTERNAL_LIVE`
- Automation: `verified-edge-hourly-differential-research`
- Effective research window: hourly, weekdays, 09:00–18:59 Asia/Kolkata
- Other research routines: paused / not created

The scheduler triggers hourly on weekdays. Its saved operating policy performs a no-op outside the configured Asia/Kolkata research window. The manual canary is not counted as a scheduled run.

## Manual canary

- Runs: 1 succeeded, 0 failed
- Queries: 4
- Official domains checked: 4
- Pages examined: 4
- Potential developments examined: 2
- Candidates persisted: 1
- Duplicates suppressed: 1
- Primary-source attempts: 1
- Primary sources found: 1
- Contradictions: 0
- Source discoveries: 0
- Research incidents: 0

The candidate is an `UPDATE` tied to an existing canonical SEBI RSS event. The direct SEBI page confirmed the publication date and press-release number. It remains `PRIMARY_SOURCE_FOUND`, uses `TITLE_METADATA_ONLY`, and has not entered the evidence pipeline.

## Candidate quality

| Candidate | Classification | Reason |
| --- | --- | --- |
| `b0abb239-543b-4bb8-8c1b-5988ef1a4134` | `NEEDS_REVIEW` | Correct entity, timestamp, official source, and overlap link; low materiality and limited incremental information. |

- Useful rate: not established from one canary candidate
- Low-value rate: not established from one canary candidate
- Duplicate suppression: observed successfully
- Incorrect candidates: 0 observed
- Primary-source verification rate: 100% of attempted canary candidates
- Zero-candidate scheduled-run rate: unavailable until scheduled runs execute

## Boundaries and security

- Prediction/trading leakage: 0
- Direct evidence promotion: 0
- Fusion changes caused by raw candidates: 0
- Source activation: 0
- Automated code changes by scheduled policy: prohibited
- API keys, cookies, authorization headers, session values, GitHub tokens, and private environment values in committed research artifacts: 0 detected
- Website instructions are explicitly treated as untrusted content

## Scheduled pilot state

Completed genuine scheduled runs: 0. The audit date is a Saturday, outside the configured weekday window. The minimum three genuine hourly runs remain outstanding and must not be replaced by immediate manual executions.

## Expansion recommendation

- Premarket: `KEEP_PAUSED`
- EOD: `KEEP_PAUSED`
- Operations audit: `KEEP_PAUSED`
- Saturday deep research: `KEEP_PAUSED`
- Sunday pre-week: `KEEP_PAUSED`

Reassess only after at least three genuine scheduled hourly runs provide measurable novelty, noise, primary-source, and zero-candidate rates.

## Decision

### CODEX LIVE RESEARCH PILOT NEEDS WORK

Reason: activation, canary, persistence, UI, and boundaries are operational, but the mandatory minimum of three genuine scheduled hourly runs has not yet occurred.
