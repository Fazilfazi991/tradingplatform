# Research Desk Operations

The Research Desk is internal and non-authoritative. Reviewers work from New, Verifying, Primary
Source Found, Rights Review, Duplicate, Contradiction, Rejected, Operational Issue, and Source
Discovery states.

Use the ingestion command only with schema-valid JSON:

```powershell
python -m intelligence_core.codex_research ingest candidate.json
```

Unknown fields, invalid URLs, non-causal timestamps, missing provenance, prediction language, and
direct evidence promotion are rejected. Candidate changes append history rather than overwrite it.

Reviewers verify identity, source ownership, primary evidence, rights, duplication, causal time, and
contradictions. Approval means “eligible for the standard ingestion pipeline,” never direct evidence.
Reject or retain ambiguous records with an explicit reason. Do not copy full page content into the
ledger.
