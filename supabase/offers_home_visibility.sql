-- ASTRO MOBILE: per-offer home page visibility.
-- Existing offers remain visible on the home page by default.
ALTER TABLE public.offers
  ADD COLUMN IF NOT EXISTS show_on_home boolean NOT NULL DEFAULT true;

COMMENT ON COLUMN public.offers.show_on_home IS
  'Whether this offer is featured on the app home page; all active offers remain available in the dedicated offers section.';
