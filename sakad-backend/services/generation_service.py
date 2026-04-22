def _unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _top_labels(captures: list[dict], limit: int = 3) -> list[str]:
    scores: dict[str, float] = {}
    for capture in captures:
        taxonomy_matches = capture.get("taxonomy_matches")
        if not isinstance(taxonomy_matches, dict):
            continue
        for label, score in taxonomy_matches.items():
            if isinstance(label, str) and isinstance(score, int | float):
                scores[label] = max(scores.get(label, 0.0), float(score))
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [label for label, _score in ordered[:limit]]


def _collect_tags(captures: list[dict], key: str, limit: int = 4) -> list[str]:
    values: list[str] = []
    for capture in captures:
        raw_value = capture.get(key)
        if not isinstance(raw_value, list):
            continue
        for item in raw_value:
            if isinstance(item, str):
                values.append(item)
    return _unique_ordered(values)[:limit]


def _collect_reference_titles(captures: list[dict], limit: int = 3) -> list[str]:
    values: list[str] = []
    for capture in captures:
        raw_value = capture.get("reference_matches")
        if not isinstance(raw_value, list):
            continue
        for item in raw_value:
            if isinstance(item, dict) and isinstance(item.get("title"), str):
                values.append(item["title"])
    return _unique_ordered(values)[:limit]


def build_generation_context(captures: list[dict]) -> str:
    labels = _top_labels(captures)
    layer1_tags = _collect_tags(captures, "layer1_tags")
    layer2_tags = _collect_tags(captures, "layer2_tags")
    references = _collect_reference_titles(captures)

    return "\n".join([
        f"Capture count: {len(captures)}",
        f"Top taxonomy labels: {', '.join(labels) or 'none'}",
        f"Layer 1 tags: {', '.join(layer1_tags) or 'none'}",
        f"Layer 2 tags: {', '.join(layer2_tags) or 'none'}",
        f"Reference titles: {', '.join(references) or 'none'}",
    ])


def build_generation_fallback(kind: str, captures: list[dict]) -> str:
    labels = ", ".join(_top_labels(captures)) or "the current session"
    layer2_tags = ", ".join(_collect_tags(captures, "layer2_tags", limit=3))
    references = ", ".join(_collect_reference_titles(captures))

    if kind == "inspiration_prompt":
        detail = f" Push the look through {layer2_tags}." if layer2_tags else ""
        return f"Build from {labels} and keep the direction concise and wearable.{detail}".strip()
    if kind == "styling_direction":
        reference_text = f" Let references like {references} keep the styling grounded." if references else ""
        return f"Lean into {labels} with a clear silhouette and one strong focal piece.{reference_text}".strip()
    return f"This set of captures points toward {labels}, with a concise fashion direction that is easy to extend into a concept."


def build_session_reflection_fallback(captures: list[dict]) -> str:
    labels = ", ".join(_top_labels(captures)) or "a focused visual direction"
    layer1_tags = ", ".join(_collect_tags(captures, "layer1_tags", limit=3))
    references = ", ".join(_collect_reference_titles(captures))

    sentences = [
        f"This session centers on {labels} across {len(captures)} capture{'s' if len(captures) != 1 else ''}.",
        f"The visual language stays grounded in {layer1_tags or 'consistent styling cues'}.",
    ]
    if references:
        sentences.append(f"References like {references} help frame the direction.")
    return " ".join(sentences)
