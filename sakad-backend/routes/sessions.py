from fastapi import APIRouter, HTTPException

from services.supabase_client import supabase

router = APIRouter()

DEV_USER_ID = "00000000-0000-0000-0000-000000000001"
SESSIONS_TABLE = "sessions"
CAPTURES_TABLE = "captures"


def _normalize_capture(capture: dict) -> dict:
    tags = capture.get("tags") or {}
    palette = tags.get("palette") if isinstance(tags, dict) else None
    return {
        "id": capture.get("id"),
        "session_id": capture.get("session_id"),
        "image_url": capture.get("image_url"),
        "created_at": capture.get("created_at"),
        "taxonomy_matches": capture.get("taxonomy_matches") or [],
        "tags": {"palette": palette or []},
        "layer1_tags": capture.get("layer1_tags") or [],
        "layer2_tags": capture.get("layer2_tags") or [],
        "reference_matches": capture.get("reference_matches") or [],
        "reference_explanation": capture.get("reference_explanation"),
    }


def _get_session_captures(session_id: str) -> list[dict]:
    response = (
        supabase.table(CAPTURES_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    rows = response.data or []
    return [_normalize_capture(row) for row in rows]


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
