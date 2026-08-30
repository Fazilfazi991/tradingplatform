from __future__ import annotations

import re
from dataclasses import dataclass

from intelligence_core.models import EntityMatch


@dataclass(frozen=True)
class Entity:
    entity_id: str
    legal_name: str
    isin: str | None
    symbols: tuple[str, ...]
    aliases: tuple[str, ...]


class EntityResolver:
    def __init__(self, entities: list[Entity]) -> None:
        self.entities = entities

    def resolve(
        self, text: str, *, isin: str | None = None, symbol: str | None = None
    ) -> EntityMatch:
        anchors = []
        for entity in self.entities:
            evidence = []
            if isin and entity.isin == isin:
                evidence.append(f"ISIN:{isin}")
            if symbol and symbol.upper() in {value.upper() for value in entity.symbols}:
                evidence.append(f"SYMBOL:{symbol.upper()}")
            normalized = _normalize(text)
            names = {entity.legal_name, *entity.aliases, *entity.symbols}
            if any(re.search(rf"\b{re.escape(_normalize(name))}\b", normalized) for name in names):
                evidence.append("EXACT_ALIAS")
            if evidence:
                anchors.append((entity.entity_id, evidence))
        if not anchors:
            return EntityMatch(status="UNMATCHED", confidence=0, evidence=())
        if len(anchors) > 1:
            return EntityMatch(
                status="MULTI_ENTITY",
                entity_ids=tuple(a[0] for a in anchors),
                confidence=1,
                evidence=tuple(item for _, evidence in anchors for item in evidence),
            )
        identifier, evidence = anchors[0]
        confidence = 1.0 if any(value.startswith(("ISIN", "SYMBOL")) for value in evidence) else 0.9
        return EntityMatch(
            status="MATCHED",
            entity_ids=(identifier,),
            confidence=confidence,
            evidence=tuple(evidence),
        )


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
