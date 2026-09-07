from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from intelligence_core.collectors import RawArtifact
from intelligence_core.models import InformationEvent, IntelligenceIncident

IST = ZoneInfo("Asia/Kolkata")


@dataclass(frozen=True)
class DurableJob:
    name: str
    kind: str
    source_id: str | None
    cadence_seconds: int | None
    local_time: str | None
    weekday: int | None
    next_run_at: datetime
    version: str


class SQLiteOperationsStore:
    """Local durable state with lease semantics designed to map onto PostgreSQL."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS schedules (
          name TEXT PRIMARY KEY, definition_json TEXT NOT NULL, version TEXT NOT NULL,
          next_run_at TEXT NOT NULL, last_run_at TEXT, enabled INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS executions (
          execution_key TEXT PRIMARY KEY, job_name TEXT NOT NULL, scheduled_for TEXT NOT NULL,
          started_at TEXT NOT NULL, ended_at TEXT, status TEXT NOT NULL, result_json TEXT
        );
        CREATE TABLE IF NOT EXISTS leases (
          job_name TEXT PRIMARY KEY, owner TEXT NOT NULL, acquired_at TEXT NOT NULL,
          expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS incidents (
          incident_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS checkpoints (
          source_id TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS raw_artifacts (
          sha256 TEXT PRIMARY KEY, source_id TEXT NOT NULL, uri TEXT NOT NULL,
          content_type TEXT NOT NULL, payload BLOB NOT NULL, observed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS information_events (
          event_key TEXT PRIMARY KEY, source_id TEXT NOT NULL, payload_json TEXT NOT NULL,
          observed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS service_runtime (
          instance_id TEXT PRIMARY KEY, pid INTEGER NOT NULL, started_at TEXT NOT NULL,
          heartbeat_at TEXT NOT NULL, status TEXT NOT NULL, stopped_at TEXT
        );
        """)
        self.connection.commit()

    def load_config(self, path: str | Path, *, now: datetime) -> None:
        config = json.loads(Path(path).read_text(encoding="utf-8"))
        for definition in config["jobs"]:
            next_run = now.astimezone(UTC) if definition.get("run_immediately") else next_run_at(definition, now)
            self.connection.execute(
                "INSERT INTO schedules(name,definition_json,version,next_run_at) VALUES(?,?,?,?) "
                "ON CONFLICT(name) DO UPDATE SET definition_json=excluded.definition_json, version=excluded.version",
                (
                    definition["name"],
                    json.dumps(definition, sort_keys=True),
                    config["version"],
                    next_run.isoformat(),
                ),
            )
        self.connection.commit()

    def due_jobs(self, now: datetime) -> list[DurableJob]:
        rows = self.connection.execute(
            "SELECT * FROM schedules WHERE enabled=1 AND next_run_at<=? ORDER BY next_run_at,name",
            (now.astimezone(UTC).isoformat(),),
        ).fetchall()
        return [self._job(row) for row in rows]

    def all_jobs(self) -> list[DurableJob]:
        return [
            self._job(row)
            for row in self.connection.execute("SELECT * FROM schedules ORDER BY name")
        ]

    def acquire(self, job_name: str, owner: str, *, now: datetime, ttl: timedelta) -> bool:
        self.connection.execute("DELETE FROM leases WHERE expires_at<=?", (now.isoformat(),))
        try:
            self.connection.execute(
                "INSERT INTO leases VALUES(?,?,?,?)",
                (job_name, owner, now.isoformat(), (now + ttl).isoformat()),
            )
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            self.connection.rollback()
            return False

    def release(self, job_name: str, owner: str) -> None:
        self.connection.execute(
            "DELETE FROM leases WHERE job_name=? AND owner=?", (job_name, owner)
        )
        self.connection.commit()

    def begin_execution(self, job: DurableJob, now: datetime) -> str | None:
        key = f"{job.name}:{job.next_run_at.isoformat()}"
        try:
            self.connection.execute(
                "INSERT INTO executions VALUES(?,?,?,?,?,?,?)",
                (
                    key,
                    job.name,
                    job.next_run_at.isoformat(),
                    now.isoformat(),
                    None,
                    "RUNNING",
                    None,
                ),
            )
            self.connection.commit()
            return key
        except sqlite3.IntegrityError:
            self.connection.rollback()
            return None

    def finish_execution(
        self, key: str, job: DurableJob, *, now: datetime, status: str, result: dict
    ) -> None:
        following = next_run_at(
            json.loads(
                self.connection.execute(
                    "SELECT definition_json FROM schedules WHERE name=?", (job.name,)
                ).fetchone()[0]
            ),
            now,
        )
        self.connection.execute(
            "UPDATE executions SET ended_at=?,status=?,result_json=? WHERE execution_key=?",
            (now.isoformat(), status, json.dumps(result, sort_keys=True, default=str), key),
        )
        self.connection.execute(
            "UPDATE schedules SET last_run_at=?,next_run_at=? WHERE name=?",
            (now.isoformat(), following.isoformat(), job.name),
        )
        self.connection.commit()

    def recover_interrupted(self, now: datetime) -> int:
        cursor = self.connection.execute(
            "UPDATE executions SET ended_at=?,status='INTERRUPTED' WHERE status='RUNNING'",
            (now.isoformat(),),
        )
        self.connection.execute("DELETE FROM leases WHERE expires_at<=?", (now.isoformat(),))
        self.connection.commit()
        return cursor.rowcount

    def record_incident(self, incident: IntelligenceIncident) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO incidents VALUES(?,?)",
            (str(incident.incident_id), incident.model_dump_json()),
        )
        self.connection.commit()

    def incidents(self) -> list[dict]:
        return [
            json.loads(row[0])
            for row in self.connection.execute("SELECT payload_json FROM incidents")
        ]

    def has_open_incident(self, incident_type: str, *, source_id: str | None = None) -> bool:
        return any(
            incident.get("incident_type") == incident_type
            and incident.get("source_id") == source_id
            and incident.get("status") in {"OPEN", "ACKNOWLEDGED"}
            for incident in self.incidents()
        )

    def resolve_open_incidents(
        self,
        incident_type: str,
        *,
        source_id: str | None,
        now: datetime,
        resolution: str,
    ) -> int:
        rows = self.connection.execute("SELECT incident_id,payload_json FROM incidents").fetchall()
        resolved = 0
        for incident_id, payload_json in rows:
            payload = json.loads(payload_json)
            if (
                payload.get("incident_type") != incident_type
                or payload.get("source_id") != source_id
                or payload.get("status") not in {"OPEN", "ACKNOWLEDGED"}
            ):
                continue
            payload.update(
                status="RESOLVED",
                resolution=resolution,
                closed_at=now.astimezone(UTC).isoformat(),
            )
            self.connection.execute(
                "UPDATE incidents SET payload_json=? WHERE incident_id=?",
                (json.dumps(payload, sort_keys=True), incident_id),
            )
            resolved += 1
        self.connection.commit()
        return resolved

    def events(self) -> list[InformationEvent]:
        return [
            InformationEvent.model_validate_json(row[0])
            for row in self.connection.execute(
                "SELECT payload_json FROM information_events ORDER BY observed_at,event_key"
            )
        ]

    def execution_keys(self) -> list[str]:
        return [
            row[0]
            for row in self.connection.execute(
                "SELECT execution_key FROM executions ORDER BY scheduled_for,execution_key"
            )
        ]

    def checkpoint(self, source_id: str) -> str | None:
        row = self.connection.execute(
            "SELECT value FROM checkpoints WHERE source_id=?", (source_id,)
        ).fetchone()
        return str(row[0]) if row else None

    def set_checkpoint(self, source_id: str, value: str, *, now: datetime) -> None:
        self.connection.execute(
            "INSERT INTO checkpoints(source_id,value,updated_at) VALUES(?,?,?) "
            "ON CONFLICT(source_id) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
            (source_id, value, now.astimezone(UTC).isoformat()),
        )
        self.connection.commit()

    def persist_collection(
        self, artifact: RawArtifact, events: list[InformationEvent]
    ) -> dict[str, int]:
        self.connection.execute(
            "INSERT OR IGNORE INTO raw_artifacts VALUES(?,?,?,?,?,?)",
            (
                artifact.sha256,
                artifact.source_id,
                artifact.uri,
                artifact.content_type,
                artifact.payload,
                artifact.observed_at.isoformat(),
            ),
        )
        inserted = 0
        for event in events:
            key = f"{event.source_id}:{event.source_event_id}"
            cursor = self.connection.execute(
                "INSERT OR IGNORE INTO information_events VALUES(?,?,?,?)",
                (key, event.source_id, event.model_dump_json(), event.observed_at.isoformat()),
            )
            inserted += cursor.rowcount
        self.connection.commit()
        return {"records_seen": len(events), "records_new": inserted}

    def counts(self) -> dict[str, int]:
        return {
            table: int(self.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in (
                "schedules",
                "executions",
                "leases",
                "incidents",
                "checkpoints",
                "raw_artifacts",
                "information_events",
                "service_runtime",
            )
        }

    def start_service(self, instance_id: str, pid: int, *, now: datetime) -> None:
        timestamp = now.astimezone(UTC).isoformat()
        self.connection.execute(
            "INSERT INTO service_runtime VALUES(?,?,?,?,?,NULL)",
            (instance_id, pid, timestamp, timestamp, "RUNNING"),
        )
        self.connection.commit()

    def heartbeat_service(self, instance_id: str, *, now: datetime) -> None:
        cursor = self.connection.execute(
            "UPDATE service_runtime SET heartbeat_at=? WHERE instance_id=? AND status='RUNNING'",
            (now.astimezone(UTC).isoformat(), instance_id),
        )
        if cursor.rowcount != 1:
            self.connection.rollback()
            raise RuntimeError("service runtime is not registered as running")
        self.connection.commit()

    def stop_service(self, instance_id: str, *, now: datetime) -> None:
        timestamp = now.astimezone(UTC).isoformat()
        self.connection.execute(
            "UPDATE service_runtime SET heartbeat_at=?,status='STOPPED',stopped_at=? "
            "WHERE instance_id=? AND status='RUNNING'",
            (timestamp, timestamp, instance_id),
        )
        self.connection.commit()

    def service_status(self, *, now: datetime, stale_after: timedelta) -> dict:
        row = self.connection.execute(
            "SELECT instance_id,pid,started_at,heartbeat_at,status,stopped_at "
            "FROM service_runtime ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return {"status": "NOT_STARTED"}
        heartbeat = datetime.fromisoformat(row["heartbeat_at"])
        status = row["status"]
        if status == "RUNNING" and now.astimezone(UTC) - heartbeat > stale_after:
            status = "STALE"
        return {
            "status": status,
            "instance_id": row["instance_id"],
            "pid": row["pid"],
            "started_at": row["started_at"],
            "heartbeat_at": row["heartbeat_at"],
            "stopped_at": row["stopped_at"],
        }

    def close(self) -> None:
        self.connection.close()

    @staticmethod
    def _job(row: sqlite3.Row) -> DurableJob:
        definition = json.loads(row["definition_json"])
        return DurableJob(
            row["name"],
            definition["kind"],
            definition.get("source_id"),
            definition.get("cadence_seconds"),
            definition.get("local_time"),
            definition.get("weekday"),
            datetime.fromisoformat(row["next_run_at"]),
            row["version"],
        )


def next_run_at(definition: dict, now: datetime) -> datetime:
    now = now.astimezone(UTC)
    if definition["kind"] == "INTERVAL":
        return now + timedelta(seconds=int(definition["cadence_seconds"]))
    local = now.astimezone(IST)
    hour, minute = map(int, definition["local_time"].split(":"))
    candidate = datetime.combine(local.date(), time(hour, minute), tzinfo=IST)
    if definition["kind"] == "WEEKLY":
        candidate += timedelta(days=(int(definition["weekday"]) - candidate.weekday()) % 7)
    if candidate <= local:
        candidate += timedelta(days=7 if definition["kind"] == "WEEKLY" else 1)
    return candidate.astimezone(UTC)
