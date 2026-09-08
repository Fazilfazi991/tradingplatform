from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]


def workflow() -> str:
    return (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")


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


def test_release_workflow_fails_closed_before_production_approval() -> None:
    text = workflow()
    authorization = text.index("authorize-production:")
    promotion = text.index("promote-production:")
    assert authorization < promotion
    assert "--require-track public_platform" in text[authorization:promotion]
    assert "environment: production" in text[promotion:]
    assert "deployment:smoke" in text
