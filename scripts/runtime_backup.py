from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class BackupError(RuntimeError):
    pass


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def integrity_check(path: Path) -> None:
    try:
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        result = connection.execute("PRAGMA integrity_check").fetchone()
        connection.close()
    except sqlite3.Error as error:
        raise BackupError("database integrity check could not run") from error
    if not result or result[0] != "ok":
        raise BackupError("database integrity check failed")


def backup_database(source: Path, destination: Path, *, now: datetime) -> Path:
    source = source.resolve()
    if not source.is_file():
        raise BackupError("source database does not exist")
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    backup_path = destination / f"{source.stem}-{now.astimezone(UTC):%Y%m%dT%H%M%SZ}.sqlite3"
    manifest_path = backup_path.with_suffix(".manifest.json")
    if backup_path.exists() or manifest_path.exists():
        raise BackupError("backup destination already exists")
    source_connection = sqlite3.connect(source)
    backup_connection = sqlite3.connect(backup_path)
    try:
        source_connection.backup(backup_connection)
    finally:
        backup_connection.close()
        source_connection.close()
    integrity_check(backup_path)
    manifest = {
        "version": "sqlite-backup-v1",
        "created_at": now.astimezone(UTC).isoformat(),
        "source_name": source.name,
        "backup_name": backup_path.name,
        "size_bytes": backup_path.stat().st_size,
        "sha256": file_sha256(backup_path),
        "integrity_check": "PASS",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path


def verify_backup(manifest_path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BackupError("backup manifest is unreadable") from error
    required = {"version", "backup_name", "size_bytes", "sha256", "integrity_check"}
    if not isinstance(manifest, dict) or not required.issubset(manifest):
        raise BackupError("backup manifest is invalid")
    backup_name = manifest["backup_name"]
    if (
        manifest["version"] != "sqlite-backup-v1"
        or manifest["integrity_check"] != "PASS"
        or not isinstance(backup_name, str)
        or Path(backup_name).name != backup_name
        or not backup_name.endswith(".sqlite3")
        or not isinstance(manifest["size_bytes"], int)
        or manifest["size_bytes"] < 0
        or not isinstance(manifest["sha256"], str)
        or len(manifest["sha256"]) != 64
    ):
        raise BackupError("backup manifest is invalid")
    backup_path = manifest_path.parent / backup_name
    if not backup_path.is_file():
        raise BackupError("backup file is missing")
    if backup_path.stat().st_size != manifest["size_bytes"]:
        raise BackupError("backup size mismatch")
    if file_sha256(backup_path) != manifest["sha256"]:
        raise BackupError("backup hash mismatch")
    integrity_check(backup_path)
    return {**manifest, "verification": "PASS"}


def restore_backup(manifest_path: Path, target: Path) -> Path:
    manifest = verify_backup(manifest_path)
    target = target.resolve()
    if target.exists():
        raise BackupError("restore target already exists; overwrite is forbidden")
    target.parent.mkdir(parents=True, exist_ok=True)
    backup_path = manifest_path.parent / manifest["backup_name"]
    source_connection = sqlite3.connect(backup_path)
    target_connection = sqlite3.connect(target)
    try:
        source_connection.backup(target_connection)
    finally:
        target_connection.close()
        source_connection.close()
    integrity_check(target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup or verify local SQLite runtime state")
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--source", type=Path)
    actions.add_argument("--verify", type=Path)
    parser.add_argument("--destination", type=Path, default=Path("data/local/backups"))
    args = parser.parse_args()
    if args.source:
        result = backup_database(args.source, args.destination, now=datetime.now(UTC))
        print(json.dumps({"status": "PASS", "manifest": str(result)}))
    else:
        result = verify_backup(args.verify)
        print(json.dumps({"status": "PASS", "sha256": result["sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
