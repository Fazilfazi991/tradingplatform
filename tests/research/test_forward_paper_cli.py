import json
import subprocess
import sys
from pathlib import Path


def test_forward_paper_status_is_disabled_and_publicly_blocked():
    result = subprocess.run(
        [sys.executable, "scripts/run_forward_paper.py", "--status"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == {
        "enabled": False,
        "package_configured": False,
        "public_delivery": "BLOCKED",
        "research_state": "HOLDOUT VALIDATED — FORWARD REQUIRED",
    }


def test_forward_paper_issue_fails_closed_while_disabled(tmp_path: Path):
    batch = tmp_path / "batch.json"
    config = tmp_path / "config.json"
    batch.write_text("[]", encoding="utf-8")
    config.write_text(
        json.dumps(
            {
                "version": "1",
                "enabled": False,
                "public_delivery": "BLOCKED",
                "package_path": None,
                "ledger_path": str(tmp_path / "forward.sqlite3"),
            }
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_forward_paper.py",
            "--config",
            str(config),
            "--issue",
            str(batch),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "FORWARD_PAPER_DISABLED" in result.stderr
    assert not (tmp_path / "forward.sqlite3").exists()
