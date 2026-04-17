# Canonical taxonomy source: data/taxonomy.json at repo root
"""Seed taxonomy.json entries into the Supabase taxonomy table with SigLIP text embeddings."""

import argparse
import json
import sys
import uuid
from pathlib import Path

# Allow imports from sakad-backend root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from services.clip_service import get_text_embedding  # noqa: E402
from services.supabase_client import supabase  # noqa: E402

TAXONOMY_PATH = Path(__file__).parent.parent.parent / "data" / "taxonomy.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed the canonical taxonomy into Supabase.",
    )
    parser.add_argument(
        "--keep-stale",
        action="store_true",
        help="Keep live taxonomy labels that are not present in data/taxonomy.json.",
    )
    return parser.parse_args()


def load_entries() -> list[dict]:
    return json.loads(TAXONOMY_PATH.read_text())


def fetch_existing_rows() -> dict[str, dict]:
    response = supabase.table("taxonomy").select("id, label").execute()
    rows = response.data or []
    return {
        row["label"]: row
        for row in rows
        if isinstance(row, dict) and row.get("label") and row.get("id")
    }


def delete_stale_rows(existing_rows: dict[str, dict], canonical_labels: set[str]) -> int:
    stale_labels = sorted(set(existing_rows) - canonical_labels)
    for label in stale_labels:
        print(f"Deleting stale taxonomy row: {label}", flush=True)
        supabase.table("taxonomy").delete().eq("label", label).execute()
    return len(stale_labels)


def build_row(entry: dict, existing_id: str | None) -> dict:
    label = entry["label"]
    description = entry["description"]
    text = f"{label}: {description}"
    embedding = get_text_embedding(text)
    return {
        "id": existing_id or str(uuid.uuid4()),
        "label": label,
        "domain": entry["domain"],
        "description": description,
        "embedding": embedding,
        "related_references": entry.get("visual_references", []),
    }


def main() -> None:
    args = parse_args()
    entries = load_entries()
    total = len(entries)
    success_count = 0

    existing_rows = fetch_existing_rows()
    canonical_labels = {entry["label"] for entry in entries}
    deleted_count = 0
    if not args.keep_stale:
        deleted_count = delete_stale_rows(existing_rows, canonical_labels)
        existing_rows = {
            label: row for label, row in existing_rows.items() if label in canonical_labels
        }

    for i, entry in enumerate(entries, start=1):
        label = entry["label"]
        print(f"Seeding {i}/{total}: {label}...", flush=True)

        existing_id = existing_rows.get(label, {}).get("id")
        row = build_row(entry, existing_id=existing_id)

        resp = supabase.table("taxonomy").upsert(row, on_conflict="label").execute()
        if resp.data:
            success_count += 1
        else:
            print(f"  WARNING: upsert returned no data for '{label}'", flush=True)

    print(
        f"\nDone. {success_count}/{total} rows successfully upserted."
        f" Deleted {deleted_count} stale rows."
    )


if __name__ == "__main__":
    main()
