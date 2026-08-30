from intelligence_core.models import (
    AccessMethod,
    IntelligenceSource,
    ReliabilityTier,
    SourceCategory,
    SourceStatus,
)


def initial_sources() -> tuple[IntelligenceSource, ...]:
    shared = {
        "access_method": AccessMethod.OFFICIAL_RSS,
        "official_status": True,
        "content_types": ("application/rss+xml", "text/xml"),
        "update_frequency": "15 minutes",
        "expected_latency_seconds": 900,
        "license_status": SourceStatus.ACTIVE_INTERNAL,
        "commercial_status": "NOT_EVALUATED",
        "internal_research_status": "OFFICIAL_RSS_SUBSCRIPTION",
        "redistribution_status": "METADATA_NOT_REDISTRIBUTED",
        "retention_status": "RSS_METADATA_AND_HASH",
        "rate_limit_policy": "minimum 15-minute polling",
        "reliability_tier": ReliabilityTier.TIER_1_PRIMARY,
        "active": True,
    }
    return (
        IntelligenceSource.model_validate(
            {
                "source_id": "rbi-press-releases-rss",
                "name": "RBI Press Releases RSS",
                "source_category": SourceCategory.MACRO,
                "provider": "Reserve Bank of India",
                "base_url": "https://rbi.org.in",
                "terms_url": "https://www.rbi.org.in/Scripts/rss.aspx",
                "notes": "Official RSS for automated updates; document content rights remain separate.",
                **shared,
            }
        ),
        IntelligenceSource.model_validate(
            {
                "source_id": "sebi-rss",
                "name": "SEBI RSS",
                "source_category": SourceCategory.CORPORATE_EVENT,
                "provider": "Securities and Exchange Board of India",
                "base_url": "https://www.sebi.gov.in",
                "terms_url": "https://www.sebi.gov.in/rss.html",
                "notes": "Official RSS; no customer republication.",
                **shared,
            }
        ),
    )
