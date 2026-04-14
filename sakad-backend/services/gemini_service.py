import json

from google import genai
from google.genai import types

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


_TIMEOUT_MS = 10_000  # 10 s — Gemini tagging is best-effort; don't let it hang /api/capture


def _get_client() -> genai.Client:
    return genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=_TIMEOUT_MS),
    )


def get_layer1_tags(image_bytes: bytes, mime_type: str = "image/jpeg") -> list[str]:
    """Return 10 single-word visual descriptors for the image, or [] on failure."""
    if not settings.GEMINI_API_KEY:
        return []
    try:
        client = _get_client()
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[_LAYER1_PROMPT, image_part],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        tags: list[str] = json.loads(response.text)
        if not isinstance(tags, list) or len(tags) != 10:
            response_len = len(tags) if isinstance(tags, list) else "non-list"
            print(f"[gemini_service] layer1: unexpected response length {response_len}")
            return []
        if not all(isinstance(t, str) for t in tags):
            print("[gemini_service] layer1: items are not all strings")
            return []
        return tags
    except json.JSONDecodeError as exc:
        print(f"[gemini_service] layer1 JSON parse error: {exc}")
        return []
    except Exception as exc:
        print(f"[gemini_service] layer1 error: {exc}")
        return []


def get_layer2_tags(image_bytes: bytes, layer1: list[str], mime_type: str = "image/jpeg") -> list[str]:
    """Return 10 hyphenated two-word descriptors for the image, or [] on failure."""
    if not settings.GEMINI_API_KEY:
        return []
    try:
        layer1_joined = ", ".join(layer1)
        prompt = _LAYER2_PROMPT_TEMPLATE.format(layer1_joined=layer1_joined)
        client = _get_client()
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, image_part],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        tags: list[str] = json.loads(response.text)
        if not isinstance(tags, list) or len(tags) != 10:
            print("[gemini_service] layer2: unexpected response length")
            return []
        if not all(isinstance(t, str) for t in tags):
            print("[gemini_service] layer2: items are not all strings")
            return []
        if not all(t.count("-") == 1 for t in tags):
            print(f"[gemini_service] layer2: items failed hyphen validation: {tags}")
            return []
        return tags
    except json.JSONDecodeError as exc:
        print(f"[gemini_service] layer2 JSON parse error: {exc}")
        return []
    except Exception as exc:
        print(f"[gemini_service] layer2 error: {exc}")
        return []
