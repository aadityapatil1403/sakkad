import logging

from services.clip_service import classify, get_image_embedding
from services.color_service import extract_palette
from services.gemini_service import get_layer1_tags_with_model, get_layer2_tags_with_model
from services.retrieval_service import get_reference_matches

logger = logging.getLogger(__name__)


def generate_reference_explanation(
    taxonomy_matches: dict[str, float] | None,
    reference_matches: list[dict] | None,
    layer1_tags: list[str] | None = None,
    layer2_tags: list[str] | None = None,
) -> str | None:
    if not taxonomy_matches or not reference_matches:
        return None

    top_taxonomy = next(iter(taxonomy_matches))
    top_reference = reference_matches[0]
    reference_name = top_reference.get("title") or top_reference.get("designer") or "the top reference"
    cue_source = layer2_tags or layer1_tags or []
    cues = ", ".join(cue_source[:3])

    explanation = f"This image reads closest to {top_taxonomy} and aligns with {reference_name}."
    if cues:
        explanation += f" Key visual cues include {cues}."
    return explanation


def enrich_capture(
    image_bytes: bytes,
    session_id: str | None,
    mime_type: str = "image/jpeg",
) -> dict:
    image_embedding = get_image_embedding(image_bytes)

    try:
        layer1_tags, layer1_model = get_layer1_tags_with_model(image_bytes, mime_type=mime_type)
    except Exception as exc:
        logger.warning("[enrich_capture] gemini layer1 failed: %s", exc)
        layer1_tags, layer1_model = [], None
    layer1_tags = layer1_tags or []

    if layer1_tags:
        try:
            layer2_tags, layer2_model = get_layer2_tags_with_model(
                image_bytes,
                layer1_tags,
                mime_type=mime_type,
            )
        except Exception as exc:
            logger.warning("[enrich_capture] gemini layer2 failed: %s", exc)
            layer2_tags, layer2_model = [], None
    else:
        layer2_tags, layer2_model = [], None
    layer2_tags = layer2_tags or []

    taxonomy_matches = classify(image_embedding)
    reference_matches = get_reference_matches(image_embedding)
    palette = extract_palette(image_bytes)

    try:
        reference_explanation = generate_reference_explanation(
            taxonomy_matches=taxonomy_matches,
            reference_matches=reference_matches,
            layer1_tags=layer1_tags or None,
            layer2_tags=layer2_tags or None,
        )
    except Exception:
        logger.exception("[enrich_capture] reference explanation failed")
        reference_explanation = None

    return {
        "embedding": image_embedding,
        "taxonomy_matches": taxonomy_matches,
        "layer1_tags": layer1_tags or None,
        "layer2_tags": layer2_tags or None,
        "tags": {"palette": palette},
        "reference_matches": reference_matches,
        "reference_explanation": reference_explanation,
        "gemini_models": {
            "layer1": layer1_model,
            "layer2": layer2_model,
        },
        "session_id": session_id,
    }
