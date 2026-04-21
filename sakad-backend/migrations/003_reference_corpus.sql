-- Migration 003: Add the curated designer reference corpus table.
-- Run manually in Supabase SQL Editor.

CREATE TABLE IF NOT EXISTS reference_corpus (
    id uuid PRIMARY KEY,
    designer text NOT NULL,
    brand text NOT NULL,
    collection_or_era text NOT NULL,
    title text NOT NULL,
    description text NOT NULL,
    taxonomy_tags jsonb NOT NULL DEFAULT '[]'::jsonb,
    image_url text,
    embedding jsonb NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS reference_corpus_designer_idx
    ON reference_corpus (designer);

CREATE INDEX IF NOT EXISTS reference_corpus_brand_idx
    ON reference_corpus (brand);
