from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def workflow() -> str:
    return (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")


def deployment_smoke() -> str:
    return (ROOT / "apps" / "web" / "scripts" / "deployment-smoke.mjs").read_text(
        encoding="utf-8"
    )


def test_release_workflow_is_manual_and_disables_concurrent_promotions() -> None:
    text = workflow()
    assert "workflow_dispatch:" in text
    assert "group: production-release" in text
    assert "cancel-in-progress: false" in text
    assert "push:" not in text


def test_release_workflow_requires_exact_hosted_quality_checks() -> None:
    text = workflow()
    assert 'test "${GITHUB_REF}" = "refs/heads/main"' in text
    for check in ("backend", "web", "repository-safety"):
        assert check in text
    assert "check-runs" in text
    assert "grep -qx \"success\"" in text


def test_release_workflow_stages_without_domain_then_promotes_same_output() -> None:
    text = workflow()
    assert "deploy --prebuilt --prod --skip-domain" in text
    assert "deployment_url: ${{ steps.deploy.outputs.url }}" in text
    assert "STAGED_DEPLOYMENT_URL: ${{ needs.stage-production-build.outputs.deployment_url }}" in text
    assert 'promote "${STAGED_DEPLOYMENT_URL}" --yes' in text
    assert "workflow_dispatch:" in text
    assert "deployment_url:" not in text.split("jobs:", 1)[0]


def test_staged_build_receives_the_validated_canonical_origin() -> None:
    text = workflow()
    staging = text[text.index("stage-production-build:") : text.index("authorize-production:")]
    assert "VERIFIED_EDGE_CANONICAL_URL: ${{ vars.VERIFIED_EDGE_CANONICAL_URL }}" in staging
    assert "NEXT_PUBLIC_SITE_URL: ${{ vars.VERIFIED_EDGE_CANONICAL_URL }}" in staging
    assert 'test "${NEXT_PUBLIC_SITE_URL}" = "${VERIFIED_EDGE_CANONICAL_URL}"' in staging
    assert 'case "${NEXT_PUBLIC_SITE_URL}" in' in staging
    assert "https://*)" in staging


def test_staged_build_validates_pulled_server_environment_without_retaining_it() -> None:
    text = workflow()
    staging = text[text.index("stage-production-build:") : text.index("authorize-production:")]
    assert " env pull " in staging
    assert '--dotenv-file "${release_env}"' in staging
    assert "--profile public-web --stage production" in staging
    assert "trap 'rm -f \"${release_env}\"' EXIT" in staging
    validation = staging.index("Validate pulled public-web environment")
    build = staging.index("Build production artifact")
    assert validation < build


def test_release_workflow_uses_lockfile_installed_vercel_cli() -> None:
    text = workflow()
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert package["devDependencies"]["vercel"] == "59.11.7"
    assert "pnpm dlx vercel" not in text
    assert text.count("pnpm exec vercel") >= 6


def test_deployment_smoke_uses_header_only_protection_bypass() -> None:
    text = deployment_smoke()
    assert '"x-vercel-protection-bypass": bypass' in text
    assert '"x-vercel-set-bypass-cookie"' not in text
    assert "?x-vercel-protection-bypass" not in text
    assert "redirect: \"manual\"" in text
    assert "bypass," not in text[text.index("console.log") :]


def test_failed_production_smoke_attempts_rollback_and_rejects_release() -> None:
    text = workflow()
    promotion = text[text.index("promote-production:") :]
    smoke = promotion.index("id: production_smoke")
    rollback = promotion.index("vercel rollback --yes --timeout=3m")
    status = promotion.index("vercel rollback status --timeout=3m")
    rejection = promotion.index("Fail release after rollback attempt")
    assert smoke < rollback < status < rejection
    assert "continue-on-error: true" in promotion
    assert "if: steps.production_smoke.outcome == 'failure'" in promotion
    assert "if: always() && steps.production_smoke.outcome == 'failure'" in promotion


def test_release_workflow_fails_closed_before_production_approval() -> None:
    text = workflow()
    authorization = text.index("authorize-production:")
    promotion = text.index("promote-production:")
    assert authorization < promotion
    assert "--require-track public_platform" in text[authorization:promotion]
    assert "environment: production" in text[promotion:]
    assert "deployment:smoke" in text
