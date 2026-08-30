from __future__ import annotations

from enum import StrEnum

from pydantic import HttpUrl

from intelligence_core.models import FrozenModel


class DocumentFormat(StrEnum):
    PDF = "PDF"
    XBRL = "XBRL"
    HTML = "HTML"
    JSON = "JSON"
    CSV = "CSV"


class FundamentalSourceCandidate(FrozenModel):
    source_id: str
    name: str
    url: HttpUrl
    authority: str
    formats: tuple[DocumentFormat, ...]
    industry_taxonomies: tuple[str, ...]
    rights_status: str
    activated: bool = False
    notes: str


def fundamental_source_candidates() -> tuple[FundamentalSourceCandidate, ...]:
    return (
        FundamentalSourceCandidate(
            source_id="nse-financial-results",
            name="NSE Corporate Filings — Financial Results",
            url=HttpUrl("https://www.nseindia.com/companies-listing/corporate-filings-financial-results"),
            authority="PRIMARY_EXCHANGE_DISCLOSURE",
            formats=(DocumentFormat.XBRL, DocumentFormat.CSV, DocumentFormat.PDF),
            industry_taxonomies=("IND_AS", "BANK", "NBFC", "LIFE_INSURANCE", "GENERAL_INSURANCE"),
            rights_status="CANDIDATE_REQUIRES_AUTOMATION_AND_REDISTRIBUTION_REVIEW",
            notes="Public interface and XBRL utilities exist; no bulk collector activated.",
        ),
        FundamentalSourceCandidate(
            source_id="bse-corporate-filings",
            name="BSE Corporate Announcements / Financial Results",
            url=HttpUrl("https://www.bseindia.com/corporates/ann.html"),
            authority="PRIMARY_EXCHANGE_DISCLOSURE",
            formats=(DocumentFormat.XBRL, DocumentFormat.PDF),
            industry_taxonomies=("IND_AS", "BANK", "NBFC", "INSURANCE"),
            rights_status="CANDIDATE_REQUIRES_AUTOMATION_AND_REDISTRIBUTION_REVIEW",
            notes="Use only after endpoint, rate, retention and redistribution review.",
        ),
        FundamentalSourceCandidate(
            source_id="company-investor-relations",
            name="Issuer investor-relations disclosures",
            url=HttpUrl("https://www.sebi.gov.in/legal/master-circulars/jan-2026/"
                        "master-circular-for-compliance-with-the-provisions-of-the-securities-and-"
                        "exchange-board-of-india-listing-obligations-and-disclosure-requirements-"
                        "regulations-2015-by-listed-entities_99478.html"),
            authority="PRIMARY_ISSUER_DISCLOSURE",
            formats=(DocumentFormat.PDF, DocumentFormat.HTML),
            industry_taxonomies=("ISSUER_SPECIFIC",),
            rights_status="PER_ISSUER_REVIEW_REQUIRED",
            notes="Discovery contract only; do not crawl issuer sites automatically.",
        ),
    )


SOURCE_PRECEDENCE = (
    "EXCHANGE_XBRL",
    "EXCHANGE_SIGNED_RESULT",
    "ISSUER_SIGNED_RESULT",
    "ISSUER_ANNUAL_REPORT",
    "LICENSED_VENDOR",
    "DERIVED_INTERPRETATION",
)
