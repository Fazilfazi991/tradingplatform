from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import Field

from intelligence_core.models import FrozenModel, SourceStatus


class NewsArticleReference(FrozenModel):
    source_article_id: str
    headline: str
    published_at: datetime
    observed_at: datetime
    entities: tuple[str, ...] = ()
    body_reference: str | None = None
    language: str = "en"
    category: str
    source_id: str
    metadata: dict = Field(default_factory=dict)


class NewsProvider(Protocol):
    def fetch_since(self, since: datetime) -> list[NewsArticleReference]: ...

    def health_check(self) -> dict: ...


class CompanyEventSourceCandidate(FrozenModel):
    source_id: str
    name: str
    official_url: str
    access_method: str
    status: SourceStatus
    reason: str
    activated: bool = False


def company_event_candidates() -> tuple[CompanyEventSourceCandidate, ...]:
    return (
        CompanyEventSourceCandidate(
            source_id="nse-corporate-rss",
            name="NSE Corporate Information RSS",
            official_url="https://www.nseindia.com/static/rss-feed",
            access_method="OFFICIAL_RSS",
            status=SourceStatus.REVIEW_REQUIRED,
            reason="Official subscription mechanism confirmed; exact feed URLs and retention terms require controlled onboarding.",
        ),
        CompanyEventSourceCandidate(
            source_id="nse-corporate-data",
            name="NSE Licensed Corporate Data",
            official_url="https://www.nseindia.com/static/market-data/corporate-data-subscription",
            access_method="LICENSED_FEED",
            status=SourceStatus.REVIEW_REQUIRED,
            reason="Official licensed continuous/EOD product; commercial agreement required.",
        ),
        CompanyEventSourceCandidate(
            source_id="bse-self-data-corporate",
            name="BSE Self Data Feed Corporate API",
            official_url="https://marketdata.bseindia.com/",
            access_method="LICENSED_API",
            status=SourceStatus.REVIEW_REQUIRED,
            reason="Official exchange API product; KYC, pricing and agreement required.",
        ),
    )
