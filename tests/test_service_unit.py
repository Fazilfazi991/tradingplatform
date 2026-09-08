from pathlib import Path


def test_intelligence_systemd_unit_has_required_supervision_and_hardening():
    unit = Path("infra/systemd/verified-edge-intelligence.service").read_text(encoding="utf-8")
    for directive in (
        "User=verified-edge",
        "EnvironmentFile=/etc/verified-edge/intelligence.env",
        "ExecStartPre=",
        "--profile intelligence-worker --stage production",
        "--state /var/lib/verified-edge/intelligence-operations.sqlite3",
        "--output-root /var/lib/verified-edge/intelligence",
        "Restart=on-failure",
        "StartLimitBurst=5",
        "TimeoutStopSec=30",
        "KillMode=mixed",
        "NoNewPrivileges=true",
        "ProtectSystem=strict",
        "ProtectHome=true",
        "ReadWritePaths=/var/lib/verified-edge",
    ):
        assert directive in unit
    assert "UPSTOX_ANALYTICS_TOKEN=" not in unit
    assert "OPENAI_API_KEY=" not in unit
