# Event intelligence operations

The daily `event-intelligence-build` runs at 16:15 Asia/Kolkata before the 16:30 archive. It reads
causally available events, creates deterministic interpretations, and writes an immutable internal
package labelled `NOT PREDICTION`.

Run live validation with:

```powershell
.venv\Scripts\python.exe scripts\validate_live_event_intelligence.py
```

Review unknown classifications, entity ambiguity, high-materiality low-certainty cases,
contradictions, velocity anomalies and processing failures. Reanalysis uses a new analyzer/model
version and appends a ledger record; prior interpretations are never overwritten.

LLM providers remain disabled without explicit credentials and enabled configurations. Duplicate
clusters should be resolved before incurring LLM cost.
