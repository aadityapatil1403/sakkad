import json
import sys

import google.generativeai as genai

from config import settings

_LAYER1_PROMPT = """\
You are analyzing a fashion photograph.
Return exactly 10 single-word visual descriptors of what you literally see.
Focus on: colors, materials, textures, shapes, silhouettes.
Rules:
- Single words only, no hyphens
- Lowercase
- Be specific (burgundy not red, leather not fabric)
- No abstract concepts, only visual facts
Return ONLY a valid JSON array of exactly 10 strings. No other text.
Example: ["black", "leather", "oversized", "shiny", "structured",
          "indigo", "denim", "wide", "burgundy", "matte"]
"""

_LAYER2_PROMPT_TEMPLATE = """\
You are analyzing a fashion photograph.
Basic visual descriptors already identified: {layer1_joined}

Return exactly 10 two-word fashion descriptors that describe this image
in more specific detail. Build on the basic descriptors above.
Focus on: garment constructions, style combinations, material qualities,
silhouette details, styling choices.
Rules:
- Exactly two words per descriptor, hyphenated
- Lowercase
- Be specific and fashion-literate
- Describe what you see, not abstract aesthetics
Return ONLY a valid JSON array of exactly 10 strings. No other text.
Example: ["wide-leg", "moto-collar", "leather-jacket", "oversized-denim",
          "burgundy-loafer", "white-sock", "cropped-torso",
          "zip-closure", "ribbed-knit", "straight-hem"]
"""


# Capture any previously-set value of _get_model (e.g. a test mock) BEFORE
# the `def` statement below overwrites it during importlib.reload().
_saved_get_model = globals().get("_get_model")


def _get_model() -> genai.GenerativeModel:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-2.0-flash")


# If a mock/patch replaced _get_model before this reload, restore it.
# On the first (non-reload) import _saved_get_model is None, so we skip this.
if _saved_get_model is not None and _saved_get_model is not _get_model:
    _get_model = _saved_get_model  # type: ignore[assignment]
del _saved_get_model

def get_layer1_tags(image_bytes: bytes) -> list[str]:
    """Return 10 single-word visual descriptors for the image, or [] on failure."""
    try:
        model = _get_model()
        image_part = {"mime_type": "image/jpeg", "data": image_bytes}
        response = model.generate_content([_LAYER1_PROMPT, image_part])
        tags: list[str] = json.loads(response.text)
        if not isinstance(tags, list) or len(tags) != 10:
            print(f"[gemini_service] layer1: unexpected response length {len(tags) if isinstance(tags, list) else 'non-list'}")
            return []
        return tags
    except Exception as exc:
        print(f"[gemini_service] layer1 error: {exc}")
        return []


def get_layer2_tags(image_bytes: bytes, layer1: list[str]) -> list[str]:
    """Return 10 hyphenated two-word descriptors for the image, or [] on failure."""
    try:
        layer1_joined = ", ".join(layer1)
        prompt = _LAYER2_PROMPT_TEMPLATE.format(layer1_joined=layer1_joined)
        model = _get_model()
        image_part = {"mime_type": "image/jpeg", "data": image_bytes}
        response = model.generate_content([prompt, image_part])
        tags: list[str] = json.loads(response.text)
        if not isinstance(tags, list) or len(tags) != 10:
            print(f"[gemini_service] layer2: unexpected response length")
            return []
        if not all(t.count("-") == 1 for t in tags):
            print(f"[gemini_service] layer2: items failed hyphen validation: {tags}")
            return []
        return tags
    except Exception as exc:
        print(f"[gemini_service] layer2 error: {exc}")
        return []
