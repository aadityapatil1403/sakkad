from fastapi import APIRouter, HTTPException
from services.supabase_client import supabase

router = APIRouter()

CAPTURES_BUCKET = "captures"
CAPTURES_TABLE = "captures"


@router.get("/api/health")
async def health():
    return {"status": "ok"}


@router.get("/api/health/supabase")
async def supabase_health():
    checks = {
        "database": {"ok": False, "table": CAPTURES_TABLE},
        "storage": {"ok": False, "bucket": CAPTURES_BUCKET},
    }

    errors: list[str] = []

    try:
        response = supabase.table(CAPTURES_TABLE).select("id").limit(1).execute()
        checks["database"]["ok"] = response.data is not None
    except Exception as exc:
        errors.append(f"database check failed: {exc}")

    try:
        supabase.storage.from_(CAPTURES_BUCKET).list(path="", options={"limit": 1})
        checks["storage"]["ok"] = True
    except Exception as exc:
        errors.append(f"storage check failed: {exc}")

    overall_ok = all(check["ok"] for check in checks.values())

    if not overall_ok:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "checks": checks,
                "errors": errors,
            },
        )

    return {
        "status": "ok",
        "checks": checks,
    }
