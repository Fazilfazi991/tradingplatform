-- Durable operational state for autonomous internal intelligence collection.
BEGIN;

SET LOCAL search_path TO verified_edge, public;
CREATE TABLE IF NOT EXISTS intelligence_schedules (
    name text PRIMARY KEY,
    definition jsonb NOT NULL,
    version text NOT NULL,
    next_run_at timestamptz NOT NULL,
    last_run_at timestamptz,
    enabled boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS intelligence_job_executions (
    execution_key text PRIMARY KEY,
    job_name text NOT NULL REFERENCES intelligence_schedules(name),
    scheduled_for timestamptz NOT NULL,
    started_at timestamptz NOT NULL,
    ended_at timestamptz,
    status text NOT NULL,
    result jsonb
);

CREATE TABLE IF NOT EXISTS intelligence_job_leases (
    job_name text PRIMARY KEY REFERENCES intelligence_schedules(name),
    owner text NOT NULL,
    acquired_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS intelligence_incidents (
    incident_id uuid PRIMARY KEY,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS intelligence_raw_artifacts (
    sha256 text PRIMARY KEY,
    source_id text NOT NULL,
    uri text NOT NULL,
    content_type text NOT NULL,
    payload bytea NOT NULL,
    observed_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS intelligence_events (
    event_key text PRIMARY KEY,
    source_id text NOT NULL,
    payload jsonb NOT NULL,
    observed_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS intelligence_executions_job_started_idx
    ON intelligence_job_executions (job_name, started_at DESC);
CREATE INDEX IF NOT EXISTS intelligence_events_source_observed_idx
    ON intelligence_events (source_id, observed_at DESC);

COMMIT;
