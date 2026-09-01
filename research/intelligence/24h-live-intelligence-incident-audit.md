# 24-Hour Live Intelligence Incident Audit

## Decision

**24H LIVE INTELLIGENCE SOAK NEEDS WORK**

The worker completed the full 86,401.48-second window and all invalid outputs were stopped before evidence, snapshots, or Fusion. The run nevertheless cannot pass because rejected provider responses were not retained with validation detail, tokens, or cost. The reported `$0.2107464` is therefore a lower bound rather than a reconciled total.

## Invented-number quarantine

- Incident: `9cf5baf4-5f67-4214-addd-e7ecd9aa2d12`
- Event lineage hash: `5cd6a3bb759ef9ac0e1b651ee08f23a32da92de5acf21570afee0cdb1ae61569`
- Source/task: RBI / event classification
- Prompt: `event-intelligence-v1-soak-v1`
- Guard: numeric values in the structured summary were compared with the supplied title and official RSS summary; a difference raised `INVENTED_NUMBER_QUARANTINED` before `cache_put`.
- Cache trace: no rejected payload, validation marker, or error body appears in `llm_cache`.
- Downstream trace: the database contains canonical raw information events but no evidence, specialist-snapshot, Fusion-input, FusionSnapshot, or Research Desk tables. Generated snapshots and Fusion attempts are both zero.
- Result: `QUARANTINED_BEFORE_EVIDENCE`.

The precise invented value cannot be reported because the runtime discarded the rejected response. Later successful analyses for the same canonical event are independently cached under later artifact hashes and contain source-supported numbers; they are not the rejected response.

## Schema failures

The 76 rows are failed provider attempts, not 76 distinct information failures:

- RBI: 71 attempts
- SEBI: 5 attempts
- Distinct affected canonical events: 10
- Recovered events: 8
- Permanently uninterpreted events: 2
- Recorded category: `OTHER_VALUE_ERROR`

The two permanent failures were the RBI Executive Director appointment and the September 2 overnight VRRR announcement. The ledger does not preserve exception messages, retry ordinal, materiality, refusal state, or rejected structured output, so a more specific breakdown would be invented.

## Provider warning

No HTTP, authentication, rate-limit, timeout, or server error is present in the provider ledger. `LLM_PROVIDER_DOWN` was a false positive: the threshold counted cumulative `ValueError` validation rows instead of consecutive provider transport failures. Collection continued throughout the warning.

## SEBI timeout

One SEBI attempt scheduled for `2026-08-31T15:01:20.146318Z` returned `ConnectTimeout`. The next scheduled attempt at `15:16:21.640815Z` succeeded and saw all 30 feed records. No event loss or scheduler gap is visible. The report's zero source failures is a reporting defect: it counted durable execution status (`SUCCEEDED`) rather than the handler result (`FAILED`).

## Scheduler and continuity

All 261 durable executions completed. RBI and SEBI each ran 96 times; each had a maximum start gap of about 905 seconds and no run was more than 5.05 seconds late. The three hourly jobs each ran 23 times with no run more than 4.96 seconds late. There was one contained SEBI handler failure and no silent material interval.

## Required repair

Before another qualifying soak, retain sanitized rejected-response hashes, validation category/message, attempt ordinal, input/output tokens, actual cost, and explicit terminal disposition. Separate provider-transport health from schema validation, count handler failures correctly, and exclude invalid results with a cache tombstone or equivalent auditable lineage marker.
