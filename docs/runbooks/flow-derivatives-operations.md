# Flow and Derivatives Operations

1. Verify research mode is `ENGINEERING_FIXTURE` and all customer/prediction gates remain blocked.
2. Ingest only approved reports and record represented period, publication time and system time.
3. Resolve exchange contract/expiry calendars before parsing; quarantine unknown or adjusted contracts.
4. Build pre-market state at 08:55 IST from prior available data only. EOD ingestion begins after 18:15.
5. Audit freshness, chain and strike completeness, expiry coverage, spreads, IV, participants, timestamp
   mismatches, source conflicts and abstention.
6. Disable a faulty adapter and rebuild from immutable artifacts; never patch values with LLM output.

LLMs may explain contradictions or summarize already calculated state. OI, PCR, IV, Greeks, basis and
flow totals are deterministic only.
