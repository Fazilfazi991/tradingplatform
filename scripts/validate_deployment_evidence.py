from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def evidence_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


class DeploymentChecks(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    environment_contract: Literal["PASS"]
    public_routes: Literal["PASS"]
    internal_auth_boundary: Literal["PASS"]
    public_payload_boundary: Literal["PASS"]
    security_headers: Literal["PASS"]
    robots_sitemap_canonical: Literal["PASS"]
    unknown_stock_404: Literal["PASS"]
    console_network: Literal["PASS"]
    rollback_rehearsal: Literal["PASS"]


class DeploymentEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal["deployment-evidence-v1"] = "deployment-evidence-v1"
    environment: Literal["staging", "production"]
    deployment_id: str = Field(min_length=1, max_length=200)
    rollback_deployment_id: str = Field(min_length=1, max_length=200)
    commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    url: str
    recorded_at: datetime
    operator: str = Field(min_length=1, max_length=100)
    checks: DeploymentChecks
    state_migration: Literal["PASS", "NOT_APPLICABLE"]
    artifact_hash: str = ""

    @field_validator("url")
    @classmethod
    def validate_origin(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("deployment URL must be an uncredentialed HTTPS origin")
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError("deployment URL must not contain path, query, or fragment")
        hostname = parsed.hostname.lower()
        if hostname == "localhost" or hostname.endswith(".localhost"):
            raise ValueError("deployment URL cannot be localhost")
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            address = None
        if address and not address.is_global:
            raise ValueError("deployment URL cannot use a non-global address")
        return value.rstrip("/")

    @field_validator("recorded_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("recorded_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def seal(self) -> DeploymentEvidence:
        if self.deployment_id == self.rollback_deployment_id:
            raise ValueError("rollback target must differ from the candidate deployment")
        expected = evidence_hash(self.model_dump(exclude={"artifact_hash"}, mode="json"))
        if self.artifact_hash and self.artifact_hash != expected:
            raise ValueError("deployment evidence hash mismatch")
        if not self.artifact_hash:
            object.__setattr__(self, "artifact_hash", expected)
        return self


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate sealed deployment evidence")
    parser.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    evidence = DeploymentEvidence.model_validate_json(args.file.read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "status": "PASS",
                "environment": evidence.environment,
                "commit_sha": evidence.commit_sha,
                "url": evidence.url,
                "artifact_hash": evidence.artifact_hash,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
