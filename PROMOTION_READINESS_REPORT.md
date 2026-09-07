# Promotion Readiness Report

Status date: 2026-09-08  
Decision: **BLOCKED**

## Current evidence

- A public homepage, coherent public navigation, methodology, data-source, validation, About, FAQ, draft Risk, draft Privacy, draft Terms, and draft Contact surfaces now exist.
- Anonymous access to internal research/admin routes and `/api/research-desk` returns `401` with `noindex`, `nofollow`, `noarchive`, and `no-store` controls.
- Public delivery policy tests reject stale data, fixture/live mixing, internal research, unapproved rights, and live predictive output without predictive validation.
- Unknown stock symbols return a real `404` rather than a plausible RELIANCE fixture.
- The production Next build, frontend typecheck, lint, and release-policy tests pass.
- Chrome desktop review confirms the homepage and methodology render without a framework error surface. The homepage preserves the established Evidence Lens visual system.
- Chrome screenshot review now covers the homepage at all seven required desktop, tablet, and
  mobile viewports. A detected 1280px overflow and undersized mobile navigation/link targets
  were repaired; the 98-combination public route/viewport matrix passes overflow, content, H1,
  and framework-overlay checks.
- Synthetic demo routes now emit `noindex, nofollow`; the sitemap is limited to approved
  informational routes and supports validated explicit or Vercel production origins.
- Keyboard-first skip navigation and automated structural accessibility checks now pass across
  all 14 public routes; local optimized-build response and bundle baselines are recorded in
  `PUBLIC_PRODUCT_QA.md`.
- Reproducible GitHub CI now runs pinned backend, frontend, repository-safety, dependency-audit,
  environment-contract, production-build, and smoke gates. Hosted runs through the backup-tooling
  commit passed; the current worker-heartbeat commit is awaiting its hosted result.
- Local SQLite backup/restore integrity checks and a real intelligence-worker
  start/heartbeat/graceful-stop rehearsal pass. These do not substitute for managed production
  storage, retention, host supervision, or deployed recovery evidence.

## Still required

- Legal/compliance approval of all perimeter and policy language.
- Public data-rights approval or proof that the launched payload contains only independently safe data.
- Authenticated-route review in staging with production-shaped secrets and logs.
- Manual screen-reader, contrast, Windows forced-colors, and 200%/400% zoom checks across the
  full interactive public route inventory.
- Clean-browser console/network audit and production performance measurements. The Chrome QA
  profile reported extension message-channel errors that are not attributable to an application
  source, so the console gate remains open pending a clean profile run.
- Canonical domain, canonical metadata, real sitemap, Search Console decision, staging/production smoke evidence, and rollback proof.
- Production host supervision, notification destinations, managed backup/retention policy, and a
  production-shaped worker soak/restart record.
- Approved claims ledger and promotion package: launch screenshots, short/long descriptions, founder notes, launch copy, and walkthrough script.
- Owner approval of demo forecast discoverability and analytics/privacy choices.

## Claims boundary

Approved current factual state: `HOLDOUT VALIDATED — FORWARD REQUIRED`. Do not publish BUY/SELL calls, target prices, return probabilities, “verified edge,” customer confidence scores, or performance claims.

## Gate

### PROMOTION NOT READY
