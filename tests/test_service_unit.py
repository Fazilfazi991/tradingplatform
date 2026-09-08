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


def test_windows_worker_task_has_supervision_and_independent_health_monitor():
    installer = Path("scripts/install_intelligence_worker_task.ps1").read_text(encoding="utf-8")
    runner = Path("scripts/run_intelligence_worker_supervised.ps1").read_text(encoding="utf-8")
    for marker in (
        "New-ScheduledTaskAction",
        "New-ScheduledTaskTrigger -AtLogOn",
        "-RestartCount 5",
        "-MultipleInstances IgnoreNew",
        '$monitorName = "$TaskName-HealthMonitor"',
    ):
        assert marker in installer
    assert "LLM_RUNTIME_ENABLED" in runner
    assert "OPENAI_API_KEY=" not in runner
    assert "OPENAI_API_KEY=" not in installer
