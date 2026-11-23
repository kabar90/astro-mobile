-- ASTRO MOBILE: multiple independently priced products using the existing product offer type.
-- The migration is applied to the live database; this file documents the corrected schema.

ALTER TABLE public.offers
  DROP CONSTRAINT IF EXISTS offers_offer_type_check;
ALTER TABLE public.offers
  ADD CONSTRAINT offers_offer_type_check
  CHECK (offer_type = ANY (ARRAY['product'::text, 'category'::text, 'bundle'::text]));

ALTER TABLE public.order_items
  DROP CONSTRAINT IF EXISTS order_items_offer_type_check;
ALTER TABLE public.order_items
  ADD CONSTRAINT order_items_offer_type_check
  CHECK (offer_type IS NULL OR offer_type = ANY (ARRAY['product'::text, 'category'::text, 'bundle'::text]));

ALTER TABLE public.offers
  DROP CONSTRAINT IF EXISTS offers_product_shape;
ALTER TABLE public.offers
  ADD CONSTRAINT offers_product_shape
  CHECK (
    (offer_type = 'product' AND category_name IS NULL AND bundle_price IS NULL
      AND (
        (product_id IS NOT NULL AND discount_type IS NOT NULL AND discount_value IS NOT NULL
          AND discount_value > 0
          AND ((discount_type = 'percentage' AND discount_value < 100) OR discount_type = 'fixed_price'))
        OR (product_id IS NULL AND discount_type IS NULL AND discount_value IS NULL)
      ))
    OR
    (offer_type = 'category' AND product_id IS NULL AND category_name IS NOT NULL
      AND length(trim(category_name)) > 0 AND discount_type IS NOT NULL
      AND discount_value IS NOT NULL AND discount_value > 0
      AND ((discount_type = 'percentage' AND discount_value < 100) OR discount_type = 'fixed_price')
      AND bundle_price IS NULL)
    OR
    (offer_type = 'bundle' AND product_id IS NULL AND category_name IS NULL
      AND discount_type IS NULL AND discount_value IS NULL
      AND bundle_price IS NOT NULL AND bundle_price >= 0)
  );

ALTER TABLE public.offer_items
  ADD COLUMN IF NOT EXISTS offer_price numeric;
ALTER TABLE public.offer_items
  DROP CONSTRAINT IF EXISTS offer_items_offer_price_check;
ALTER TABLE public.offer_items
  ADD CONSTRAINT offer_items_offer_price_check
  CHECK (offer_price IS NULL OR offer_price > 0);
