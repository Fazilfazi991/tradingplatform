from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator
from research_core.common import stable_hash


class ResearchType(StrEnum):
    COMPANY_EVENT = "COMPANY_EVENT"
    SECTOR_EVENT = "SECTOR_EVENT"
    MACRO_EVENT = "MACRO_EVENT"
    REGULATORY_EVENT = "REGULATORY_EVENT"
    GLOBAL_MARKET_EVENT = "GLOBAL_MARKET_EVENT"
    COMMODITY_EVENT = "COMMODITY_EVENT"
    CURRENCY_RATES_EVENT = "CURRENCY_RATES_EVENT"
    EARNINGS = "EARNINGS"
    GUIDANCE = "GUIDANCE"
    CORPORATE_ACTION = "CORPORATE_ACTION"
    MANAGEMENT_CHANGE = "MANAGEMENT_CHANGE"
    ORDER_CONTRACT = "ORDER_CONTRACT"
    M_AND_A = "M_AND_A"
    INVESTIGATION = "INVESTIGATION"
    LITIGATION = "LITIGATION"
    POLICY_CHANGE = "POLICY_CHANGE"
    SOURCE_DISCOVERY = "SOURCE_DISCOVERY"
    COLLECTOR_FAILURE = "COLLECTOR_FAILURE"
    DATA_ANOMALY = "DATA_ANOMALY"
    NARRATIVE_SHIFT = "NARRATIVE_SHIFT"
    CONTRADICTION = "CONTRADICTION"
    OTHER = "OTHER"


class CandidateStatus(StrEnum):
    DISCOVERED = "DISCOVERED"
    DUPLICATE = "DUPLICATE"
    VERIFYING = "VERIFYING"
    PRIMARY_SOURCE_FOUND = "PRIMARY_SOURCE_FOUND"
    PRIMARY_SOURCE_NOT_FOUND = "PRIMARY_SOURCE_NOT_FOUND"
    SOURCE_RIGHTS_REVIEW = "SOURCE_RIGHTS_REVIEW"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    EVIDENCE_ELIGIBILITY_REVIEW = "EVIDENCE_ELIGIBILITY_REVIEW"
    EVIDENCE_ELIGIBLE = "EVIDENCE_ELIGIBLE"
    REJECTED = "REJECTED"
    STALE = "STALE"
    ERROR = "ERROR"


class SourceType(StrEnum):
    PRIMARY_OFFICIAL = "PRIMARY_OFFICIAL"
    PRIMARY_COMPANY = "PRIMARY_COMPANY"
    PRIMARY_REGULATOR = "PRIMARY_REGULATOR"
    PRIMARY_GOVERNMENT = "PRIMARY_GOVERNMENT"
    LICENSED_DATA = "LICENSED_DATA"
    SECONDARY_REPUTABLE = "SECONDARY_REPUTABLE"
    SECONDARY_OTHER = "SECONDARY_OTHER"
    SOCIAL = "SOCIAL"
    UNKNOWN = "UNKNOWN"


class ResearchConfidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class MaterialityCandidate(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class NoveltyCandidate(StrEnum):
    NEW = "NEW"
    UPDATE = "UPDATE"
    DUPLICATE = "DUPLICATE"
    RELATED = "RELATED"
    UNKNOWN = "UNKNOWN"


class ResearchIncidentType(StrEnum):
    BROWSER_RESEARCH_UNAVAILABLE = "BROWSER_RESEARCH_UNAVAILABLE"
    CODEX_RESEARCH_RUN_MISSED = "CODEX_RESEARCH_RUN_MISSED"


class CodexResearchIncident(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    incident_type: ResearchIncidentType
    observed_at: datetime
    run_id: UUID | None = None
    detail: str = Field(min_length=3, max_length=1000)
    resolved: bool = False


class CodexResearchCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_id: UUID = Field(default_factory=uuid4)
    discovered_at: datetime
    research_run_id: UUID
    research_type: ResearchType
    scope: str
    entity_id: str | None = None
    entity_name: str | None = None
    symbol: str | None = None
    sector: str | None = None
    market: str = "INDIA"
    title: str = Field(min_length=3, max_length=300)
    summary: str = Field(min_length=3, max_length=2000)
    event_type_candidate: str = "UNKNOWN"
    materiality_candidate: MaterialityCandidate = MaterialityCandidate.UNKNOWN
    novelty_candidate: NoveltyCandidate = NoveltyCandidate.UNKNOWN
    source_url: HttpUrl
    source_domain: str
    source_type: SourceType
    primary_source_url: HttpUrl | None = None
    primary_source_status: str = "NOT_CHECKED"
    published_at: datetime | None = None
    observed_at: datetime
    available_at: datetime
    verification_status: str = "UNVERIFIED"
    duplicate_status: NoveltyCandidate = NoveltyCandidate.UNKNOWN
    existing_event_ids: tuple[str, ...] = ()
    supporting_sources: tuple[HttpUrl, ...] = ()
    contradicting_sources: tuple[HttpUrl, ...] = ()
    codex_reasoning_summary: str = Field(min_length=3, max_length=2000)
    codex_confidence: ResearchConfidence = ResearchConfidence.UNKNOWN
    source_rights_status: str = "REVIEW_REQUIRED"
    recommended_action: str = "EVIDENCE_ELIGIBILITY_REVIEW"
    status: CandidateStatus = CandidateStatus.DISCOVERED
    provenance: dict[str, Any]
    parent_candidate_id: UUID | None = None
    payload_hash: str = ""

    @model_validator(mode="after")
    def validate_candidate(self) -> CodexResearchCandidate:
        if not self.provenance:
            raise ValueError("provenance is required")
        if self.observed_at < self.discovered_at or self.available_at < self.observed_at:
            raise ValueError("candidate timestamps violate causal order")
        if self.published_at and self.observed_at < self.published_at:
            raise ValueError("candidate observed before publication")
        if urlparse(str(self.source_url)).hostname != self.source_domain.lower():
            raise ValueError("source domain does not match source URL")
        forbidden = re.compile(
            r"\b(BUY|SELL|TARGET_PRICE|EXPECTED_RETURN|PROBABILITY_UP|TRADE|STOP_LOSS|POSITION_SIZE)\b",
            re.IGNORECASE,
        )
        if forbidden.search(f"{self.title} {self.summary} {self.recommended_action}"):
            raise ValueError("prediction or execution language is forbidden")
        if self.status == CandidateStatus.EVIDENCE_ELIGIBLE:
            raise ValueError("Codex cannot directly promote evidence")
        if not self.payload_hash:
            object.__setattr__(
                self,
                "payload_hash",
                stable_hash(self.model_dump(exclude={"payload_hash"}, mode="json")),
            )
        return self


class CodexResearchRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: UUID = Field(default_factory=uuid4)
    run_type: str
    scheduled_for: datetime
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    queries: tuple[str, ...] = ()
    sources_checked: tuple[str, ...] = ()
    pages_examined: int = Field(default=0, ge=0)
    candidates_created: int = Field(default=0, ge=0)
    duplicates_suppressed: int = Field(default=0, ge=0)
    primary_sources_found: int = Field(default=0, ge=0)
    contradictions_found: int = Field(default=0, ge=0)
    incidents_found: int = Field(default=0, ge=0)
    source_candidates_found: int = Field(default=0, ge=0)
    token_usage: dict[str, int] = Field(default_factory=dict)
    errors: tuple[str, ...] = ()
    payload_hash: str = ""

    @model_validator(mode="after")
    def seal(self) -> CodexResearchRun:
        if self.started_at < self.scheduled_for:
            raise ValueError("research run starts before scheduled time")
        if self.completed_at and self.completed_at < self.started_at:
            raise ValueError("research run completion precedes start")
        if not self.payload_hash:
            object.__setattr__(self, "payload_hash", stable_hash(self.model_dump(exclude={"payload_hash"}, mode="json")))
        return self


class SourceDiscoveryCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_name: str
    official_status: bool
    url: HttpUrl
    data_type: str
    coverage: str
    frequency: str
    api_or_feed: str
    rights_notes: str
    automation_feasibility: str
    historical_availability: str
    cost_if_publicly_known: str = "UNKNOWN"
    recommendation: str
    status: str = "REVIEW_REQUIRED"

    @model_validator(mode="after")
    def no_auto_activation(self) -> SourceDiscoveryCandidate:
        if self.status != "REVIEW_REQUIRED":
            raise ValueError("new source discoveries must remain REVIEW_REQUIRED")
        return self


ALLOWED_TRANSITIONS = {
    CandidateStatus.DISCOVERED: {CandidateStatus.VERIFYING, CandidateStatus.DUPLICATE, CandidateStatus.REJECTED},
    CandidateStatus.VERIFYING: {
        CandidateStatus.PRIMARY_SOURCE_FOUND,
        CandidateStatus.PRIMARY_SOURCE_NOT_FOUND,
        CandidateStatus.SOURCE_RIGHTS_REVIEW,
        CandidateStatus.ERROR,
    },
    CandidateStatus.PRIMARY_SOURCE_FOUND: {CandidateStatus.SOURCE_VERIFIED, CandidateStatus.SOURCE_RIGHTS_REVIEW},
    CandidateStatus.SOURCE_VERIFIED: {CandidateStatus.EVIDENCE_ELIGIBILITY_REVIEW},
    CandidateStatus.SOURCE_RIGHTS_REVIEW: {CandidateStatus.EVIDENCE_ELIGIBILITY_REVIEW, CandidateStatus.REJECTED},
    CandidateStatus.EVIDENCE_ELIGIBILITY_REVIEW: {CandidateStatus.REJECTED, CandidateStatus.EVIDENCE_ELIGIBLE},
}


class ResearchLedger:
    """Append-only local ledger; core platform operation never imports or depends on it."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS research_candidate_history (
          sequence INTEGER PRIMARY KEY AUTOINCREMENT, candidate_id TEXT NOT NULL,
          recorded_at TEXT NOT NULL, status TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS research_runs (
          run_id TEXT PRIMARY KEY, scheduled_for TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS source_discoveries (
          sequence INTEGER PRIMARY KEY AUTOINCREMENT, recorded_at TEXT NOT NULL,
          payload_json TEXT NOT NULL
        );
        """)
        self.connection.commit()

    def ingest(self, candidate: CodexResearchCandidate) -> None:
        if self.history(candidate.candidate_id):
            raise ValueError("candidate already exists; append a status transition")
        self._append(candidate)

    def transition(
        self,
        candidate_id: UUID,
        status: CandidateStatus,
        *,
        deterministic_approval: bool = False,
        updates: dict[str, Any] | None = None,
    ) -> CodexResearchCandidate:
        history = self.history(candidate_id)
        if not history:
            raise KeyError("candidate does not exist")
        current = history[-1]
        if status not in ALLOWED_TRANSITIONS.get(current.status, set()):
            raise ValueError("unsupported candidate status transition")
        if status == CandidateStatus.EVIDENCE_ELIGIBLE and not deterministic_approval:
            raise ValueError("deterministic approval is required for evidence eligibility")
        payload = current.model_dump(mode="python")
        payload.update(updates or {})
        payload.update({"status": status, "payload_hash": ""})
        if status == CandidateStatus.EVIDENCE_ELIGIBLE:
            payload["status"] = CandidateStatus.EVIDENCE_ELIGIBILITY_REVIEW
            payload["recommended_action"] = "DETERMINISTIC_APPROVAL_RECORDED_FOR_STANDARD_PIPELINE"
        candidate = CodexResearchCandidate.model_validate(payload)
        self._append(candidate)
        return candidate

    def history(self, candidate_id: UUID) -> list[CodexResearchCandidate]:
        return [
            CodexResearchCandidate.model_validate_json(row[0])
            for row in self.connection.execute(
                "SELECT payload_json FROM research_candidate_history WHERE candidate_id=? ORDER BY sequence",
                (str(candidate_id),),
            )
        ]

    def latest(self) -> list[CodexResearchCandidate]:
        rows = self.connection.execute("""
            SELECT h.payload_json FROM research_candidate_history h
            JOIN (SELECT candidate_id, MAX(sequence) AS sequence FROM research_candidate_history GROUP BY candidate_id) x
            ON h.sequence=x.sequence ORDER BY h.recorded_at DESC
        """).fetchall()
        return [CodexResearchCandidate.model_validate_json(row[0]) for row in rows]

    def unresolved(self) -> list[CodexResearchCandidate]:
        terminal = {CandidateStatus.DUPLICATE, CandidateStatus.REJECTED, CandidateStatus.STALE}
        return [candidate for candidate in self.latest() if candidate.status not in terminal]

    def contradictions(self) -> list[CodexResearchCandidate]:
        return [candidate for candidate in self.latest() if candidate.research_type == ResearchType.CONTRADICTION]

    def recent_runs(self, *, limit: int = 20) -> list[CodexResearchRun]:
        rows = self.connection.execute(
            "SELECT payload_json FROM research_runs ORDER BY scheduled_for DESC LIMIT ?", (limit,)
        ).fetchall()
        return [CodexResearchRun.model_validate_json(row[0]) for row in rows]

    def source_discoveries(self, *, limit: int = 20) -> list[SourceDiscoveryCandidate]:
        rows = self.connection.execute(
            "SELECT payload_json FROM source_discoveries ORDER BY sequence DESC LIMIT ?", (limit,)
        ).fetchall()
        return [SourceDiscoveryCandidate.model_validate_json(row[0]) for row in rows]

    def add_run(self, run: CodexResearchRun) -> None:
        self.connection.execute(
            "INSERT INTO research_runs VALUES(?,?,?)",
            (str(run.run_id), run.scheduled_for.isoformat(), run.model_dump_json()),
        )
        self.connection.commit()

    def add_source_discovery(self, source: SourceDiscoveryCandidate) -> None:
        self.connection.execute(
            "INSERT INTO source_discoveries(recorded_at,payload_json) VALUES(?,?)",
            (datetime.now(UTC).isoformat(), source.model_dump_json()),
        )
        self.connection.commit()

    def _append(self, candidate: CodexResearchCandidate) -> None:
        self.connection.execute(
            "INSERT INTO research_candidate_history(candidate_id,recorded_at,status,payload_json) VALUES(?,?,?,?)",
            (str(candidate.candidate_id), datetime.now(UTC).isoformat(), candidate.status, candidate.model_dump_json()),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()


class ResearchBudget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    maximum_queries: int = Field(default=8, ge=1, le=25)
    maximum_pages: int = Field(default=20, ge=1, le=50)
    maximum_candidates: int = Field(default=10, ge=1, le=25)
    maximum_browser_interactions: int = Field(default=6, ge=0, le=20)


def normalize_title(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def title_similarity(first: str, second: str) -> float:
    left, right = set(normalize_title(first).split()), set(normalize_title(second).split())
    return len(left & right) / len(left | right) if left or right else 1.0


def novelty(candidate: CodexResearchCandidate, existing: list[CodexResearchCandidate]) -> NoveltyCandidate:
    for prior in existing:
        same_primary = candidate.primary_source_url and candidate.primary_source_url == prior.primary_source_url
        same_source = candidate.source_url == prior.source_url
        close_in_time = abs((candidate.observed_at - prior.observed_at).total_seconds()) <= 172800
        same_entity = candidate.entity_id and candidate.entity_id == prior.entity_id
        similarity = title_similarity(candidate.title, prior.title)
        if same_primary or same_source or (close_in_time and similarity >= 0.82 and same_entity):
            return NoveltyCandidate.DUPLICATE
        if close_in_time and similarity >= 0.58:
            return NoveltyCandidate.RELATED
    return NoveltyCandidate.NEW


def plan_queries(
    *,
    unknown_events: list[dict[str, str]],
    contradictions: list[dict[str, str]],
    incidents: list[dict[str, str]],
    budget: ResearchBudget,
) -> tuple[str, ...]:
    planned: list[str] = []
    for event in unknown_events:
        planned.append(f"{event.get('entity', '')} {event['title']} official filing primary source".strip())
    for item in contradictions:
        planned.append(f"{item['topic']} official clarification contradiction")
    for incident in incidents:
        planned.append(f"{incident['source']} official feed schema status")
    return tuple(dict.fromkeys(planned))[: budget.maximum_queries]


def missed_run(*, expected_at: datetime, last_completed_at: datetime | None, grace: timedelta) -> bool:
    return last_completed_at is None or last_completed_at + grace < expected_at


def operator_enabled(environment: dict[str, str]) -> bool:
    return environment.get("CODEX_RESEARCH_OPERATOR_ENABLED", "false").lower() == "true"


def _ingest(path: Path, database: Path) -> None:
    candidate = CodexResearchCandidate.model_validate_json(path.read_text(encoding="utf-8"))
    ledger = ResearchLedger(database)
    try:
        ledger.ingest(candidate)
    finally:
        ledger.close()
    print(json.dumps({"candidate_id": str(candidate.candidate_id), "status": candidate.status}))


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m intelligence_core.codex_research")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("file", type=Path)
    ingest.add_argument("--database", type=Path, default=Path("data/local/codex-research.sqlite3"))
    args = parser.parse_args()
    if args.command == "ingest":
        _ingest(args.file, args.database)


if __name__ == "__main__":
    main()
