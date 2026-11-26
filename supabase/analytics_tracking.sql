-- ASTRO MOBILE analytics tracking
-- Applied to Supabase project exkhbenfbwrbqprtyqas on 2026-11-26.
-- Public client events are restricted by RLS; admin reads require the admin email.

create table if not exists public.astro_analytics_events (
  id bigint generated always as identity primary key,
  event_name text not null check (event_name in ('download_page_view','apk_download_click','app_first_open','account_created','order_created')),
  installation_id text,
  user_id uuid,
  source text not null default 'app',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists astro_analytics_events_created_at_idx
  on public.astro_analytics_events (created_at desc);
create index if not exists astro_analytics_events_name_created_idx
  on public.astro_analytics_events (event_name, created_at desc);
create unique index if not exists astro_analytics_first_open_once_idx
  on public.astro_analytics_events (installation_id)
  where event_name = 'app_first_open' and installation_id is not null;

alter table public.astro_analytics_events enable row level security;
revoke all on public.astro_analytics_events from anon, authenticated;
grant insert on public.astro_analytics_events to anon, authenticated;
grant usage, select on sequence public.astro_analytics_events_id_seq to anon, authenticated;
grant select on public.astro_analytics_events to authenticated;

drop policy if exists "public can record limited analytics events" on public.astro_analytics_events;
create policy "public can record limited analytics events"
on public.astro_analytics_events for insert to anon, authenticated
with check (
  event_name in ('download_page_view','apk_download_click','app_first_open')
  and (user_id is null or user_id = (select auth.uid()))
  and (installation_id is null or char_length(installation_id) between 8 and 100)
);

drop policy if exists "admin can read analytics" on public.astro_analytics_events;
create policy "admin can read analytics"
on public.astro_analytics_events for select to authenticated
using (lower(coalesce(auth.jwt() ->> 'email','')) = 'ahmedkabar.ak@gmail.com');

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create or replace function private.log_astro_account_created()
returns trigger language plpgsql security definer set search_path = ''
as $$
begin
  insert into public.astro_analytics_events(event_name,user_id,source,metadata)
  values ('account_created',new.id,'supabase_auth',jsonb_build_object('created_at',new.created_at));
  return new;
end;
$$;

drop trigger if exists astro_log_account_created on auth.users;
create trigger astro_log_account_created after insert on auth.users
for each row execute function private.log_astro_account_created();

create or replace function private.log_astro_order_created()
returns trigger language plpgsql security definer set search_path = ''
as $$
begin
  insert into public.astro_analytics_events(event_name,user_id,source,metadata)
  values ('order_created',new.customer_id,'orders',jsonb_build_object('order_id',new.id,'total_price',new.total_price));
  return new;
end;
$$;

drop trigger if exists astro_log_order_created on public.orders;
create trigger astro_log_order_created after insert on public.orders
for each row execute function private.log_astro_order_created();

-- Backfill pre-existing accounts and orders once, without creating duplicates.
insert into public.astro_analytics_events(event_name,user_id,source,metadata,created_at)
select 'account_created',u.id,'supabase_auth_backfill',jsonb_build_object('backfilled',true),u.created_at
from auth.users u
where not exists (select 1 from public.astro_analytics_events e where e.event_name='account_created' and e.user_id=u.id);

insert into public.astro_analytics_events(event_name,user_id,source,metadata,created_at)
select 'order_created',o.customer_id,'orders_backfill',
       jsonb_build_object('order_id',o.id,'total_price',o.total_price,'backfilled',true),o.created_at
from public.orders o
where not exists (select 1 from public.astro_analytics_events e where e.event_name='order_created' and e.metadata->>'order_id'=o.id::text);
