# Intelligence acquisition network

`services/intelligence-core` is a causal, fixture-first acquisition service. Scheduled workers—not
Codex—discover approved URIs, fetch bounded artifacts, preserve hashes, parse source records, normalize
append-only events, resolve anchored entities, cluster repeated stories, monitor health, and build
immutable `available_at <= cutoff` snapshots.

The flow is source registry → collection policy → scheduler/runner → raw artifact → normalized event →
entity match → cluster/novelty → health gate → causal snapshot. Reliability, event confidence,
predictive importance, and validated predictive value remain separate. Ambiguous entities and failing
sources cannot enter canonical intelligence. Weak snapshots abstain as `INSUFFICIENT_INTELLIGENCE`.

Local scheduling is an in-process abstraction for development. Production should run the same
idempotent jobs in persistent workers with PostgreSQL job leasing, durable object storage, metrics,
and incident routing. Vercel/request handlers and interactive Codex sessions are not collectors.

Raw and canonical history is append-only. Parser replay creates new derived versions; corrections and
retractions link to earlier events rather than rewriting them. This preserves what the system knew at
every historical cutoff.
