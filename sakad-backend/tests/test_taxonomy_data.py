import json
from pathlib import Path


TAXONOMY_PATH = Path(__file__).resolve().parents[2] / "data" / "taxonomy.json"
MANIFEST_PATH = Path(__file__).resolve().parent.parent / "eval" / "classifier_manifest.json"


def load_taxonomy() -> list[dict]:
    return json.loads(TAXONOMY_PATH.read_text())


def load_manifest() -> list[dict]:
    return json.loads(MANIFEST_PATH.read_text())


def test_canonical_taxonomy_is_fashion_only() -> None:
    taxonomy = load_taxonomy()

    assert taxonomy
    domains = {entry["domain"] for entry in taxonomy}

    assert domains == {"fashion_streetwear", "abstract_visual"}
    assert sum(1 for entry in taxonomy if entry["domain"] == "abstract_visual") == 25


def test_manifest_labels_exist_in_canonical_taxonomy() -> None:
    taxonomy = load_taxonomy()
    labels = {entry["label"] for entry in taxonomy}
    manifest = load_manifest()

    required = set()
    for item in manifest:
        required.update(item["expected_primary_labels"])
        required.update(item.get("acceptable_secondary_labels", []))

    assert required.issubset(labels)
