-- ASTRO MOBILE: category images and product display settings.
-- Run once in Supabase SQL Editor. Existing category data is preserved.

alter table public.categories
  add column if not exists image_url text;

create table if not exists public.store_display_settings (
  id integer primary key default 1 check (id = 1),
  product_layout text not null default 'grid'
    check (product_layout in ('grid', 'list')),
  grid_columns integer not null default 2
    check (grid_columns in (2, 3)),
  allow_customer_toggle boolean not null default true,
  updated_at timestamptz not null default now()
);

insert into public.store_display_settings
  (id, product_layout, grid_columns, allow_customer_toggle)
values (1, 'grid', 2, true)
on conflict (id) do nothing;

alter table public.store_display_settings enable row level security;

drop policy if exists "store display settings are readable"
  on public.store_display_settings;
create policy "store display settings are readable"
  on public.store_display_settings for select
  using (true);

drop policy if exists "admin manages store display settings"
  on public.store_display_settings;
create policy "admin manages store display settings"
  on public.store_display_settings for all
  to authenticated
  using (lower(coalesce(auth.jwt() ->> 'email', '')) = 'ahmedkabar.ak@gmail.com')
  with check (lower(coalesce(auth.jwt() ->> 'email', '')) = 'ahmedkabar.ak@gmail.com');

grant select on public.store_display_settings to anon, authenticated;
grant insert, update, delete on public.store_display_settings to authenticated;

do $$
begin
  alter publication supabase_realtime add table public.store_display_settings;
exception
  when duplicate_object then null;
  when undefined_object then null;
end $$;
