-- Append-only history for Open-Meteo current weather (and optional WMO evaluation).
-- Each ingest inserts a new row. Rows are not updated.
-- Apply in Supabase SQL Editor or via: python scripts/migrate.py supabase/migrations/003_current_weather.sql
-- If an older latest-only table already exists, drop and recreate:
-- Drop the existing table if it exists.
-- drop table if exists public.current_weather;
create table public.current_weather (
  id bigint generated always as identity primary key,
  location_key text not null default 'da_nang',
  payload jsonb not null,
  fetched_at timestamptz not null,
  created_at timestamptz not null default now ()
);

comment on table public.current_weather is 'History of Open-Meteo current weather payloads (and optional WMO evaluation). Append-only.';

create index if not exists current_weather_location_fetched_at_idx on public.current_weather (location_key, fetched_at desc);

alter table public.current_weather enable row level security;

drop policy if exists "Allow anon read current_weather" on public.current_weather;

create policy "Allow anon read current_weather" on public.current_weather for
select
  to anon,
  authenticated using (true);

grant
select
  on public.current_weather to anon,
  authenticated;

grant all on public.current_weather to service_role;

grant usage,
select
  on sequence public.current_weather_id_seq to service_role;
