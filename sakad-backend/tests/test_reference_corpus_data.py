import json
from pathlib import Path


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


def load_reference_corpus() -> list[dict]:
    return json.loads(REFERENCE_CORPUS_PATH.read_text())


def test_reference_corpus_is_small_curated_non_empty() -> None:
    entries = load_reference_corpus()

    assert 1 <= len(entries) <= 12


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
