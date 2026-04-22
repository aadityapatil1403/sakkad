import functools
import logging
import re
from collections.abc import Callable
from typing import TypeVar

from google import genai
from google.genai import errors
from google.genai import types
from pydantic import BaseModel, ValidationError

from config import settings
from models.gemini import Layer1TagsResponse, Layer2TagsResponse, ShortTextResponse

logger = logging.getLogger(__name__)

_TIMEOUT_MS = 60_000
_TEXT_TIMEOUT_MS = 8_000
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


def _is_capacity_error(exc: Exception) -> bool:
    if not isinstance(exc, errors.ServerError):
        return False

    return getattr(exc, "status_code", None) == 503


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

    for index, model_name in enumerate(models):
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

            tags = _parse_tag_response(
                raw_response,
                layer=layer,
                response_model=response_model,
            )
            if tags is None:
                return [], None

            validated_tags = _validate_tags(
                tags,
                layer=layer,
                raw_response=raw_response,
                normalizer=normalizer,
                validator=validator,
            )
            if validated_tags is None:
                return [], None

            return validated_tags, model_name
        except Exception as exc:
            has_fallback = index < len(models) - 1
            if _is_capacity_error(exc):
                logger.warning(
                    "[gemini_service] %s: model %s unavailable (503), %s",
                    layer,
                    model_name,
                    "trying fallback" if has_fallback else "no fallback available",
                )
                if has_fallback:
                    continue
                return [], None

            if has_fallback:
                logger.warning(
                    "[gemini_service] %s: model %s failed, trying fallback: %s",
                    layer,
                    model_name,
                    exc,
                )
                continue

            logger.exception("[gemini_service] %s: API error: %s", layer, exc)
            return [], None

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
) -> tuple[list[str], str | None]:
    if not settings.GEMINI_API_KEY:
        return [], None
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


def get_layer2_tags(image_bytes: bytes, layer1: list[str], mime_type: str = "image/jpeg") -> list[str]:
    """Return 10 hyphenated two-word descriptors for the image, or [] on failure."""
    return get_layer2_tags_with_model(image_bytes, layer1, mime_type=mime_type)[0]


def generate_short_text(
    *,
    task: str,
    context: str,
    fallback_instructions: str,
) -> str | None:
    if not settings.GEMINI_API_KEY:
        return None

    prompt = _TEXT_PROMPT_TEMPLATE.format(
        task=task,
        context=context,
        fallback_instructions=fallback_instructions,
    )

    models = _get_gemini_models()
    for index, model_name in enumerate(models):
        has_fallback = index < len(models) - 1
        try:
            response = _get_text_client().models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ShortTextResponse,
                ),
            )
        except Exception as exc:
            if _is_capacity_error(exc) and has_fallback:
                logger.warning(
                    "[gemini_service] text: model %s unavailable (503), trying fallback",
                    model_name,
                )
                continue
            if has_fallback:
                logger.warning(
                    "[gemini_service] text: model %s failed, trying fallback: %s",
                    model_name,
                    exc,
                )
                continue
            logger.warning("[gemini_service] text generation failed: %s", exc)
            return None

        raw_response = response.text
        if not raw_response:
            _log_failure(
                layer="text",
                reason="empty response text",
                raw_response=raw_response,
                details={"task": task, "model": model_name},
            )
            return None

        try:
            parsed = ShortTextResponse.model_validate_json(raw_response)
        except ValidationError as exc:
            _log_failure(
                layer="text",
                reason="schema parsing failed",
                raw_response=raw_response,
                details=exc.errors(),
            )
            return None

        text = parsed.text.strip()
        return text or None

    return None
