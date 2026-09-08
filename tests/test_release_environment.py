from scripts.verify_release_environment import validate_environment


def test_production_public_web_reports_names_without_values():
    secret = "never-print-this-secret"
    report = validate_environment(
        {
            "NEXT_PUBLIC_SITE_URL": "https://verified.example",
            "VERIFIED_EDGE_INTERNAL_USERNAME": "operator",
            "VERIFIED_EDGE_INTERNAL_PASSWORD": secret,
        },
        profile="public-web",
        stage="production",
    )
    assert report["status"] == "PASS"
    assert secret not in str(report)
    assert report["values_disclosed"] is False


def test_production_profiles_fail_closed_when_required_values_are_absent():
    report = validate_environment({}, profile="intelligence-worker", stage="production")
    assert report["status"] == "FAIL"
    assert "OPENAI_API_KEY:MISSING" in report["errors"]
    assert "UPSTOX_ANALYTICS_TOKEN:MISSING" in report["errors"]
    assert "LLM_RUNTIME_ENABLED:MUST_BE_TRUE" in report["errors"]


def test_public_secret_names_and_insecure_origins_are_rejected():
    report = validate_environment(
        {
            "NEXT_PUBLIC_SITE_URL": "http://127.0.0.1:3000",
            "NEXT_PUBLIC_OPENAI_API_KEY": "redacted",
            "VERIFIED_EDGE_INTERNAL_USERNAME": "operator",
            "VERIFIED_EDGE_INTERNAL_PASSWORD": "redacted",
        },
        profile="public-web",
        stage="production",
    )
    assert report["status"] == "FAIL"
    assert "NEXT_PUBLIC_SITE_URL:LOCALHOST_NOT_ALLOWED" in report["errors"]
    assert "NEXT_PUBLIC_OPENAI_API_KEY:PUBLIC_SECRET_NAME" in report["errors"]
