from fastapi import APIRouter, HTTPException

from services.gemini_service import generate_session_reflection
from services.generation_service import (
    build_generation_context,
    build_session_reflection_fallback,
)
from services.read_contract import normalize_capture_read
from services.supabase_client import supabase

router = APIRouter()

DEV_USER_ID = "00000000-0000-0000-0000-000000000001"
SESSIONS_TABLE = "sessions"
CAPTURES_TABLE = "captures"


def _missing_session_id_column(exc: Exception) -> bool:
    message = str(exc).lower()
    return "session_id" in message and (
        ("column" in message and "does not exist" in message)
        or ("schema cache" in message and "column" in message)
    )


def _get_session_captures(session_id: str) -> list[dict]:
    captures, _legacy_schema = _get_session_captures_with_legacy_flag(session_id)
    return captures


def _get_session_captures_with_legacy_flag(session_id: str) -> tuple[list[dict], bool]:
    try:
        response = (
            supabase.table(CAPTURES_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
    except Exception as exc:
        if _missing_session_id_column(exc):
            return [], True
        raise
    rows = response.data or []
    return [normalize_capture_read(row) for row in rows], False


@router.post("/api/sessions/start")
async def start_session():
    response = supabase.table(SESSIONS_TABLE).insert({"user_id": DEV_USER_ID}).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to start session")
    return response.data[0]


@router.post("/api/sessions/{session_id}/end")
async def end_session(session_id: str):
    response = (
        supabase.table(SESSIONS_TABLE)
        .update({"ended_at": "now()"})
        .eq("id", session_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Session not found")
    return response.data[0]


@router.get("/api/sessions")
async def list_sessions():
    response = (
        supabase.table(SESSIONS_TABLE)
        .select("*")
        .order("started_at", desc=True)
        .execute()
    )
    if response.data is None:
        raise HTTPException(status_code=500, detail="Failed to fetch sessions")
    return response.data


@router.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session_response = (
        supabase.table(SESSIONS_TABLE)
        .select("*")
        .eq("id", session_id)
        .execute()
    )
    if not session_response.data:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session": session_response.data[0],
        "captures": _get_session_captures(session_id),
    }


@router.get("/api/sessions/{session_id}/reflection")
async def get_session_reflection(session_id: str) -> dict:
    session_response = (
        supabase.table(SESSIONS_TABLE)
        .select("*")
        .eq("id", session_id)
        .execute()
    )
    if not session_response.data:
        raise HTTPException(status_code=404, detail="Session not found")

    captures, legacy_schema = _get_session_captures_with_legacy_flag(session_id)
    if legacy_schema:
        raise HTTPException(
            status_code=503,
            detail="Session reflection is unavailable until captures.session_id is migrated",
        )
    if not captures:
        raise HTTPException(status_code=404, detail="Session has no captures to summarize")

    reflection = generate_session_reflection(
        context=build_generation_context(captures),
    )

    return {
        "session_id": session_id,
        "reflection": reflection or build_session_reflection_fallback(captures),
        "fallback_used": reflection is None,
        "capture_count": len(captures),
    }
