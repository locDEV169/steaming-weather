-- Append-only history for Lifestyle & Context-aware Insights.
-- Each ingest inserts a new row. Rows are not updated.

create table if not exists public.lifestyle_insights (
  id bigint generated always as identity primary key,
  location_key text not null default 'da_nang',
  payload jsonb not null,
  fetched_at timestamptz not null,
  created_at timestamptz not null default now()
);

comment on table public.lifestyle_insights is
  'History of Dự báo theo ngữ cảnh hành vi (Lifestyle & Context-aware Insights). Append-only.';

create index if not exists lifestyle_insights_location_fetched_at_idx
  on public.lifestyle_insights (location_key, fetched_at desc);

alter table public.lifestyle_insights enable row level security;

drop policy if exists "Allow anon read lifestyle_insights"
  on public.lifestyle_insights;
create policy "Allow anon read lifestyle_insights"
  on public.lifestyle_insights
  for select
  to anon, authenticated
  using (true);

grant select on public.lifestyle_insights to anon, authenticated;
grant all on public.lifestyle_insights to service_role;
grant usage, select on sequence public.lifestyle_insights_id_seq to service_role;
