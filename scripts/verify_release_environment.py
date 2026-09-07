from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

Stage = Literal["local", "staging", "production"]
Profile = Literal["public-web", "intelligence-worker", "market-worker"]


@dataclass(frozen=True)
class Requirement:
    name: str
    stages: tuple[Stage, ...]
    secret: bool = False


REQUIREMENTS: dict[Profile, tuple[Requirement, ...]] = {
    "public-web": (
        Requirement("NEXT_PUBLIC_SITE_URL", ("staging", "production")),
        Requirement("VERIFIED_EDGE_INTERNAL_USERNAME", ("staging", "production"), True),
        Requirement("VERIFIED_EDGE_INTERNAL_PASSWORD", ("staging", "production"), True),
    ),
    "intelligence-worker": (
        Requirement("LLM_RUNTIME_ENABLED", ("staging", "production")),
        Requirement("OPENAI_API_KEY", ("staging", "production"), True),
        Requirement("OPENAI_MODEL", ("staging", "production")),
    ),
    "market-worker": (
        Requirement("UPSTOX_ANALYTICS_TOKEN", ("staging", "production"), True),
    ),
}


def validate_environment(
    environment: Mapping[str, str], *, profile: Profile, stage: Stage
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    errors: list[str] = []
    for requirement in REQUIREMENTS[profile]:
        required = stage in requirement.stages
        present = bool(environment.get(requirement.name, "").strip())
        rows.append(
            {
                "name": requirement.name,
                "required": required,
                "present": present,
                "secret": requirement.secret,
            }
        )
        if required and not present:
            errors.append(f"{requirement.name}:MISSING")

    if profile == "public-web" and environment.get("NEXT_PUBLIC_SITE_URL"):
        parsed = urlparse(environment["NEXT_PUBLIC_SITE_URL"])
        local = parsed.hostname in {"localhost", "127.0.0.1"}
        if not parsed.hostname or (stage != "local" and parsed.scheme != "https") or (
            parsed.scheme not in {"http", "https"}
        ):
            errors.append("NEXT_PUBLIC_SITE_URL:INVALID_OR_INSECURE")
        if stage != "local" and local:
            errors.append("NEXT_PUBLIC_SITE_URL:LOCALHOST_NOT_ALLOWED")

    if profile == "intelligence-worker":
        enabled = environment.get("LLM_RUNTIME_ENABLED", "").lower()
        if stage in {"staging", "production"} and enabled != "true":
            errors.append("LLM_RUNTIME_ENABLED:MUST_BE_TRUE")

    leaked = sorted(
        name
        for name in environment
        if name.startswith("NEXT_PUBLIC_")
        and any(marker in name for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD"))
    )
    errors.extend(f"{name}:PUBLIC_SECRET_NAME" for name in leaked)
    return {
        "profile": profile,
        "stage": stage,
        "status": "PASS" if not errors else "FAIL",
        "variables": rows,
        "errors": sorted(set(errors)),
        "values_disclosed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate release environment names safely")
    parser.add_argument("--profile", choices=tuple(REQUIREMENTS), required=True)
    parser.add_argument("--stage", choices=("local", "staging", "production"), required=True)
    args = parser.parse_args()
    report = validate_environment(os.environ, profile=args.profile, stage=args.stage)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
