import base64
import functools
import logging
import random
import re
import time
from collections.abc import Callable
from typing import TypeVar

from google import genai
from google.genai import errors
from google.genai import types
from pydantic import BaseModel, ValidationError

from config import settings
from models.gemini import Layer1TagsResponse, Layer2TagsResponse, ReflectionTextResponse, ShortTextResponse

logger = logging.getLogger(__name__)

_TIMEOUT_MS = 60_000
_IMAGE_TIMEOUT_MS = 120_000
_TEXT_TIMEOUT_MS = 12_000
_RAW_RESPONSE_LOG_LIMIT = 800

_UNICODE_HYPHENS_RE = re.compile(r"[‐‑‒–—−]")
_HYPHEN_SPACING_RE = re.compile(r"\s*-\s*")

_LAYER1_PROMPT = """\
You are analyzing a fashion photograph.
Return exactly 10 single-word visual descriptors of what you literally see.
Focus on: colors, materials, textures, shapes, silhouettes.
Rules:
- Single words only, no hyphens
- Lowercase
- Be specific (burgundy not red, leather not fabric)
- No abstract concepts, only visual facts
Return ONLY a valid JSON object with this shape:
{{"tags": ["black", "leather", "oversized", "shiny", "structured",
           "indigo", "denim", "wide", "burgundy", "matte"]}}
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
Return ONLY a valid JSON object with this shape:
{{"tags": ["wide-leg", "moto-collar", "leather-jacket", "oversized-denim",
           "burgundy-loafer", "white-sock", "cropped-torso",
           "zip-closure", "ribbed-knit", "straight-hem"]}}
"""

_LAYER2_ABSTRACT_PROMPT = """\
You are a fashion creative director. Given this image of a real-world texture, object,
or environment, generate exactly 10 hyphenated descriptors (e.g. cracked-leather,
rust-dyed, bark-brown) that describe the surface quality, material feel, color tone,
and structural character of what you see — as if translating it into fashion material
language. No garment names, no body parts, no outfit pieces.
Rules:
- Exactly two words per descriptor, hyphenated
- Lowercase
Return ONLY a valid JSON object with this shape:
{{"tags": ["cracked-leather", "rust-dyed", "bark-brown", "woven-grid",
           "matte-slate", "sand-worn", "moss-green", "coarse-grain",
           "mineral-wash", "soft-lichen"]}}
"""

_REFLECTION_SYSTEM_CONTEXT = (
    "You are a fashion creative director and cultural theorist with deep knowledge "
    "of designer archives, aesthetic movements, and visual theory. Your role is to "
    "reveal WHY someone is drawn to what they capture — connecting their visual "
    "instincts to specific designers, cultural movements, and material philosophies."
)

_REFLECTION_PROMPT_TEMPLATE = """\
{system_context}

A designer has just completed a capture session. Here is what they photographed:

{context}

Write 3-4 sentences that:
1. Identify 2-3 dominant visual threads running across these captures
2. Name specific designers or houses whose work shares this visual DNA \
(e.g. Iris van Herpen, Rick Owens, Jil Sander, Issey Miyake, Martin Margiela, \
Yohji Yamamoto, Craig Green, Helmut Lang, Alexander McQueen, Comme des Garçons)
3. Explain the specific quality that connects these captures to those designers \
(material transformation, structural tension, organic geometry, industrial decay, etc.)
4. End with one sentence about what this pattern reveals about the person's aesthetic instinct

Tone: like a knowledgeable mentor speaking directly to the person — conversational, \
insightful, not a product description. Do NOT use lists or bullet points.

Return ONLY a valid JSON object with this shape:
{{"text": "Your 3-4 sentence reflection here."}}
"""

_TEXT_PROMPT_TEMPLATE = """\
You are helping narrate a fashion research session.
Task: {task}

Context:
{context}

Requirements:
- Return one short paragraph only
- Keep it concise, readable, and demo-friendly
- Do not use markdown or bullets
- Follow this guidance: {fallback_instructions}

Return ONLY a valid JSON object with this shape:
{{"text": "Short render-ready copy."}}
"""

_TagsResponseT = TypeVar("_TagsResponseT", bound=BaseModel)


def _get_gemini_models() -> list[str]:
    models = [settings.GEMINI_MODEL.strip()]
    models.extend(
        model.strip()
        for model in settings.GEMINI_FALLBACK_MODELS.split(",")
        if model.strip()
    )
    return [model for model in models if model]


def _truncate_raw_response(raw_response: str | None) -> str | None:
    if raw_response is None or len(raw_response) <= _RAW_RESPONSE_LOG_LIMIT:
        return raw_response
    return f"{raw_response[:_RAW_RESPONSE_LOG_LIMIT]}...<truncated>"


def _log_failure(
    *,
    layer: str,
    reason: str,
    raw_response: str | None,
    details: object | None = None,
    level: int = logging.WARNING,
) -> None:
    logger.log(
        level,
        "[gemini_service] %s: %s | raw_response=%r | details=%s",
        layer,
        reason,
        _truncate_raw_response(raw_response),
        details,
    )


def _parse_tag_response(
    raw_response: str,
    *,
    layer: str,
    response_model: type[_TagsResponseT],
) -> list[str] | None:
    try:
        return response_model.model_validate_json(raw_response).tags
    except ValidationError as exc:
        _log_failure(
            layer=layer,
            reason="schema parsing failed",
            raw_response=raw_response,
            details=exc.errors(),
        )
        return None


def _normalize_base_tag(tag: str) -> str:
    normalized = tag.strip().lower()
    normalized = _UNICODE_HYPHENS_RE.sub("-", normalized)
    normalized = _HYPHEN_SPACING_RE.sub("-", normalized)
    return normalized


def _normalize_layer1_tag(tag: str) -> str:
    return _normalize_base_tag(tag)


def _normalize_layer2_tag(tag: str) -> str:
    normalized = _normalize_base_tag(tag)
    if normalized.count("-") <= 1:
        return normalized

    parts = [part for part in normalized.split("-") if part]
    if len(parts) < 2:
        return normalized

    return f"{''.join(parts[:-1])}-{parts[-1]}"


def _validate_tags(
    tags: list[str],
    *,
    layer: str,
    raw_response: str,
    normalizer: Callable[[str], str],
    validator: Callable[[str], str | None],
) -> list[str] | None:
    normalized_tags = [normalizer(tag) for tag in tags]
    invalid_tags = []
    for original_tag, normalized_tag in zip(tags, normalized_tags, strict=True):
        reason = validator(normalized_tag)
        if reason is not None:
            invalid_tags.append({
                "tag": original_tag,
                "normalized_tag": normalized_tag,
                "reason": reason,
            })

    if invalid_tags:
        _log_failure(
            layer=layer,
            reason="tag validation failed",
            raw_response=raw_response,
            details=invalid_tags,
        )
        return None

    return normalized_tags


def _validate_layer1_tag(tag: str) -> str | None:
    if not tag:
        return "empty string"
    if "-" in tag:
        return "hyphens are not allowed in layer1"
    if re.search(r"\s", tag):
        return "whitespace is not allowed in layer1"
    return None


def _validate_layer2_tag(tag: str) -> str | None:
    if not tag:
        return "empty string"
    if re.search(r"\s", tag):
        return "whitespace is not allowed in layer2"
    if tag.count("-") != 1:
        return "expected exactly one hyphen"
    left, right = tag.split("-", 1)
    if not left or not right:
        return "both hyphen-separated segments must be non-empty"
    return None


@functools.lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    return genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=_TIMEOUT_MS),
    )


@functools.lru_cache(maxsize=1)
def _get_text_client() -> genai.Client:
    return genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=_TEXT_TIMEOUT_MS),
    )


@functools.lru_cache(maxsize=1)
def _get_image_client() -> genai.Client:
    return genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=_IMAGE_TIMEOUT_MS),
    )


def _is_retryable_error(exc: Exception) -> bool:
    """Return True for transient server/rate/network errors worth retrying on a fallback model."""
    if isinstance(exc, errors.ServerError):
        code = getattr(exc, "code", None)
        # 500/502/503/504 are all transient server conditions worth trying a fallback model
        return code in (500, 502, 503, 504)
    # ClientError covers 4xx — auth failures, invalid model names are non-transient
    if isinstance(exc, errors.ClientError):
        code = getattr(exc, "code", None)
        return code == 429  # rate limit is the only retryable 4xx
    # Network-level errors (timeout, disconnect, httpx transport) are transient
    try:
        import httpx
        if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
            return True
    except ImportError:
        pass
    return isinstance(exc, (ConnectionError, TimeoutError, OSError))


def _call_gemini_tags(
    prompt: str,
    image_bytes: bytes,
    mime_type: str,
    response_model: type[_TagsResponseT],
    normalizer: Callable[[str], str],
    validator: Callable[[str], str | None],
    layer: str,
) -> tuple[list[str], str | None]:
    """Call Gemini, parse schema-backed tags, apply normalization and validation."""
    client = _get_client()
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    models = _get_gemini_models()
    max_attempts = 3

    for index, model_name in enumerate(models):
        for attempt in range(max_attempts):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt, image_part],  # type: ignore[arg-type]
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_model,
                    ),
                )
                raw_response = response.text
                if not raw_response:
                    _log_failure(
                        layer=layer,
                        reason="empty response text",
                        raw_response=raw_response,
                        details={"model": model_name},
                    )
                    return [], None

                tags = _parse_tag_response(raw_response, layer=layer, response_model=response_model)
                if tags is None:
                    return [], None

                validated_tags = _validate_tags(
                    tags, layer=layer, raw_response=raw_response,
                    normalizer=normalizer, validator=validator,
                )
                if validated_tags is None:
                    return [], None

                return validated_tags, model_name

            except Exception as exc:
                if not _is_retryable_error(exc):
                    logger.exception("[gemini_service] %s: API error: %s", layer, exc)
                    return [], None

                is_last_attempt = attempt == max_attempts - 1
                is_last_model = index == len(models) - 1

                if is_last_attempt and is_last_model:
                    logger.warning("[gemini_service] %s: all models unavailable: %s", layer, exc)
                    return [], None

                delay = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(
                    "[gemini_service] %s: model %s attempt %d/%d failed, retrying in %.1fs: %s",
                    layer, model_name, attempt + 1, max_attempts, delay, exc,
                )
                time.sleep(delay)

    return [], None


def get_layer1_tags_with_model(
    image_bytes: bytes, mime_type: str = "image/jpeg"
) -> tuple[list[str], str | None]:
    if not settings.GEMINI_API_KEY:
        return [], None
    return _call_gemini_tags(
        prompt=_LAYER1_PROMPT,
        image_bytes=image_bytes,
        mime_type=mime_type,
        response_model=Layer1TagsResponse,
        normalizer=_normalize_layer1_tag,
        validator=_validate_layer1_tag,
        layer="layer1",
    )


def get_layer1_tags(image_bytes: bytes, mime_type: str = "image/jpeg") -> list[str]:
    """Return 10 single-word visual descriptors for the image, or [] on failure."""
    return get_layer1_tags_with_model(image_bytes, mime_type=mime_type)[0]


def get_layer2_tags_with_model(
    image_bytes: bytes,
    layer1: list[str],
    mime_type: str = "image/jpeg",
    is_abstract: bool = False,
) -> tuple[list[str], str | None]:
    if not settings.GEMINI_API_KEY:
        return [], None
    if is_abstract:
        prompt = _LAYER2_ABSTRACT_PROMPT
    else:
        prompt = _LAYER2_PROMPT_TEMPLATE.format(layer1_joined=", ".join(layer1))
    return _call_gemini_tags(
        prompt=prompt,
        image_bytes=image_bytes,
        mime_type=mime_type,
        response_model=Layer2TagsResponse,
        normalizer=_normalize_layer2_tag,
        validator=_validate_layer2_tag,
        layer="layer2",
    )


def get_layer2_tags(
    image_bytes: bytes, layer1: list[str], mime_type: str = "image/jpeg", is_abstract: bool = False
) -> list[str]:
    """Return 10 hyphenated two-word descriptors for the image, or [] on failure."""
    return get_layer2_tags_with_model(image_bytes, layer1, mime_type=mime_type, is_abstract=is_abstract)[0]


_TextResponseT = TypeVar("_TextResponseT", ShortTextResponse, ReflectionTextResponse)


def _call_gemini_text(
    prompt: str,
    response_model: type[_TextResponseT],
    layer: str,
) -> str | None:
    """Call Gemini for a text response with exponential backoff retries across models."""
    models = _get_gemini_models()
    max_attempts = 3

    for index, model_name in enumerate(models):
        for attempt in range(max_attempts):
            try:
                response = _get_text_client().models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_model,
                    ),
                )
            except Exception as exc:
                if not _is_retryable_error(exc):
                    logger.warning("[gemini_service] %s generation failed: %s", layer, exc)
                    return None

                is_last_attempt = attempt == max_attempts - 1
                is_last_model = index == len(models) - 1

                if is_last_attempt and is_last_model:
                    logger.warning("[gemini_service] %s: all models unavailable: %s", layer, exc)
                    return None

                delay = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(
                    "[gemini_service] %s: model %s attempt %d/%d failed, retrying in %.1fs: %s",
                    layer, model_name, attempt + 1, max_attempts, delay, exc,
                )
                time.sleep(delay)
                continue

            raw_response = response.text
            if not raw_response:
                _log_failure(layer=layer, reason="empty response text",
                             raw_response=raw_response, details={"model": model_name})
                return None

            try:
                parsed = response_model.model_validate_json(raw_response)
            except ValidationError as exc:
                _log_failure(layer=layer, reason="schema parsing failed",
                             raw_response=raw_response, details=exc.errors())
                return None

            text = parsed.text.strip()
            return text or None

    return None


def generate_short_text(
    *,
    task: str,
    context: str,
    fallback_instructions: str,
) -> str | None:
    if not settings.GEMINI_API_KEY:
        return None
    prompt = _TEXT_PROMPT_TEMPLATE.format(
        task=task, context=context, fallback_instructions=fallback_instructions,
    )
    return _call_gemini_text(prompt, ShortTextResponse, layer="text")


def generate_session_reflection(context: str) -> str | None:
    if not settings.GEMINI_API_KEY:
        return None
    prompt = _REFLECTION_PROMPT_TEMPLATE.format(
        system_context=_REFLECTION_SYSTEM_CONTEXT, context=context,
    )
    return _call_gemini_text(prompt, ReflectionTextResponse, layer="reflection")


_SKETCH_SYSTEM_PROMPT = """\
You are a fashion illustration AI. Generate a hand-drawn fashion design sketch with these \
non-negotiable constraints:
- Single figure on pure white background
- Hand-drawn line art aesthetic: variable stroke weight, gestural marks, pencil/ink feel
- NO photorealism — this must look like a designer's sketchbook, not a photograph
- Show the full garment construction: seams, drape, proportion, silhouette
- Selective detail: face and hands loosely indicated, garments precisely rendered
- Reference designers: Issey Miyake, Margiela, Jil Sander, Helmut Lang, Yohji Yamamoto
- Monochrome or limited palette — black line on white, with optional single accent wash
- Portrait orientation, centered figure, generous white space around edges
"""

_SKETCH_PROMPT_TEMPLATE = """\
Fashion design sketch brief: {statement}

Style influences from captured imagery (SigLIP taxonomy scores):
{taxonomy_lines}

Draw the garment(s) described in the brief. Express the style influences through \
silhouette choice, fabric suggestion, and construction details — not decoration. \
Keep the sketch architectural and precise.\
"""


def generate_fashion_sketch(
    *,
    statement: str,
    taxonomy_labels: list[tuple[str, float]],
) -> tuple[str, str] | None:
    """Return (base64_image, mime_type) for a fashion sketch, or None on failure."""
    if not settings.GEMINI_API_KEY:
        return None

    taxonomy_lines = "\n".join(
        f"- {label}: {score:.2f}" for label, score in taxonomy_labels[:6]
    ) or "- No taxonomy data available"

    prompt = _SKETCH_PROMPT_TEMPLATE.format(
        statement=statement,
        taxonomy_lines=taxonomy_lines,
    )

    client = _get_image_client()
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_IMAGE_MODEL,
                contents=[_SKETCH_SYSTEM_PROMPT, prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )
        except Exception as exc:
            if not _is_retryable_error(exc) or attempt == max_attempts - 1:
                logger.warning("[gemini_service] sketch generation failed: %s", exc)
                return None
            delay = (2 ** attempt) + random.uniform(0, 1)
            logger.warning(
                "[gemini_service] sketch: attempt %d/%d failed, retrying in %.1fs: %s",
                attempt + 1, max_attempts, delay, exc,
            )
            time.sleep(delay)
            continue

        for part in response.parts:
            if part.inline_data is not None:
                mime_type = part.inline_data.mime_type or "image/png"
                image_b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                return image_b64, mime_type

        logger.warning("[gemini_service] sketch: no image part in response")
        return None

    return None
