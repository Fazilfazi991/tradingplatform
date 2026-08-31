from __future__ import annotations

import hashlib
import ipaddress
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx

from intelligence_core.models import (
    CollectionPolicy,
    EventType,
    InformationEvent,
    IntelligenceSource,
)


class CollectorError(RuntimeError):
    pass


class SecurityPolicyError(CollectorError):
    pass


@dataclass(frozen=True)
class RawArtifact:
    source_id: str
    uri: str
    content_type: str
    payload: bytes
    observed_at: datetime

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.payload).hexdigest()


class IntelligenceCollector(ABC):
    @abstractmethod
    def discover(self) -> list[str]: ...

    @abstractmethod
    def fetch(self, uri: str) -> RawArtifact: ...

    @abstractmethod
    def parse(self, artifact: RawArtifact) -> list[dict]: ...

    @abstractmethod
    def normalize(self, records: list[dict], artifact: RawArtifact) -> list[InformationEvent]: ...

    @abstractmethod
    def health_check(self) -> bool: ...

    @abstractmethod
    def checkpoint(self) -> str | None: ...

    @abstractmethod
    def replay(self, artifact: RawArtifact) -> list[InformationEvent]: ...

    @abstractmethod
    def source_metadata(self) -> IntelligenceSource: ...


def validate_url(uri: str, allowed_hosts: set[str]) -> None:
    parsed = urlparse(uri)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.hostname.lower() not in allowed_hosts
    ):
        raise SecurityPolicyError("URL is not an approved HTTPS source host")
    try:
        if ipaddress.ip_address(parsed.hostname).is_private:
            raise SecurityPolicyError("private network targets are forbidden")
    except ValueError:
        pass
    if parsed.username or parsed.password or parsed.port not in {None, 443}:
        raise SecurityPolicyError("credentials and nonstandard ports are forbidden")


class OfficialRssCollector(IntelligenceCollector):
    def __init__(
        self,
        source: IntelligenceSource,
        policy: CollectionPolicy,
        feed_url: str,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.source = source
        self.policy = policy
        self.feed_url = feed_url
        hostname = urlparse(str(source.base_url)).hostname
        if not hostname:
            raise SecurityPolicyError("source base URL has no hostname")
        configured_hosts = {value.lower() for value in source.entities_supported if "." in value}
        self.allowed_hosts = {hostname.lower(), *configured_hosts}
        validate_url(feed_url, self.allowed_hosts)
        self.transport = transport
        self._checkpoint: str | None = None

    def discover(self) -> list[str]:
        return [self.feed_url]

    def fetch(self, uri: str) -> RawArtifact:
        validate_url(uri, self.allowed_hosts)
        with httpx.Client(
            timeout=self.policy.timeout_seconds, follow_redirects=False, transport=self.transport
        ) as client:
            response = client.get(uri, headers={"User-Agent": "VerifiedEdge-InternalResearch/1.0"})
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").split(";")[0].lower()
        if content_type not in {"application/rss+xml", "application/xml", "text/xml"}:
            raise CollectorError(f"unsupported content type: {content_type}")
        if len(response.content) > self.policy.maximum_bytes:
            raise CollectorError("bounded download limit exceeded")
        return RawArtifact(
            self.source.source_id, uri, content_type, response.content, datetime.now(UTC)
        )

    def parse(self, artifact: RawArtifact) -> list[dict]:
        try:
            root = ET.fromstring(artifact.payload)
        except ET.ParseError as error:
            raise CollectorError("malformed RSS XML") from error
        records = []
        for item in root.findall(".//item"):
            records.append({child.tag.lower(): (child.text or "").strip() for child in item})
        return records

    def normalize(self, records: list[dict], artifact: RawArtifact) -> list[InformationEvent]:
        events = []
        for record in records:
            title = record.get("title", "").strip()
            link = record.get("link", "").strip()
            if not title or not link:
                continue
            validate_url(link, self.allowed_hosts)
            published = _rss_time(record.get("pubdate")) or artifact.observed_at
            events.append(
                InformationEvent(
                    source_id=self.source.source_id,
                    source_event_id=record.get("guid") or link,
                    entity_type="MACRO_OR_REGULATORY",
                    event_type=EventType.OTHER,
                    title=title,
                    summary=record.get("description", ""),
                    canonical_url=link,
                    raw_artifact_uri=artifact.uri,
                    raw_payload_hash=artifact.sha256,
                    event_time=published,
                    published_at=published,
                    observed_at=artifact.observed_at,
                    available_at=max(published, artifact.observed_at),
                    collection_origin="FORWARD_COLLECTED",
                    source_available_at=published,
                    system_observed_at=artifact.observed_at,
                )
            )
        return events

    def health_check(self) -> bool:
        return bool(self.discover())

    def checkpoint(self) -> str | None:
        return self._checkpoint

    def replay(self, artifact: RawArtifact) -> list[InformationEvent]:
        return self.normalize(self.parse(artifact), artifact)

    def source_metadata(self) -> IntelligenceSource:
        return self.source


def _rss_time(value: str | None) -> datetime | None:
    if not value:
        return None
    from email.utils import parsedate_to_datetime

    try:
        parsed = parsedate_to_datetime(value)
    except ValueError:
        parsed = datetime.strptime(value, "%d %b, %Y %z")
    if parsed.tzinfo:
        return parsed.astimezone(UTC)
    # Indian regulator RSS feeds publish local wall time without a numeric offset.
    return parsed.replace(tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(UTC)
