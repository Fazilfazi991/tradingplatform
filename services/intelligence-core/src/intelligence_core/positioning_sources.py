from typing import Any

from pydantic import HttpUrl

from intelligence_core.models import FrozenModel


class PositioningSourceCandidate(FrozenModel):
    source_id: str
    name: str
    url: HttpUrl
    official_status: str
    access_mechanism: str
    automated_access_status: str
    retention: str
    internal_research_rights: str
    commercial_rights: str
    redistribution: str
    rate_limits: str
    historical_depth: str
    timestamp_quality: str
    review_state: str
    activated: bool = False


def positioning_source_candidates() -> tuple[PositioningSourceCandidate, ...]:
    common: dict[str, Any] = {"official_status": "OFFICIAL_PRIMARY_PUBLICATION",
              "automated_access_status": "REVIEW_REQUIRED_NO_SCRAPER",
              "retention": "REVIEW_REQUIRED", "internal_research_rights": "REVIEW_REQUIRED",
              "commercial_rights": "REVIEW_REQUIRED", "redistribution": "NOT_APPROVED",
              "rate_limits": "NOT_DOCUMENTED_FOR_AUTOMATION", "historical_depth": "VARIES",
              "timestamp_quality": "EOD_OR_REPORT_SPECIFIC", "review_state": "CANDIDATE"}
    return (
        PositioningSourceCandidate(source_id="nse-fii-dii", name="NSE FII/FPI & DII Trading Activity",
            url=HttpUrl("https://www.nseindia.com/reports/fii-dii"), access_mechanism="OFFICIAL_CSV", **common),
        PositioningSourceCandidate(source_id="nse-fo-reports", name="NSE F&O Reports",
            url=HttpUrl("https://www.nseindia.com/all-reports-derivatives"),
            access_mechanism="OFFICIAL_CSV_ZIP_REPORTS", **common),
        PositioningSourceCandidate(source_id="nsdl-fpi", name="NSDL FPI Investment Reports",
            url=HttpUrl("https://pilot.fpi.nsdl.co.in/Reports/ReportsListing.aspx"),
            access_mechanism="OFFICIAL_REPORT_AND_EXPORT", **common),
        PositioningSourceCandidate(source_id="bse-bulk-block", name="BSE Bulk and Block Deal Reports",
            url=HttpUrl("https://www.bseindia.com/markets/equity/EQReports/bulk_deals.aspx"),
            access_mechanism="OFFICIAL_EOD_REPORT", **common),
    )
