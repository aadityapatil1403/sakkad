import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.supabase_client import supabase
from services.clip_service import get_image_embedding

router = APIRouter()

STORAGE_BUCKET = "captures"


@router.post("/api/capture")
async def capture(file: UploadFile = File(...)):
    image_bytes = await file.read()

    filename = f"{uuid.uuid4()}.{file.filename.rsplit('.', 1)[-1] if '.' in file.filename else 'jpg'}"

    storage_response = supabase.storage.from_(STORAGE_BUCKET).upload(
        path=filename,
        file=image_bytes,
        file_options={"content-type": file.content_type or "image/jpeg"},
    )
    if hasattr(storage_response, "error") and storage_response.error:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {storage_response.error}")

    public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)

    embedding = get_image_embedding(image_bytes)

    insert_response = supabase.table("captures").insert({
        "image_url": public_url,
        "embedding": embedding,
    }).execute()

    if not insert_response.data:
        raise HTTPException(status_code=500, detail="Failed to insert capture record")

    return insert_response.data[0]
