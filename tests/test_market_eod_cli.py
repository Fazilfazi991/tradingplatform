import json
import subprocess
import sys


def test_market_eod_status_does_not_create_runtime_state(tmp_path):
    ledger = tmp_path / "eod.sqlite3"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_market_eod.py",
            "--status",
            "--ledger",
            str(ledger),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)
    assert report["execution_operations"] is False
    assert report["status"] == "NOT_STARTED"
    assert report["public_delivery"] == "BLOCKED"
    assert not ledger.exists()


def test_market_eod_run_fails_before_credentials_while_disabled(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_market_eod.py",
            "--run",
            "--ledger",
            str(tmp_path / "eod.sqlite3"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "MARKET_DATA_EOD_DISABLED" in result.stderr
