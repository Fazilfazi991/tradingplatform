# Deployment and rollback runbook

Verified Edge is a mixed Python/Next repository. The public web deployment must use the root `vercel.json`; provider auto-detection is not an acceptable deployment contract.

## Environments

- Local: synthetic/demo public routes; internal routes remain disabled unless local credentials are deliberately configured.
- Staging: separate project/domain, non-production credentials, internal routes protected, robots noindex until acceptance.
- Production: canonical domain, least-privilege server-only secrets, approved public content only.

Never prefix provider, database, or internal-access credentials with `NEXT_PUBLIC_`.

## Pre-deploy

1. Confirm the intended commit and a clean working tree.
2. Require green repository CI.
3. Validate all required environment variable names without printing values.
   Run `python scripts/verify_release_environment.py --profile public-web --stage staging`
   (or `production`). Validate worker profiles separately; the command reports presence only.
4. Confirm `CODEX_RESEARCH_OPERATOR_ENABLED=false` unless the authenticated internal runtime is deliberately configured.
5. Confirm public serializers reject internal, stale, mixed, and rights-unapproved records.
6. Record the previous production deployment identifier for rollback.

## Staging verification

Verify the exact built commit over HTTPS:

- `/`, `/fusion`, `/models`, and demo journeys load without console/network errors.
- Unknown stock symbols return 404.
- Internal routes and `/api/research-desk` return 401 anonymously and include `noindex`/`no-store` controls after authorization.
- Security headers are present.
- No public response contains internal hashes, paths, live raw provider data, credentials, or research candidates.
- Robots, sitemap, canonical metadata, 404, loading, and error states match the release report.

## Production promotion

Promote the already-verified immutable staging build. Do not rebuild from a different commit. Run the production smoke suite and record timestamp, commit, deployment ID, domain, operator, result, and rollback target.

Seal the evidence as `deployment-evidence-v1` and validate it with:

```powershell
.\.venv\Scripts\python.exe scripts\validate_deployment_evidence.py --file <evidence.json>
```

The contract requires an HTTPS non-local origin, full commit SHA, distinct rollback deployment,
timezone-aware timestamp, environment validation, public/internal and payload boundaries, security
headers, canonical/indexing checks, unknown-stock 404, clean console/network evidence, and a passed
rollback rehearsal. It rejects incomplete checks and detects post-recording modification. Store no
credentials, response bodies, raw provider data, or internal research payloads in this artifact.

## Rollback

Rollback when the public/internal boundary, content rights, data provenance, major routes, security headers, or availability checks fail. Promote the recorded previous healthy deployment, rerun smoke checks, open an incident, and preserve failed-deployment logs. Application rollback must never rewrite append-only research or forward-paper records.

## Data and state

Local SQLite files and runtime databases are never deployment artifacts. Production-owned state requires documented backup, retention, restore, and migration procedures before the operations gate can pass.
