from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
REPORT = ROOT / "VERIFIED_EDGE_FINAL_READINESS_REPORT.md"


def report() -> str:
    return REPORT.read_text(encoding="utf-8")


def test_final_report_has_the_complete_acceptance_structure() -> None:
    headings = re.findall(r"^## (\d+)\. (.+)$", report(), flags=re.MULTILINE)
    assert [int(number) for number, _ in headings] == list(range(1, 24))
    assert headings[-1][1] == "FINAL VERDICT"


def test_final_report_preserves_independent_fail_closed_track_states() -> None:
    text = report()
    assert "`PRODUCTION BLOCKED`" in text
    assert "`PROMOTION BLOCKED`" in text
    assert "`HOLDOUT VALIDATED — FORWARD REQUIRED`" in text
    assert "### VERIFIED EDGE RELEASE BLOCKED" in text
    assert "VERIFIED EDGE PRODUCTION & PROMOTION READY" not in text
    assert "PREDICTION FEATURE READY" not in text


def test_final_report_does_not_invent_production_evidence() -> None:
    text = report()
    production_section = text.split("## 1. Production URL", 1)[1].split("## 2.", 1)[0]
    assert "NOT AVAILABLE" in production_section
    assert "No canonical production domain" in production_section
    assert "Deployment smoke workflow: implemented but not executed" in text
