from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg


def main() -> None:
    database_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if not database_url:
        raise SystemExit("BLOCKED: DATABASE_URL or SUPABASE_DB_URL is absent")
    migration_paths = sorted(Path("infra/migrations").glob("000[1-3]_*.sql"))
    with psycopg.connect(database_url) as connection:
        for path in migration_paths:
            connection.execute(path.read_text(encoding="utf-8"))
        tables = connection.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='verified_edge' ORDER BY tablename"
        ).fetchall()
        constraints = connection.execute(
            "SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace "
            "WHERE n.nspname='verified_edge'"
        ).fetchone()[0]
        triggers = connection.execute(
            "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
            "JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='verified_edge' AND NOT t.tgisinternal"
        ).fetchone()[0]
    print(
        json.dumps(
            {
                "status": "PASS",
                "migrations": [path.name for path in migration_paths],
                "verified_edge_tables": len(tables),
                "constraints": constraints,
                "triggers": triggers,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
