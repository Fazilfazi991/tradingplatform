# Engine Dependency Policy

Dependencies are independent, partially overlapping, highly overlapping, derived-from or unknown.
Shared source IDs, event IDs, cluster IDs and feature/data families are explicit.

News/psychology may share story clusters; macro/news may share an RBI release; psychology/positioning may
share crowding; technical/historical may share price features. Highly overlapping evidence receives a
0.35 independence factor, partial overlap 0.65 and derived evidence 0.20. These are conservative V0
deduplication factors, not predictive weights.

Exact statistical independence is never claimed. Dependency penalties and shared provenance remain in
the sealed fusion snapshot and explanation.
