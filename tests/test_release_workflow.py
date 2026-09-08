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


def test_protected_staging_requires_automation_bypass_secret() -> None:
    text = workflow()
    staging = text[text.index("stage-production-build:") : text.index("authorize-production:")]
    assert "VERCEL_AUTOMATION_BYPASS_SECRET: ${{ secrets.VERCEL_AUTOMATION_BYPASS_SECRET }}" in staging
    assert 'test -n "${VERCEL_AUTOMATION_BYPASS_SECRET}"' in staging


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
    browser_smoke = promotion.index("id: production_browser_smoke")
    evidence = promotion.index("id: deployment_evidence")
    upload = promotion.index("id: upload_evidence")
    rollback = promotion.index("vercel rollback --yes --timeout=3m")
    status = promotion.index("vercel rollback status --timeout=3m")
    rejection = promotion.index("Fail release after rollback attempt")
    assert smoke < browser_smoke < evidence < upload < rollback < status < rejection
    assert promotion.count("continue-on-error: true") == 4
    for step in (
        "production_smoke",
        "production_browser_smoke",
        "deployment_evidence",
        "upload_evidence",
    ):
        assert f"steps.{step}.outcome == 'failure'" in promotion


def test_release_workflow_fails_closed_before_production_approval() -> None:
    text = workflow()
    authorization = text.index("authorize-production:")
    promotion = text.index("promote-production:")
    assert authorization < promotion
    assert "--require-track public_platform" in text[authorization:promotion]
    assert "environment: production" in text[promotion:]
    assert "deployment:smoke" in text


def test_release_workflow_requires_rollback_evidence_before_staging() -> None:
    text = workflow()
    authorization = text[text.index("authorize-staging:") : text.index("stage-production-build:")]
    assert "rollback_deployment_id:" in text.split("jobs:", 1)[0]
    assert "rollback_rehearsed:" in text.split("jobs:", 1)[0]
    assert "ROLLBACK_DEPLOYMENT_ID: ${{ inputs.rollback_deployment_id }}" in authorization
    assert "ROLLBACK_REHEARSED: ${{ inputs.rollback_rehearsed }}" in authorization
    assert 'test "${ROLLBACK_REHEARSED}" = "true"' in authorization
    assert 'test -n "${ROLLBACK_DEPLOYMENT_ID}"' in authorization
    assert '${{ inputs.rollback_deployment_id }}" \\' not in text


def test_successful_promotion_uploads_validated_sealed_evidence() -> None:
    promotion = workflow()[workflow().index("promote-production:") :]
    smoke = promotion.index("id: production_smoke")
    browser_smoke = promotion.index("id: production_browser_smoke")
    create = promotion.index("python -m scripts.create_deployment_evidence")
    validate = promotion.index("scripts/validate_deployment_evidence.py")
    upload = promotion.index("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02")
    rollback = promotion.index("Roll back failed production release")
    assert smoke < browser_smoke < create < validate < upload < rollback
    assert "VISUAL_QA_BASE_URL: ${{ vars.VERIFIED_EDGE_CANONICAL_URL }}" in promotion
    assert "deployment-evidence-${{ github.sha }}" in promotion
    assert "retention-days: 90" in promotion
