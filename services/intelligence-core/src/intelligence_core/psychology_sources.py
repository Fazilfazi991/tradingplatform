from pydantic import HttpUrl

from intelligence_core.models import FrozenModel


class PsychologySourceCandidate(FrozenModel):
    source_id: str
    name: str
    url: HttpUrl
    signal_type: str
    rights_status: str
    activated: bool = False
    privacy_requirements: tuple[str, ...] = ()
    notes: str


def psychology_source_candidates() -> tuple[PsychologySourceCandidate, ...]:
    return (
        PsychologySourceCandidate(
            source_id="google-trends-api-alpha", name="Google Trends API Alpha",
            url=HttpUrl("https://developers.google.com/search/apis/trends"),
            signal_type="SEARCH_ATTENTION",
            rights_status="CANDIDATE_ACCESS_AND_PRODUCT_RIGHTS_APPROVAL_REQUIRED",
            notes="Official alpha exists; unofficial libraries do not establish commercial rights."),
        PsychologySourceCandidate(
            source_id="reddit-data-api", name="Reddit Data API",
            url=HttpUrl("https://redditinc.com/policies/data-api-terms"),
            signal_type="COMMUNITY_ATTENTION_AND_SENTIMENT",
            rights_status="BLOCKED_PENDING_EXPLICIT_COMMERCIAL_APPROVAL",
            privacy_requirements=("minimize user data", "honour deletion", "retention review",
                                  "no re-identification"),
            notes="Commercial use requires a separate agreement; no scraping or activation."),
        PsychologySourceCandidate(
            source_id="youtube-data-api", name="YouTube Data API",
            url=HttpUrl("https://developers.google.com/youtube/terms/developer-policies"),
            signal_type="VIDEO_METADATA_ATTENTION",
            rights_status="CANDIDATE_TERMS_RETENTION_AND_DISPLAY_REVIEW_REQUIRED",
            privacy_requirements=("API policy compliance", "deletion handling"),
            notes="Official API candidate only; no collection enabled."),
    )
