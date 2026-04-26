import re
from typing import Literal

from pydantic import BaseModel

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

from services.gemini_service import generate_fashion_sketch, generate_short_text
from services.generation_service import (
    build_generation_context,
    build_generation_fallback,
)
from services.supabase_client import supabase

router = APIRouter()

GenerationKind = Literal["inspiration_prompt", "styling_direction", "creative_summary"]


class GenerateRequest(BaseModel):
    kind: GenerationKind
    session_id: str | None = None
    capture_ids: list[str] | None = None


def _get_session(session_id: str) -> dict | None:
    response = supabase.table("sessions").select("*").eq("id", session_id).execute()
    rows = response.data or []
    return rows[0] if rows else None


def _get_session_captures(session_id: str) -> list[dict]:
    response = supabase.table("captures").select("*").eq("session_id", session_id).execute()
    return response.data or []


def _get_captures(capture_ids: list[str]) -> list[dict]:
    response = supabase.table("captures").select("*").in_("id", capture_ids).execute()
    return response.data or []


def _fallback_instructions(kind: GenerationKind) -> str:
    if kind == "inspiration_prompt":
        return "Write one short inspiration prompt with a clear styling direction."
    if kind == "styling_direction":
        return "Write one short styling direction focused on silhouette and materials."
    return "Write one short creative summary."


@router.post("/api/generate")
async def generate(payload: GenerateRequest) -> dict:

    if bool(payload.session_id) == bool(payload.capture_ids):
        raise HTTPException(
            status_code=422,
            detail="Provide exactly one of session_id or capture_ids",
        )

    captures: list[dict]
    session_id = payload.session_id
    if payload.session_id is not None:
        if not _UUID_RE.match(payload.session_id):
            raise HTTPException(status_code=422, detail="Invalid session_id (not UUID)")
        session = _get_session(payload.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        captures = _get_session_captures(payload.session_id)
        if not captures:
            raise HTTPException(status_code=404, detail="Session has no captures to summarize")
    else:
        capture_ids = payload.capture_ids or []
        if not capture_ids:
            raise HTTPException(status_code=422, detail="capture_ids must not be empty")
        invalid_ids = [cid for cid in capture_ids if not _UUID_RE.match(cid)]
        if invalid_ids:
            raise HTTPException(status_code=422, detail=f"Invalid capture IDs (not UUID): {invalid_ids}")
        captures = _get_captures(capture_ids)
        if not captures:
            raise HTTPException(status_code=404, detail="Captures not found")
        session_ids = {capture.get("session_id") for capture in captures if capture.get("session_id")}
        session_id = next(iter(session_ids)) if len(session_ids) == 1 else None

    context = build_generation_context(captures)
    generated_text = await run_in_threadpool(
        generate_short_text,
        task=payload.kind,
        context=context,
        fallback_instructions=_fallback_instructions(payload.kind),
    )
    fallback_used = generated_text is None

    return {
        "kind": payload.kind,
        "text": generated_text or build_generation_fallback(payload.kind, captures),
        "fallback_used": fallback_used,
        "source": {
            "session_id": session_id,
            "capture_ids": [capture.get("id") for capture in captures if capture.get("id") is not None],
        },
    }


class GenerateImageRequest(BaseModel):
    statement: str
    capture_ids: list[str]


def _top_taxonomy_labels(captures: list[dict], limit: int = 6) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for capture in captures:
        taxonomy_matches = capture.get("taxonomy_matches")
        if not isinstance(taxonomy_matches, dict):
            continue
        for label, score in taxonomy_matches.items():
            if isinstance(label, str) and isinstance(score, int | float):
                scores[label] = max(scores.get(label, 0.0), float(score))
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)[:limit]


@router.post("/api/generate/image")
async def generate_image(payload: GenerateImageRequest) -> dict:
    if not payload.statement.strip():
        raise HTTPException(status_code=422, detail="statement must not be empty")
    if not payload.capture_ids:
        raise HTTPException(status_code=422, detail="capture_ids must not be empty")

    invalid_ids = [cid for cid in payload.capture_ids if not _UUID_RE.match(cid)]
    if invalid_ids:
        raise HTTPException(status_code=422, detail=f"Invalid capture IDs (not UUID): {invalid_ids}")

    captures = _get_captures(payload.capture_ids)
    if not captures:
        raise HTTPException(status_code=404, detail="Captures not found")

    returned_ids = {c.get("id") for c in captures if c.get("id") is not None}
    missing_ids = [cid for cid in payload.capture_ids if cid not in returned_ids]
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Captures not found: {missing_ids}",
        )

    taxonomy_labels = _top_taxonomy_labels(captures)
    result = await run_in_threadpool(
        generate_fashion_sketch,
        statement=payload.statement,
        taxonomy_labels=taxonomy_labels,
    )

    if result is None:
        raise HTTPException(status_code=503, detail="Sketch generation unavailable")

    image_b64, mime_type = result

    return {
        "image_b64": image_b64,
        "mime_type": mime_type,
        "statement": payload.statement,
        "taxonomy_influences": [
            {"label": label, "score": round(score, 3)} for label, score in taxonomy_labels
        ],
    }
