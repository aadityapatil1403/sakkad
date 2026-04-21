import asyncio
import functools
import logging
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from services.enrich_service import enrich_capture
from services.read_contract import normalize_capture_read
from services.supabase_client import supabase

router = APIRouter()
logger = logging.getLogger(__name__)

STORAGE_BUCKET = "captures"
_missing_capture_enrichment_columns: set[str] = set()
_ENRICHMENT_COLUMNS = {"session_id", "reference_matches", "reference_explanation"}


def _build_capture_insert_payload(
    *,
    public_url: str,
    enriched_capture: dict,
    include_enrichment: bool,
) -> dict:
    payload = {
        "image_url": public_url,
        "embedding": enriched_capture["embedding"],
        "taxonomy_matches": enriched_capture["taxonomy_matches"],
        "layer1_tags": enriched_capture["layer1_tags"],
        "layer2_tags": enriched_capture["layer2_tags"],
        "tags": enriched_capture["tags"],
    }
    if include_enrichment:
        if "session_id" not in _missing_capture_enrichment_columns:
            payload["session_id"] = enriched_capture["session_id"]
        if "reference_matches" not in _missing_capture_enrichment_columns:
            payload["reference_matches"] = enriched_capture["reference_matches"]
        if "reference_explanation" not in _missing_capture_enrichment_columns:
            payload["reference_explanation"] = enriched_capture["reference_explanation"]
    return payload


def _missing_enrichment_columns(exc: Exception) -> set[str]:
    message = str(exc).lower()
    schema_error = (
        ("column" in message and "does not exist" in message)
        or ("schema cache" in message and "column" in message)
    )
    if not schema_error:
        return set()
    return {column for column in _ENRICHMENT_COLUMNS if column in message}


def _insert_capture(payload: dict, *, allow_retry_without_enrichment: bool) -> object:
    global _missing_capture_enrichment_columns

    try:
        return supabase.table("captures").insert(payload).execute()
    except Exception as exc:
        missing_columns = _missing_enrichment_columns(exc)
        if not allow_retry_without_enrichment or not missing_columns:
            raise
        _missing_capture_enrichment_columns.update(missing_columns)
        logger.warning(
            "[capture] enrichment columns unavailable; retrying legacy insert shape: %s",
            exc,
        )
        retry_payload = {
            key: value
            for key, value in payload.items()
            if key not in missing_columns
        }
        return supabase.table("captures").insert(retry_payload).execute()


@router.get("/api/captures/{capture_id}")
async def get_capture(capture_id: str) -> dict:
    response = (
        supabase.table("captures")
        .select("*")
        .eq("id", capture_id)
        .limit(1)
        .execute()
    )
    if response.data is None:
        raise HTTPException(status_code=500, detail="Failed to fetch capture")
    if not response.data:
        raise HTTPException(status_code=404, detail="Capture not found")
    return normalize_capture_read(response.data[0])


@router.post("/api/capture")
async def capture(
    file: UploadFile = File(...),
    session_id: str | None = Form(default=None),
) -> dict:
    try:
        image_bytes = await file.read()

        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"

        storage_response = supabase.storage.from_(STORAGE_BUCKET).upload(
            path=filename,
            file=image_bytes,
            file_options={"content-type": file.content_type or "image/jpeg"},
        )
        if hasattr(storage_response, "error") and storage_response.error:
            logger.error("[capture] storage upload failed: %s", storage_response.error)
            raise HTTPException(
                status_code=500,
                detail=f"Storage upload failed: {storage_response.error}",
            )

        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)

        loop = asyncio.get_running_loop()
        enrich_fn = functools.partial(
            enrich_capture,
            image_bytes,
            session_id,
            file.content_type or "image/jpeg",
        )
        try:
            enriched_capture = await loop.run_in_executor(None, enrich_fn)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        insert_payload = _build_capture_insert_payload(
            public_url=public_url,
            enriched_capture=enriched_capture,
            include_enrichment=True,
        )
        insert_response = _insert_capture(
            insert_payload,
            allow_retry_without_enrichment=bool(_ENRICHMENT_COLUMNS & set(insert_payload)),
        )

        if not insert_response.data:
            logger.error("[capture] insert failed after successful processing")
            raise HTTPException(status_code=500, detail="Failed to insert capture record")

        capture_record = insert_response.data[0]
        logger.info(
            "[capture] success: id=%s taxonomy_matches=%s reference_matches=%s gemini_layer1=%s gemini_layer2=%s layer1_model=%s layer2_model=%s",
            capture_record.get("id"),
            len(enriched_capture["taxonomy_matches"]),
            len(enriched_capture["reference_matches"]),
            bool(enriched_capture["layer1_tags"]),
            bool(enriched_capture["layer2_tags"]),
            enriched_capture["gemini_models"]["layer1"],
            enriched_capture["gemini_models"]["layer2"],
        )
        capture_record["gemini_models"] = enriched_capture["gemini_models"]
        return capture_record
    except HTTPException:
        logger.exception("[capture] request failed")
        raise
    except Exception:
        logger.exception("[capture] unhandled failure")
        raise
