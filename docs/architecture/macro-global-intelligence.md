# Macro and global market intelligence

The macro pipeline is `official release/event → causal observation/vintage → category state →
cross-market state → multi-axis regime → sector exposure → evidence output → pre-market/EOD
snapshot`. It describes information available at a cutoff and does not forecast stock returns.

Original releases and revisions are immutable separate values with distinct availability times.
Snapshots select only observations known by the system at the cutoff. Global price contracts remain
fixture-backed until an approved or licensed source is configured.

The existing provider-neutral LLM router supports RBI interpretation, macro explanations,
policy summaries, contradiction analysis and sector-exposure explanations. Provider attempts,
fallbacks, latency, cost configuration, cache state and consensus remain explicit. Deterministic
fallback works without credentials.
