import sqlite3
from datetime import UTC, datetime

import pytest

from scripts.runtime_backup import BackupError, backup_database, restore_backup, verify_backup


def test_backup_verify_and_non_overwriting_restore(tmp_path):
    source = tmp_path / "source.sqlite3"
    connection = sqlite3.connect(source)
    connection.execute("CREATE TABLE events(id INTEGER PRIMARY KEY, value TEXT)")
    connection.execute("INSERT INTO events(value) VALUES('preserved')")
    connection.commit()
    connection.close()

    manifest = backup_database(
        source,
        tmp_path / "backups",
        now=datetime(2026, 9, 8, tzinfo=UTC),
    )
    assert verify_backup(manifest)["verification"] == "PASS"
    restored = restore_backup(manifest, tmp_path / "restore" / "state.sqlite3")
    restored_connection = sqlite3.connect(restored)
    assert restored_connection.execute("SELECT value FROM events").fetchone()[0] == "preserved"
    restored_connection.close()
    with pytest.raises(BackupError, match="overwrite is forbidden"):
        restore_backup(manifest, restored)


def test_modified_backup_fails_hash_verification(tmp_path):
    source = tmp_path / "source.sqlite3"
    connection = sqlite3.connect(source)
    connection.execute("CREATE TABLE state(value TEXT)")
    connection.commit()
    connection.close()
    manifest = backup_database(source, tmp_path / "backups", now=datetime.now(UTC))
    backup = next((tmp_path / "backups").glob("*.sqlite3"))
    with backup.open("ab") as handle:
        handle.write(b"tampered")
    with pytest.raises(BackupError, match="size mismatch"):
        verify_backup(manifest)


def test_backup_manifest_rejects_path_traversal(tmp_path):
    manifest = tmp_path / "malicious.manifest.json"
    manifest.write_text(
        '{"version":"sqlite-backup-v1","backup_name":"../outside.sqlite3",'
        '"size_bytes":0,"sha256":"0000000000000000000000000000000000000000000000000000000000000000",'
        '"integrity_check":"PASS"}',
        encoding="utf-8",
    )
    with pytest.raises(BackupError, match="manifest is invalid"):
        verify_backup(manifest)
