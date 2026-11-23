-- ASTRO MOBILE: weekly offers containing multiple independently priced products
ALTER TABLE public.offers
  DROP CONSTRAINT IF EXISTS offers_offer_type_check;
ALTER TABLE public.offers
  ADD CONSTRAINT offers_offer_type_check
  CHECK (offer_type = ANY (ARRAY['product'::text, 'category'::text, 'bundle'::text, 'multi_product'::text]));

ALTER TABLE public.offer_items
  ADD COLUMN IF NOT EXISTS offer_price numeric;

ALTER TABLE public.offer_items
  DROP CONSTRAINT IF EXISTS offer_items_offer_price_check;
ALTER TABLE public.offer_items
  ADD CONSTRAINT offer_items_offer_price_check
  CHECK (offer_price IS NULL OR offer_price >= 0);

ALTER TABLE public.order_items
  DROP CONSTRAINT IF EXISTS order_items_offer_type_check;
ALTER TABLE public.order_items
  ADD CONSTRAINT order_items_offer_type_check
  CHECK (offer_type IS NULL OR offer_type = ANY (ARRAY['product'::text, 'category'::text, 'bundle'::text, 'multi_product'::text));
