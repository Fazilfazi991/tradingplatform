# Psychology and Sentiment Intelligence Architecture

Status: **ENGINEERING / READY**. This is internal evidence, not prediction.

```text
point-in-time event/news evidence
  -> evidence-bound sentiment observation
  -> cluster-first duplicate suppression
  -> quality/novelty/relevance/confirmation aggregation
  -> attention + narratives + disagreement + fear/euphoria/crowding/speculation
  -> entity / sector / market psychology snapshot
  -> PsychologyEvidenceEngine (may abstain; never predicts returns)
```

Source records remain immutable for provenance, while clusters receive at most one independent vote.
Snapshots enforce `available_at <= cutoff` and carry deterministic hashes. Entity, sector and market
states use the same typed dimensions but remain separate aggregations; sector breadth cannot be replaced
by one mega-cap without an explicit future methodology.

Pre-market processing is scheduled for 08:50 IST after macro, and EOD processing for 16:25 after event
and macro processing. Current handlers expose internal contracts only; no social source is active.
