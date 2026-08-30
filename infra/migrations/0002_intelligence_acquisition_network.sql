BEGIN;

SET LOCAL search_path TO verified_edge, public;

CREATE TABLE intelligence_sources (
  source_id text PRIMARY KEY,
  name text NOT NULL,
  source_category text NOT NULL,
  provider text NOT NULL,
  base_url text NOT NULL,
  access_method text NOT NULL,
  official_status boolean NOT NULL,
  entitlement_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  reliability_tier text NOT NULL,
  predictive_status text NOT NULL DEFAULT 'UNKNOWN',
  collector_version text NOT NULL,
  parser_version text NOT NULL,
  active boolean NOT NULL DEFAULT false,
  last_success_at timestamptz,
  last_failure_at timestamptz,
  health_status text NOT NULL DEFAULT 'UNKNOWN',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE information_events (
  event_id uuid PRIMARY KEY,
  entity_id uuid,
  entity_type text NOT NULL,
  source_id text NOT NULL REFERENCES intelligence_sources(source_id),
  source_event_id text,
  event_type text NOT NULL,
  event_subtype text,
  title text NOT NULL,
  summary text NOT NULL,
  raw_artifact_uri text NOT NULL,
  raw_payload_hash text NOT NULL,
  event_time timestamptz NOT NULL,
  published_at timestamptz NOT NULL,
  observed_at timestamptz NOT NULL,
  available_at timestamptz NOT NULL,
  ingested_at timestamptz NOT NULL,
  effective_at timestamptz,
  source_version text NOT NULL,
  collector_version text NOT NULL,
  parser_version text NOT NULL,
  language text NOT NULL,
  importance text NOT NULL,
  quality_status text NOT NULL,
  duplicate_group_id text,
  correction_of uuid REFERENCES information_events(event_id),
  supersedes uuid REFERENCES information_events(event_id),
  metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (source_id, source_event_id, raw_payload_hash)
);

CREATE TABLE intelligence_job_ledger (
  job_id uuid PRIMARY KEY,
  source_id text NOT NULL REFERENCES intelligence_sources(source_id),
  mode text NOT NULL,
  scheduled_for timestamptz NOT NULL,
  started_at timestamptz NOT NULL,
  ended_at timestamptz NOT NULL,
  status text NOT NULL,
  records_seen integer NOT NULL DEFAULT 0,
  records_new integer NOT NULL DEFAULT 0,
  records_duplicate integer NOT NULL DEFAULT 0,
  records_failed integer NOT NULL DEFAULT 0,
  raw_artifacts integer NOT NULL DEFAULT 0,
  canonical_events integer NOT NULL DEFAULT 0,
  retry_count integer NOT NULL DEFAULT 0,
  error_summary text,
  collector_version text NOT NULL,
  code_sha text NOT NULL
);

CREATE TABLE source_candidates (
  candidate_id uuid PRIMARY KEY,
  name text NOT NULL,
  category text NOT NULL,
  discovered_by text NOT NULL,
  discovered_at timestamptz NOT NULL,
  official_url text NOT NULL,
  access_method text NOT NULL,
  potential_value text NOT NULL,
  legal_status text NOT NULL,
  technical_status text NOT NULL,
  cost text NOT NULL,
  priority integer NOT NULL,
  review_status text NOT NULL,
  decision text,
  reason text
);

CREATE INDEX information_events_causal_idx ON information_events(entity_id, available_at);
CREATE INDEX information_events_source_idx ON information_events(source_id, source_event_id);

COMMIT;
