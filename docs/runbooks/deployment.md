# Deployment and rollback runbook

Verified Edge is a mixed Python/Next repository. The public web deployment must use the root `vercel.json`; provider auto-detection is not an acceptable deployment contract.

Automatic Vercel Git deployments are disabled in `vercel.json`. This is deliberate: a push to
`main` is a tested repository update, not production authorization. The manual `staged release`
workflow may create a domainless production-shaped candidate only after the exact commit's hosted
quality checks pass. Promotion remains impossible unless the public-platform track subsequently
passes and the protected `production` environment is approved.

## Environments

- Local: synthetic/demo public routes; internal routes remain disabled unless local credentials are deliberately configured.
- Staging: separate project/domain, non-production credentials, internal routes protected, robots noindex until acceptance.
- Production: canonical domain, least-privilege server-only secrets, approved public content only.

Never prefix provider, database, or internal-access credentials with `NEXT_PUBLIC_`.

## Pre-deploy

1. Confirm the intended commit and a clean working tree.
2. Require green repository CI.
3. Require an explicit fail-closed Track A authorization:
   `python scripts/audit_release_gates.py --require-track public_platform`.
   Exit code `3` means the release remains blocked; do not deploy or override it.
4. Validate all required environment variable names without printing values.
   Run `python scripts/verify_release_environment.py --profile public-web --stage staging`
   (or `production`). Validate worker profiles separately; the command reports presence only.
   The intelligence-worker profile requires both the OpenAI semantic runtime and the read-only
   `UPSTOX_ANALYTICS_TOKEN`, because provider health is a mandatory scheduled canary even while
   EOD collection remains disabled.
5. Confirm `CODEX_RESEARCH_OPERATOR_ENABLED=false` unless the authenticated internal runtime is deliberately configured.
6. Confirm public serializers reject internal, stale, mixed, and rights-unapproved records.
7. Record the previous production deployment identifier for rollback.

## GitHub release environments

Configure two protected GitHub environments; do not store their values in the repository:

- `production-staging`: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, required
  `VERCEL_AUTOMATION_BYPASS_SECRET`, and `VERIFIED_EDGE_CANONICAL_URL` as a non-secret variable.
- `production`: the same scoped Vercel identifiers and canonical URL, with required owner/reviewer
  approval and no self-approval.

The staging job maps the approved `VERIFIED_EDGE_CANONICAL_URL` to the web build's
`NEXT_PUBLIC_SITE_URL`. This is intentional: the release workflow owns the immutable build origin,
and the public Next.js bundle must not depend on an unverified project-level default. The workflow
rejects an empty or non-HTTPS canonical origin before building.

After pulling production project settings, the job also pulls an ephemeral dotenv file and runs the
public-web environment contract against it. The report contains names and presence booleans only;
the file is deleted on step exit and never uploaded. Missing server-side internal-route credentials
therefore stop staging before an artifact is built.

Run `.github/workflows/release.yml` manually from `main`. Supply the previous healthy production
deployment ID and attest that rollback to it has been rehearsed successfully; the workflow rejects
the release before staging when either condition is absent. After linking the approved Vercel project,
it verifies that the exact rollback target is accessible without retaining inspection output. It then
verifies the exact commit's `backend`,
`web`, and `repository-safety` checks, builds with the pinned Vercel CLI, deploys using
`--prod --skip-domain`, and smoke-tests the candidate. The promotion job consumes that workflow
output directly; it cannot accept a caller-supplied deployment URL. It runs only after
`--require-track public_platform` succeeds and then requires the protected production approval.
The workflow must remain red/blocked while the release manifest contains external or failed Track A
gates.

The Vercel CLI is an exact lockfile-installed root development dependency and every release command
uses `pnpm exec vercel`. Do not replace it with a transient `pnpm dlx` install: that command is not
part of the reproducible dependency graph and has failed module resolution under the pinned pnpm
runtime.

## Staging verification

Verify the exact built commit over HTTPS:

- `/`, `/fusion`, `/models`, and demo journeys load without console/network errors.
- Unknown stock symbols return 404.
- Internal routes and `/api/research-desk` return 401 anonymously and include `noindex`/`no-store` controls after authorization.
- Security headers are present.
- No public response contains internal hashes, paths, live raw provider data, credentials, or research candidates.
- Robots, sitemap, canonical metadata, 404, loading, and error states match the release report.

The automated deployment smoke additionally scans rendered HTML and public JavaScript/CSS assets
for forbidden internal markers and local paths, and rejects exposed JavaScript source maps. It is
deployment evidence, not a substitute for the owner/legal/accessibility approvals in the release
manifest.

When Vercel Deployment Protection is enabled, the smoke runner transmits the configured
`VERCEL_AUTOMATION_BYPASS_SECRET` only in the `x-vercel-protection-bypass` request header. For the
protected staging workflow this secret is required and the job fails before build when it is
absent. It never
places the credential in a URL, output, artifact, or bypass cookie. Every request supplies the
header directly, so redirect-based cookie setup is intentionally disabled and an unexpected
protection redirect fails the smoke test.

## Production promotion

Promote the already-verified immutable staging build. Do not rebuild from a different commit. Run
the HTTP boundary suite and browser console/network suite against the canonical origin, then record
timestamp, commit, deployment ID, domain, operator, result, and rollback target. If either canonical
smoke suite, evidence sealing, or evidence upload fails, the workflow requests an immediate Vercel rollback
to the exact recorded healthy deployment,
waits for rollback status, re-runs the canonical HTTP boundary suite, and then rejects the release.
A failed rollback or failed post-rollback smoke also leaves the workflow
red and requires the bad-deployment incident runbook; it must never be treated as a successful
release.

### First-release recovery candidate

When no healthy rollback deployment exists, the owner may manually dispatch the same workflow with
`bootstrap_staging=true`, an empty rollback target, and `rollback_rehearsed=false`. This exceptional
mode still requires exact-commit hosted quality, the protected `production-staging` environment,
complete secret/environment validation, a prebuilt domainless deployment, and the full staged smoke
boundary. It records the candidate in the workflow summary and then stops: production authorization
and promotion are structurally skipped.

After the candidate is independently reviewed, rehearse rollback to it and retain the deployment ID.
Only then may a later normal dispatch use it as the rollback target. Bootstrap mode is not a launch,
does not assign a domain, does not close `EXT-06`, and must never be used to bypass Track A gates.

After canonical smoke passes, the workflow seals the evidence as `deployment-evidence-v1`, validates
it, and uploads `deployment-evidence-<commit SHA>` with 90-day retention. To validate a downloaded
copy manually, run:

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
