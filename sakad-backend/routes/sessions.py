from fastapi import APIRouter, HTTPException
from services.supabase_client import supabase

router = APIRouter()

DEV_USER_ID = "00000000-0000-0000-0000-000000000001"
SESSIONS_TABLE = "sessions"


@router.post("/api/sessions/start")
async def start_session():
    response = supabase.table(SESSIONS_TABLE).insert({
        "user_id": DEV_USER_ID,
    }).execute()
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
