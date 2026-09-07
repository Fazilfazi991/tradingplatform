# Runtime backup and restore

The current local/internal intelligence, forensic, and forward-validation ledgers use SQLite.
They are runtime state and are never committed or bundled into a web deployment.

## Backup

Stop the owning worker or otherwise ensure the database has one writer. Then run:

```powershell
.\.venv\Scripts\python.exe scripts\runtime_backup.py --source data\local\intelligence-operations.sqlite3
```

The tool uses SQLite's online backup API, runs `PRAGMA integrity_check`, and writes a separate
manifest containing size and SHA-256. Backups default to ignored `data/local/backups` storage.
Copying a live database file directly is not an approved backup procedure.

## Verification

```powershell
.\.venv\Scripts\python.exe scripts\runtime_backup.py --verify <manifest-path>
```

Verification checks the file name, size, SHA-256, and SQLite integrity. Any mismatch fails closed.

## Restore rehearsal

Restore uses `restore_backup` from `scripts.runtime_backup` and only accepts a target path that
does not exist. It never overwrites operational state. Rehearse into an isolated directory, open
the restored database read-only, compare row counts and latest execution/event timestamps, then
record the rehearsal result. Swapping restored state into service requires a separately approved
maintenance window and rollback plan.

## Retention and production boundary

Do not place credentials, raw licensed exports, or public artifacts in the backup directory.
Retention, encryption, off-host storage, recovery point objective, and recovery time objective
require an owner-approved production storage design. PostgreSQL production backup/restore must
use the managed database provider's point-in-time recovery facilities and remains an external
deployment gate; this SQLite tool is not a substitute.
