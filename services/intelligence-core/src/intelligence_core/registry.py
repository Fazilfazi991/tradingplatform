from __future__ import annotations

from datetime import UTC, datetime

from intelligence_core.models import IntelligenceSource, SourceStatus


class SourceRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, IntelligenceSource] = {}

    def register(self, source: IntelligenceSource) -> None:
        if source.source_id in self._sources:
            raise ValueError(f"duplicate source_id: {source.source_id}")
        if source.active and source.license_status not in {
            SourceStatus.ACTIVE_FIXTURE,
            SourceStatus.ACTIVE_INTERNAL,
        }:
            raise ValueError("only approved fixture/internal sources may be active")
        self._sources[source.source_id] = source

    def get(self, source_id: str) -> IntelligenceSource:
        return self._sources[source_id]

    def all(self) -> tuple[IntelligenceSource, ...]:
        return tuple(self._sources[key] for key in sorted(self._sources))

    def update_health(self, source_id: str, status) -> None:
        source = self.get(source_id)
        self._sources[source_id] = source.model_copy(
            update={"health_status": status, "updated_at": datetime.now(UTC)}
        )


class SourceCandidateRegistry:
    def __init__(self) -> None:
        self._records: dict[str, dict] = {}

    def propose(self, candidate: dict) -> None:
        identifier = candidate["candidate_id"]
        if identifier in self._records:
            raise ValueError("candidate already exists")
        if candidate.get("review_status") == "ACTIVE":
            raise ValueError("candidates cannot activate themselves")
        self._records[identifier] = {**candidate, "review_status": "PROPOSED"}

    def review(self, candidate_id: str, *, decision: str, reason: str) -> None:
        if decision not in {"APPROVE_FOR_IMPLEMENTATION", "REJECT", "REVIEW_REQUIRED"}:
            raise ValueError("invalid human review decision")
        self._records[candidate_id] |= {
            "decision": decision,
            "reason": reason,
            "review_status": "REVIEWED",
        }

    def get(self, candidate_id: str) -> dict:
        return dict(self._records[candidate_id])
