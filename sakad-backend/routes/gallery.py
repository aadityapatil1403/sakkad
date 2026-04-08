from fastapi import APIRouter, HTTPException
from services.supabase_client import supabase

router = APIRouter()


@router.get("/api/gallery")
async def gallery():
    response = (
        supabase.table("captures")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    if response.data is None:
        raise HTTPException(status_code=500, detail="Failed to fetch gallery")

    return response.data
