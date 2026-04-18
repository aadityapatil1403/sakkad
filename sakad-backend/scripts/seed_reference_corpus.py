"""Seed the curated designer reference corpus into Supabase with SigLIP text embeddings.

Canonical source: data/reference_corpus.json at repo root.
Contract:
- table: reference_corpus
- upsert key: id
- embedding: JSON array of normalized floats returned by get_text_embedding()
"""

import argparse
import json
import sys
from pathlib import Path

# Allow imports from sakad-backend root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from services.clip_service import get_text_embedding  # noqa: E402
from services.supabase_client import supabase  # noqa: E402

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "reference_corpus.json"
TABLE_NAME = "reference_corpus"
REQUIRED_FIELDS = (
    "id",
    "designer",
    "brand",
    "collection_or_era",
    "title",
    "description",
    "taxonomy_tags",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed the curated designer reference corpus into Supabase.",
    )
    parser.add_argument(
        "--keep-stale",
        action="store_true",
        help="Keep live reference rows whose ids are not present in data/reference_corpus.json.",
    )
    return parser.parse_args()


def load_entries() -> list[dict]:
    entries = json.loads(DATA_PATH.read_text())
    if not isinstance(entries, list) or not entries:
        raise ValueError("data/reference_corpus.json must contain a non-empty JSON array.")

    for index, entry in enumerate(entries, start=1):
        validate_entry(entry, index)
    return entries


def validate_entry(entry: dict, index: int) -> None:
    missing_fields = [field for field in REQUIRED_FIELDS if field not in entry]
    if missing_fields:
        raise ValueError(
            f"reference_corpus.json entry {index} is missing required field(s): "
            f"{', '.join(missing_fields)}"
        )
    if not isinstance(entry["taxonomy_tags"], list) or not entry["taxonomy_tags"]:
        raise ValueError(
            f"reference_corpus.json entry {index} must provide a non-empty taxonomy_tags list."
        )
    for field in REQUIRED_FIELDS[:-1]:
        value = entry[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"reference_corpus.json entry {index} field '{field}' must be a non-empty string."
            )


def fetch_existing_rows() -> dict[str, dict]:
    response = supabase.table(TABLE_NAME).select("id").execute()
    rows = response.data or []
    return {row["id"]: row for row in rows if isinstance(row, dict) and row.get("id")}


def delete_stale_rows(existing_rows: dict[str, dict], canonical_ids: set[str]) -> int:
    stale_ids = sorted(set(existing_rows) - canonical_ids)
    for row_id in stale_ids:
        print(f"Deleting stale reference row: {row_id}", flush=True)
        supabase.table(TABLE_NAME).delete().eq("id", row_id).execute()
    return len(stale_ids)


def build_embedding_text(entry: dict) -> str:
    tags = ", ".join(entry["taxonomy_tags"])
    return (
        f"Designer: {entry['designer']}\n"
        f"Brand: {entry['brand']}\n"
        f"Collection or era: {entry['collection_or_era']}\n"
        f"Title: {entry['title']}\n"
        f"Description: {entry['description']}\n"
        f"Tags: {tags}"
    )


def build_row(entry: dict) -> dict:
    return {
        "id": entry["id"],
        "designer": entry["designer"],
        "brand": entry["brand"],
        "collection_or_era": entry["collection_or_era"],
        "title": entry["title"],
        "description": entry["description"],
        "taxonomy_tags": entry["taxonomy_tags"],
        "image_url": entry.get("image_url"),
        "embedding": get_text_embedding(build_embedding_text(entry)),
        "metadata": entry.get("metadata", {}),
    }


def main() -> None:
    args = parse_args()
    entries = load_entries()
    total = len(entries)
    success_count = 0

    existing_rows = fetch_existing_rows()
    canonical_ids = {entry["id"] for entry in entries}
    deleted_count = 0
    if not args.keep_stale:
        deleted_count = delete_stale_rows(existing_rows, canonical_ids)

    for index, entry in enumerate(entries, start=1):
        print(f"Seeding {index}/{total}: {entry['title']}...", flush=True)
        row = build_row(entry)
        response = supabase.table(TABLE_NAME).upsert(row, on_conflict="id").execute()
        if response.data:
            success_count += 1
        else:
            print(f"  WARNING: upsert returned no data for '{entry['id']}'", flush=True)

    print(
        f"\nDone. {success_count}/{total} rows successfully upserted."
        f" Deleted {deleted_count} stale rows."
    )


if __name__ == "__main__":
    main()
