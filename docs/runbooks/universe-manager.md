# Universe manager runbook

The manager detects listings, symbol/name/ISIN changes, suspensions, delistings, mergers, and index
membership changes. New identities are anchored by ISIN/exchange symbol, assigned an internal ID, and
staged as `DATA_PENDING`.

States are `DISCOVERED`, `IDENTITY_RESOLVED`, `DATA_PENDING`, `QUALITY_PENDING`,
`RESEARCH_ELIGIBLE`, `SUSPENDED`, `DELISTED`, and `BLOCKED`. Automation may stage changes but cannot
assign `RESEARCH_ELIGIBLE`; history, quality, corporate-action, point-in-time membership, and governing
research gates require separate approval. Current NIFTY 200 data remains a current QA snapshot only.
