# Canonical taxonomy source: data/taxonomy.json at repo root
"""Seed taxonomy.json entries into the Supabase taxonomy table with SigLIP text embeddings."""

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


def main() -> None:
    entries = json.loads(TAXONOMY_PATH.read_text())
    total = len(entries)
    success_count = 0

    for i, entry in enumerate(entries, start=1):
        label = entry["label"]
        description = entry["description"]
        text = f"{label}: {description}"

        print(f"Seeding {i}/{total}: {label}...", flush=True)

        embedding = get_text_embedding(text)

        row = {
            "id": str(uuid.uuid4()),
            "label": label,
            "domain": entry["domain"],
            "description": description,
            "embedding": embedding,
            "related_references": entry.get("visual_references", []),
        }

        resp = supabase.table("taxonomy").upsert(row, on_conflict="label").execute()
        if resp.data:
            success_count += 1
        else:
            print(f"  WARNING: upsert returned no data for '{label}'", flush=True)

    print(f"\nDone. {success_count}/{total} rows successfully upserted.")


if __name__ == "__main__":
    main()
