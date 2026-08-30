# DR-005: Universe data readiness

Status: Accepted for infrastructure testing; blocked for historical research  
Date: 2026-08-30

## Decision

The current NIFTY 200 list from the official NSE Indices constituent download may be used for
current ingestion and mapping QA only. On 2026-08-30 its 200 symbols mapped exactly to 200 active
NSE equity records in the public Upstox instrument master, with no fuzzy matches or exceptions.

This source is a current snapshot, not effective-dated history. It cannot reconstruct membership
at an earlier decision date. Using it for historical universe research would introduce survivorship
and look-ahead bias.

Infrastructure tests and explicitly single-security research independent of index membership may
proceed once their other gates pass. Historical NIFTY 200 cross-sectional research, universe-based
feature selection, ranking, and performance claims may not proceed.

An acceptable future source must be licensed for the intended use, preserve additions/removals and
effective dates, identify securities by stable exchange identity/ISIN, and be versioned and retained
with provenance. Official effective-dated index files or a licensed index/reference-data vendor are
acceptable candidates after legal and technical validation.

