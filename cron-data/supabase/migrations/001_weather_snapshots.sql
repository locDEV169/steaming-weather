-- Latest-only weather snapshots for FE / ingest (no-cron MVP).
-- Apply in Supabase SQL Editor or via CLI.
create table if not exists public.weather_snapshots (
  location_key text not null default 'da_nang',
  kind text not null check (kind in ('weather', 'rainny', 'air_quality')),
  payload jsonb not null,
  fetched_at timestamptz not null,
  updated_at timestamptz not null default now (),
  primary key (location_key, kind)
);

comment on table public.weather_snapshots is 'Shaped Open-Meteo snapshots (weather, rainny, air_quality) keyed by location_key (e.g. da_nang, sai_gon).';

alter table public.weather_snapshots enable row level security;

-- Public read for FE anon key; writes only via service_role (bypasses RLS).
drop policy if exists "Allow anon read weather_snapshots" on public.weather_snapshots;

create policy "Allow anon read weather_snapshots" on public.weather_snapshots for
select
  to anon,
  authenticated using (true);

grant
select
  on public.weather_snapshots to anon,
  authenticated;
