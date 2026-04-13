# Migrations

Run files in order by numeric prefix in the **Supabase SQL Editor**.

Never auto-run these from application code.

## Files

- `001_classification_columns.sql` — adds nullable JSONB classification columns to `captures` for the 4-layer taxonomy pipeline (`tags`, `taxonomy_matches`, `layer1_tags`–`layer4_tags`)
