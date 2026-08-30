from __future__ import annotations

from datetime import datetime
from typing import Protocol

from intelligence_core.macro import MacroObservation
from intelligence_core.models import FrozenModel, SourceStatus


class MacroProvider(Protocol):
    def observations_since(self, since: datetime) -> list[MacroObservation]: ...

    def health_check(self) -> dict: ...


class MacroSourceCandidate(FrozenModel):
    source_id: str
    name: str
    official_url: str
    access_method: str
    status: SourceStatus
    revision_capable: bool
    reason: str
    activated: bool = False


def macro_source_candidates() -> tuple[MacroSourceCandidate, ...]:
    return (
        MacroSourceCandidate(
            source_id="rbi-dbie",
            name="RBI Database on Indian Economy",
            official_url="https://dbie.rbi.org.in/",
            access_method="OFFICIAL_PORTAL",
            status=SourceStatus.REVIEW_REQUIRED,
            revision_capable=True,
            reason="Public official dissemination; stable automated endpoint and retention review pending.",
        ),
        MacroSourceCandidate(
            source_id="mospi-releases",
            name="MOSPI official releases",
            official_url="https://mospi.gov.in/",
            access_method="OFFICIAL_FILE",
            status=SourceStatus.REVIEW_REQUIRED,
            revision_capable=True,
            reason="Official CPI/GDP/IIP source; release-specific adapter validation pending.",
        ),
        MacroSourceCandidate(
            source_id="fred-alfred",
            name="FRED and ALFRED APIs",
            official_url="https://fred.stlouisfed.org/docs/api/fred/",
            access_method="OFFICIAL_API",
            status=SourceStatus.REVIEW_REQUIRED,
            revision_capable=True,
            reason="API key, terms acceptance and series-owner rights review required.",
        ),
        MacroSourceCandidate(
            source_id="us-bls-api",
            name="US Bureau of Labor Statistics API",
            official_url="https://www.bls.gov/developers/",
            access_method="OFFICIAL_API",
            status=SourceStatus.REVIEW_REQUIRED,
            revision_capable=True,
            reason="Official public API; selected-series and vintage behavior validation pending.",
        ),
        MacroSourceCandidate(
            source_id="us-bea-api",
            name="US Bureau of Economic Analysis API",
            official_url="https://apps.bea.gov/api/",
            access_method="OFFICIAL_API",
            status=SourceStatus.REVIEW_REQUIRED,
            revision_capable=True,
            reason="Official public API; key/terms and release-vintage validation pending.",
        ),
    )
