def _normalize_taxonomy_matches(value: object) -> dict[str, float]:
    if isinstance(value, dict):
        normalized: dict[str, float] = {}
        for key, score in value.items():
            if isinstance(key, str) and isinstance(score, int | float):
                normalized[key] = float(score)
        return dict(sorted(normalized.items(), key=lambda item: item[1], reverse=True))

    if isinstance(value, list):
        normalized = {}
        for item in value:
            if not isinstance(item, dict):
                continue
            label = item.get("label")
            score = item.get("score")
            if isinstance(label, str) and isinstance(score, int | float):
                normalized[label] = float(score)
        return dict(sorted(normalized.items(), key=lambda item: item[1], reverse=True))

    return {}


def _normalize_tags(value: object) -> dict[str, object | None]:
    tags = value if isinstance(value, dict) else {}
    palette = tags.get("palette")
    attributes = tags.get("attributes")
    mood = tags.get("mood")
    layer2 = tags.get("layer2")
    return {
        "palette": palette if isinstance(palette, list) else None,
        "attributes": attributes if isinstance(attributes, list) else None,
        "mood": mood if isinstance(mood, str) else None,
        "layer2": layer2 if isinstance(layer2, list) else None,
    }


def _normalize_reference_matches(value: object) -> list[dict[str, object | None]] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        return None

    normalized: list[dict[str, object | None]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        score = item.get("score")
        normalized.append({
            "brand": item.get("brand") or item.get("designer"),
            "title": item.get("title"),
            "score": float(score) if isinstance(score, int | float) else None,
            "description": item.get("description"),
        })
    return normalized


def normalize_capture_read(capture: dict) -> dict:
    return {
        "id": capture.get("id"),
        "session_id": capture.get("session_id"),
        "image_url": capture.get("image_url"),
        "created_at": capture.get("created_at"),
        "taxonomy_matches": _normalize_taxonomy_matches(capture.get("taxonomy_matches")),
        "tags": _normalize_tags(capture.get("tags")),
        "layer1_tags": capture.get("layer1_tags") if isinstance(capture.get("layer1_tags"), list) else None,
        "layer2_tags": capture.get("layer2_tags") if isinstance(capture.get("layer2_tags"), list) else None,
        "reference_matches": _normalize_reference_matches(capture.get("reference_matches")),
        "reference_explanation": (
            capture.get("reference_explanation")
            if isinstance(capture.get("reference_explanation"), str)
            or capture.get("reference_explanation") is None
            else None
        ),
    }
