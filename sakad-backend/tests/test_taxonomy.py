import json


SOCCER_LABEL_IDS = {
    "retro-kit-culture",
    "football-casual",
    "soccer-heritage",
    "sport-hybrid",
    "training-ground",
    "kit-collector",
}

SOCCER_LABELS = {
    "Retro Kit Culture",
    "Football Casual",
    "Soccer Heritage",
    "Sport Hybrid",
    "Training Ground",
    "Kit Collector",
}

REQUIRED_BRANDS = {
    "KidSuper",
    "Palace Skateboards",
    "Martine Rose",
    "Willy Chavarria",
    "Corteiz (CRTZ)",
    "424",
    "Wales Bonner x Adidas",
}


def test_taxonomy_has_soccer_labels() -> None:
    with open("../data/taxonomy.json") as f:
        taxonomy = json.load(f)
    labels = {entry["label"] for entry in taxonomy}
    missing = SOCCER_LABELS - labels
    assert not missing, f"Missing soccer labels: {missing}"


def test_taxonomy_minimum_count() -> None:
    with open("../data/taxonomy.json") as f:
        taxonomy = json.load(f)
    assert len(taxonomy) >= 87, f"Expected >= 87 labels, got {len(taxonomy)}"


def test_soccer_labels_have_rich_descriptions() -> None:
    with open("../data/taxonomy.json") as f:
        taxonomy = json.load(f)
    for entry in taxonomy:
        if entry["id"] in SOCCER_LABEL_IDS:
            assert len(entry["description"]) >= 200, (
                f"{entry['label']} description too short: {len(entry['description'])} chars"
            )
            assert entry["domain"] == "fashion_streetwear", (
                f"{entry['label']} has wrong domain: {entry['domain']}"
            )
            assert len(entry["visual_references"]) >= 2, (
                f"{entry['label']} needs at least 2 visual_references"
            )


def test_reference_corpus_has_soccer_bucket() -> None:
    with open("../data/reference_corpus.json") as f:
        corpus = json.load(f)
    soccer = [
        e for e in corpus
        if e.get("metadata", {}).get("bucket") == "soccer_streetwear"
    ]
    assert len(soccer) >= 20, f"Expected >= 20 soccer entries, got {len(soccer)}"


def test_soccer_corpus_brands_covered() -> None:
    with open("../data/reference_corpus.json") as f:
        corpus = json.load(f)
    soccer = [
        e for e in corpus
        if e.get("metadata", {}).get("bucket") == "soccer_streetwear"
    ]
    brands_in_corpus = {e["brand"] for e in soccer}
    # brand field may include collab suffixes (e.g. "Palace Skateboards x Juventus")
    # so check if any brand string starts with the required brand name
    def brand_present(required: str) -> bool:
        return any(b == required or b.startswith(required + " x") for b in brands_in_corpus)

    missing = {b for b in REQUIRED_BRANDS if not brand_present(b)}
    assert not missing, f"Missing required brands: {missing}"


def test_soccer_corpus_entries_have_valid_schema() -> None:
    with open("../data/reference_corpus.json") as f:
        corpus = json.load(f)
    soccer = [
        e for e in corpus
        if e.get("metadata", {}).get("bucket") == "soccer_streetwear"
    ]
    for entry in soccer:
        assert entry.get("id"), f"Missing id: {entry}"
        assert entry.get("designer"), f"Missing designer in {entry.get('id')}"
        assert entry.get("brand"), f"Missing brand in {entry.get('id')}"
        assert entry.get("description"), f"Missing description in {entry.get('id')}"
        assert len(entry.get("taxonomy_tags", [])) >= 1, f"No taxonomy_tags in {entry.get('id')}"
        assert len(entry["description"]) >= 100, (
            f"Description too short for {entry.get('id')}: {len(entry['description'])} chars"
        )
