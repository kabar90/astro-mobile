-- ASTRO MOBILE: store an individual Libyan-dinar price for each inquiry reply image.
-- Safe additive migration: keeps admin_image_urls for backward compatibility.
alter table public.product_inquiries
  add column if not exists admin_image_items jsonb not null default '[]'::jsonb;

alter table public.product_inquiries
  drop constraint if exists product_inquiries_admin_image_items_array_check;

alter table public.product_inquiries
  add constraint product_inquiries_admin_image_items_array_check
  check (
    jsonb_typeof(admin_image_items) = 'array'
    and not exists (
      select 1
      from jsonb_array_elements(admin_image_items) as item
      where jsonb_typeof(item) <> 'object'
         or not (item ? 'url')
         or not (item ? 'price')
         or jsonb_typeof(item->'url') <> 'string'
         or jsonb_typeof(item->'price') not in ('number', 'null')
         or (jsonb_typeof(item->'price') = 'number' and (item->>'price')::numeric < 0)
    )
  );
