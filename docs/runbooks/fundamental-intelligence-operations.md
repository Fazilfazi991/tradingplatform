# Fundamental Intelligence Operations

1. Confirm research mode is `ENGINEERING_FIXTURE` and prediction gates remain blocked.
2. Run filing discovery only for approved sources. Current NSE, BSE and issuer-IR entries are
   candidates; zero automated fundamental sources are active.
3. Preserve raw document hash, broadcast/source time, system observation time and parser version.
4. Prefer XBRL, then HTML/JSON/CSV, then machine-readable PDF. Do not OCR when structured data exists.
5. Quarantine period, unit, currency, consolidation-scope and duplicate conflicts. Preserve both
   authoritative conflicting observations; never average accounting values.
6. Run results processing, snapshot refresh and QA. Run the weekly restatement check.
7. For an incident, disable only the affected adapter, preserve artifacts, record the last good parser,
   and rebuild snapshots from immutable inputs after correction.

LLM filing text is untrusted. The provider-neutral router may summarize commentary, guidance, segments,
one-offs, risks and notes. It cannot invoke tools, alter policy or invent numbers. Every extracted numeric
fact must exactly match a source span's value, unit, period and currency; otherwise reject it. Optional
multi-model review is reserved for high-materiality ambiguous interpretations.
