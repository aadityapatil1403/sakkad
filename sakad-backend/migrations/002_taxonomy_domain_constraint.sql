-- Migration 002: Update taxonomy domain constraint to allow 3-tier domains
-- Run manually in Supabase SQL Editor before re-seeding taxonomy.
--
-- Background: original constraint only allowed 'fashion' and 'art'.
-- taxonomy.json now uses 3 domains: fashion_streetwear, art_reference, visual_context.

ALTER TABLE taxonomy DROP CONSTRAINT IF EXISTS taxonomy_domain_check;

ALTER TABLE taxonomy ADD CONSTRAINT taxonomy_domain_check
    CHECK (domain IN ('fashion_streetwear', 'art_reference', 'visual_context'));
