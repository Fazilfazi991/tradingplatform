from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class UniverseState(StrEnum):
    DISCOVERED = "DISCOVERED"
    IDENTITY_RESOLVED = "IDENTITY_RESOLVED"
    DATA_PENDING = "DATA_PENDING"
    QUALITY_PENDING = "QUALITY_PENDING"
    RESEARCH_ELIGIBLE = "RESEARCH_ELIGIBLE"
    SUSPENDED = "SUSPENDED"
    DELISTED = "DELISTED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class InstrumentRecord:
    instrument_id: str
    symbol: str
    isin: str
    legal_name: str
    exchange: str
    sector: str | None
    provider_ids: dict[str, str]
    state: UniverseState


class UniverseManager:
    def __init__(self) -> None:
        self.records: dict[str, InstrumentRecord] = {}
        self.changes: list[dict[str, str]] = []

    def detect(self, observations: list[dict[str, str]]) -> list[InstrumentRecord]:
        discovered = []
        for item in observations:
            identifier = item.get("isin") or f"{item['exchange']}:{item['symbol']}"
            existing = self.records.get(identifier)
            if existing is None:
                record = InstrumentRecord(
                    identifier,
                    item["symbol"],
                    item.get("isin", ""),
                    item["legal_name"],
                    item["exchange"],
                    item.get("sector"),
                    {item.get("provider", "source"): item.get("provider_id", item["symbol"])},
                    UniverseState.DATA_PENDING,
                )
                self.records[identifier] = record
                discovered.append(record)
                self.changes.append({"type": "NEW_LISTING", "instrument_id": identifier})
            elif existing.symbol != item["symbol"]:
                self.records[identifier] = InstrumentRecord(
                    existing.instrument_id,
                    item["symbol"],
                    existing.isin,
                    item["legal_name"],
                    existing.exchange,
                    item.get("sector"),
                    existing.provider_ids,
                    UniverseState.DATA_PENDING,
                )
                self.changes.append({"type": "SYMBOL_CHANGE", "instrument_id": identifier})
        return discovered

    def transition(self, instrument_id: str, state: UniverseState) -> None:
        if state == UniverseState.RESEARCH_ELIGIBLE:
            raise PermissionError("research eligibility requires separate quality/history approval")
        current = self.records[instrument_id]
        self.records[instrument_id] = InstrumentRecord(**{**current.__dict__, "state": state})

    def coverage(self) -> dict[str, int]:
        return {
            "total_known_instruments": len(self.records),
            "research_eligible": sum(
                r.state == UniverseState.RESEARCH_ELIGIBLE for r in self.records.values()
            ),
            "data_pending": sum(
                r.state == UniverseState.DATA_PENDING for r in self.records.values()
            ),
            "changes_detected": len(self.changes),
        }
