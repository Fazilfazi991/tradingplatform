begin;

create schema if not exists verified_edge;
revoke all on schema verified_edge from public;

create type verified_edge.quality_status as enum ('ACCEPTED','WARNING','QUARANTINED','REJECTED');
create type verified_edge.event_severity as enum ('INFO','WARNING','ERROR','CRITICAL');
create type verified_edge.source_category as enum ('MARKET','NEWS','CORPORATE','FUNDAMENTAL','MACRO','SENTIMENT','FLOW','DERIVATIVES','ALTERNATIVE');

create table verified_edge.providers (
 id uuid primary key, name text not null, environment text not null, provider_type text not null,
 terms_version text, entitlement_metadata jsonb not null default '{}', active boolean not null default true,
 created_at timestamptz not null default now(), unique(name, environment)
);
create table verified_edge.instruments (
 id uuid primary key, exchange text not null, segment text not null, symbol text not null,
 company_name text, isin text, instrument_type text not null, tick_size numeric check(tick_size >= 0),
 listing_status text not null, valid_from date, valid_to date,
 check(valid_to is null or valid_from is null or valid_to >= valid_from),
 unique(exchange,segment,symbol,valid_from)
);
create table verified_edge.instrument_provider_ids (
 instrument_id uuid not null references verified_edge.instruments(id),
 provider_id uuid not null references verified_edge.providers(id), provider_instrument_key text not null,
 valid_from date not null, valid_to date,
 primary key(provider_id,provider_instrument_key,valid_from),
 unique(instrument_id,provider_id,valid_from), check(valid_to is null or valid_to >= valid_from)
);
create table verified_edge.indices (
 code text primary key, name text not null, exchange text not null, provider_mapping jsonb not null default '{}'
);
create table verified_edge.index_memberships (
 index_code text not null references verified_edge.indices(code), instrument_id uuid not null references verified_edge.instruments(id),
 effective_from date not null, effective_to date, source text not null, source_version text not null,
 primary key(index_code,instrument_id,effective_from), check(effective_to is null or effective_to >= effective_from)
);
create table verified_edge.trading_calendar (
 exchange text not null, session_date date not null, open_at timestamptz, close_at timestamptz,
 session_type text not null, source_version text not null, primary key(exchange,session_date),
 check(close_at is null or open_at is null or close_at > open_at)
);
create table verified_edge.ingestion_runs (
 id uuid primary key, provider_id uuid not null references verified_edge.providers(id), job_type text not null,
 requested_start date, requested_end date, started_at timestamptz not null, completed_at timestamptz,
 status text not null, requested_symbols jsonb not null default '[]', received_rows bigint not null default 0,
 accepted_rows bigint not null default 0, quarantined_rows bigint not null default 0, error_count bigint not null default 0,
 config_hash text not null, code_sha text not null
);
create table verified_edge.market_observations_raw (
 id uuid primary key, provider_id uuid not null references verified_edge.providers(id),
 instrument_id uuid not null references verified_edge.instruments(id), observation_type text not null,
 interval text not null, session_date date not null, observed_at timestamptz not null,
 source_timestamp timestamptz not null, raw_payload jsonb not null, payload_hash text not null,
 ingested_at timestamptz not null default now(), ingestion_run_id uuid not null references verified_edge.ingestion_runs(id),
 unique(provider_id,instrument_id,observation_type,interval,session_date,payload_hash)
);
create index market_raw_lookup on verified_edge.market_observations_raw(instrument_id,session_date);
create table verified_edge.daily_bars_canonical (
 instrument_id uuid not null references verified_edge.instruments(id), session_date date not null,
 canonical_version integer not null check(canonical_version > 0), open numeric not null check(open >= 0),
 high numeric not null check(high >= 0), low numeric not null check(low >= 0), close numeric not null check(close >= 0),
 volume bigint not null check(volume >= 0), oi bigint check(oi >= 0),
 source_raw_observation_id uuid not null references verified_edge.market_observations_raw(id),
 transformation_hash text not null, quality_status verified_edge.quality_status not null,
 created_at timestamptz not null default now(), primary key(instrument_id,session_date,canonical_version),
 check(high >= open and high >= close and low <= open and low <= close and high >= low)
);
create table verified_edge.corporate_actions (
 id uuid primary key, instrument_id uuid not null references verified_edge.instruments(id), action_type text not null,
 announcement_date date, ex_date date, record_date date, effective_date date, ratio numeric, cash_amount numeric,
 currency char(3), source text not null, source_version text not null, quality_status verified_edge.quality_status not null
);
create table verified_edge.adjustment_factors (
 instrument_id uuid not null references verified_edge.instruments(id), session_date date not null,
 price_factor numeric not null check(price_factor > 0), volume_factor numeric not null check(volume_factor > 0),
 corporate_action_id uuid references verified_edge.corporate_actions(id), version integer not null check(version > 0),
 primary key(instrument_id,session_date,version)
);
create table verified_edge.data_quality_events (
 id uuid primary key, severity verified_edge.event_severity not null, check_code text not null,
 instrument_id uuid references verified_edge.instruments(id), session_date date, observed jsonb, expected jsonb,
 status text not null, ingestion_run_id uuid references verified_edge.ingestion_runs(id), opened_at timestamptz not null default now(),
 resolved_at timestamptz, resolution text
);
create index quality_open_incidents on verified_edge.data_quality_events(severity,status) where status='OPEN';
create table verified_edge.quarantined_observations (
 raw_observation_id uuid primary key references verified_edge.market_observations_raw(id),
 check_code text not null, severity verified_edge.event_severity not null, review_status text not null default 'PENDING',
 reason text not null, resolution text, reviewed_at timestamptz
);
create table verified_edge.data_sources (
 id uuid primary key, name text not null, category verified_edge.source_category not null, source_version text not null,
 terms_version text, entitlement_metadata jsonb not null default '{}', active boolean not null default true,
 unique(name,source_version)
);
create table verified_edge.information_events (
 id uuid primary key, entity_id uuid not null, event_type text not null, source_id uuid not null references verified_edge.data_sources(id),
 event_time timestamptz not null, published_at timestamptz not null, observed_at timestamptz not null,
 available_at timestamptz not null, effective_at timestamptz, raw_artifact_uri text not null,
 normalized_payload jsonb not null, quality_status verified_edge.quality_status not null,
 source_version text not null, created_at timestamptz not null default now(),
 check(available_at >= published_at), check(observed_at >= published_at)
);
create index information_time_lookup on verified_edge.information_events(entity_id,available_at);
create table verified_edge.datasets (
 id uuid primary key, name text not null, purpose text not null, universe_version text not null,
 start_date date, end_date date, manifest_uri text not null, sha256 text not null unique,
 created_at timestamptz not null default now(), sealed_at timestamptz, parent_dataset_id uuid references verified_edge.datasets(id),
 check(end_date is null or start_date is null or end_date >= start_date)
);
create table verified_edge.dataset_partitions (
 dataset_id uuid not null references verified_edge.datasets(id), file_uri text not null, file_sha256 text not null,
 row_count bigint not null check(row_count >= 0), canonical_selector jsonb not null,
 primary key(dataset_id,file_uri)
);

create function verified_edge.prevent_mutation() returns trigger language plpgsql as $$
begin raise exception '% is append-only', tg_table_name; end $$;
create trigger raw_append_only before update or delete on verified_edge.market_observations_raw
for each row execute function verified_edge.prevent_mutation();
create trigger canonical_append_only before update or delete on verified_edge.daily_bars_canonical
for each row execute function verified_edge.prevent_mutation();
create trigger information_events_append_only before update or delete on verified_edge.information_events
for each row execute function verified_edge.prevent_mutation();
create function verified_edge.prevent_sealed_dataset_mutation() returns trigger language plpgsql as $$
begin if old.sealed_at is not null then raise exception 'sealed dataset cannot mutate'; end if; return new; end $$;
create trigger sealed_dataset_immutable before update or delete on verified_edge.datasets
for each row execute function verified_edge.prevent_sealed_dataset_mutation();

revoke all on all tables in schema verified_edge from anon, authenticated, public;
revoke all on all sequences in schema verified_edge from anon, authenticated, public;
revoke execute on all functions in schema verified_edge from public, anon, authenticated;

commit;

