-- Migration 005: Add retrieval/session enrichment columns to captures
-- Run manually in Supabase SQL Editor.

ALTER TABLE captures ADD COLUMN IF NOT EXISTS session_id uuid;
ALTER TABLE captures ADD COLUMN IF NOT EXISTS reference_matches jsonb;
ALTER TABLE captures ADD COLUMN IF NOT EXISTS reference_explanation text;

ALTER TABLE captures DROP CONSTRAINT IF EXISTS captures_session_id_fkey;

ALTER TABLE captures
    ADD CONSTRAINT captures_session_id_fkey
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL;
