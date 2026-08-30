from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from verified_edge.domain import InformationEvent, SourceCategory


class IntelligenceSource(ABC):
    category: SourceCategory

    @abstractmethod
    def fetch(
        self, entity_ids: list[UUID], available_before: datetime
    ) -> list[InformationEvent]: ...


class NewsSource(IntelligenceSource):
    category = SourceCategory.NEWS


class FundamentalSource(IntelligenceSource):
    category = SourceCategory.FUNDAMENTAL


class MacroSource(IntelligenceSource):
    category = SourceCategory.MACRO


class SentimentSource(IntelligenceSource):
    category = SourceCategory.SENTIMENT


class FlowSource(IntelligenceSource):
    category = SourceCategory.FLOW


class DerivativesSource(IntelligenceSource):
    category = SourceCategory.DERIVATIVES


class CorporateEventSource(IntelligenceSource):
    category = SourceCategory.CORPORATE
