# Macro intelligence operations

Scheduled internal jobs use Asia/Kolkata:

- macro release processing: hourly
- pre-market snapshot: 08:45
- EOD macro snapshot: 16:20
- macro QA: 17:05

Run RBI metadata validation with:

```powershell
.venv\Scripts\python.exe scripts\validate_live_macro_intelligence.py
```

Numeric observations remain fixture-backed until a source-specific adapter passes terms, vintage,
unit, release-time and revision validation. Review staleness, revisions, source mismatches, unit
errors, snapshot completeness and LLM failures. Outputs are internal and labelled not prediction.
