import json
from pathlib import Path
from uuid import UUID


REFERENCE_CORPUS_PATH = Path(__file__).resolve().parents[2] / "data" / "reference_corpus.json"
REQUIRED_FIELDS = {
    "id",
    "designer",
    "brand",
    "collection_or_era",
    "title",
    "description",
    "taxonomy_tags",
}
REQUIRED_BUCKETS = {
    "western_americana",
    "workwear_utility",
    "biker_moto",
    "japanese_streetwear",
    "minimalism_tailoring",
    "avant_garde",
    "soccer_streetwear",
}


def load_reference_corpus() -> list[dict]:
    return json.loads(REFERENCE_CORPUS_PATH.read_text())


def test_reference_corpus_is_large_curated_non_empty() -> None:
    entries = load_reference_corpus()

    assert len(entries) >= 50


def test_reference_corpus_entries_have_required_fields() -> None:
    entries = load_reference_corpus()

    for entry in entries:
        assert REQUIRED_FIELDS.issubset(entry)
        assert isinstance(entry["taxonomy_tags"], list)
        assert entry["taxonomy_tags"]
        for field in REQUIRED_FIELDS - {"taxonomy_tags"}:
            assert isinstance(entry[field], str)
            assert entry[field].strip()


def test_reference_corpus_ids_are_unique() -> None:
    entries = load_reference_corpus()
    ids = [entry["id"] for entry in entries]

    assert len(ids) == len(set(ids))
    for row_id in ids:
        assert str(UUID(row_id)) == row_id


def test_reference_corpus_covers_requested_buckets_with_metadata() -> None:
    entries = load_reference_corpus()
    bucket_counts: dict[str, int] = {bucket: 0 for bucket in REQUIRED_BUCKETS}

    for entry in entries:
        metadata = entry.get("metadata", {})
        assert isinstance(metadata, dict)
        bucket = metadata.get("bucket")
        assert bucket in REQUIRED_BUCKETS
        bucket_counts[bucket] += 1

    for bucket in REQUIRED_BUCKETS:
        assert bucket_counts[bucket] >= 8
