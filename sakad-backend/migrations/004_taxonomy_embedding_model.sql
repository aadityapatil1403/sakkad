-- Migration 004: Track the embedding model used for taxonomy vectors.
-- Run manually in Supabase SQL Editor before re-seeding taxonomy.

ALTER TABLE taxonomy
    ADD COLUMN IF NOT EXISTS embedding_model text;
