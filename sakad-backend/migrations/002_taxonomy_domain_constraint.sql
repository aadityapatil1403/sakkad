-- Migration 002: Legacy taxonomy domain broadening for a previously mixed-domain taxonomy
-- Run manually in Supabase SQL Editor before re-seeding taxonomy.
--
-- Background: original constraint only allowed 'fashion' and 'art'.
-- The current canonical taxonomy is fashion-only again, but this broader constraint remains
-- backward-compatible with older seeded data and does not block current re-seeds.

ALTER TABLE taxonomy DROP CONSTRAINT IF EXISTS taxonomy_domain_check;

ALTER TABLE taxonomy ADD CONSTRAINT taxonomy_domain_check
    CHECK (domain IN ('fashion_streetwear', 'art_reference', 'visual_context'));
