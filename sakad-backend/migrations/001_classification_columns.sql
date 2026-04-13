-- Migration 001: Add classification columns to captures table
-- Run manually in Supabase SQL Editor.

ALTER TABLE captures ADD COLUMN IF NOT EXISTS tags jsonb;
ALTER TABLE captures ADD COLUMN IF NOT EXISTS taxonomy_matches jsonb;
ALTER TABLE captures ADD COLUMN IF NOT EXISTS layer1_tags jsonb;
ALTER TABLE captures ADD COLUMN IF NOT EXISTS layer2_tags jsonb;
ALTER TABLE captures ADD COLUMN IF NOT EXISTS layer3_tags jsonb;
ALTER TABLE captures ADD COLUMN IF NOT EXISTS layer4_tags jsonb;
