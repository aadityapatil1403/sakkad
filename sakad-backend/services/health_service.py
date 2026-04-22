from __future__ import annotations

from config import settings
from services import clip_service
from services.supabase_client import supabase

CAPTURES_BUCKET = "captures"
CAPTURES_TABLE = "captures"


def _check_database() -> dict:
    try:
        response = supabase.table(CAPTURES_TABLE).select("id").limit(1).execute()
    except Exception as exc:
        return {
            "ok": False,
            "required": True,
            "detail": f"database check failed: {exc}",
            "table": CAPTURES_TABLE,
        }

    return {
        "ok": response.data is not None,
        "required": True,
        "detail": "database ready" if response.data is not None else "database returned no payload",
        "table": CAPTURES_TABLE,
    }


def _check_storage() -> dict:
    try:
        supabase.storage.from_(CAPTURES_BUCKET).list(path="", options={"limit": 1})
    except Exception as exc:
        return {
            "ok": False,
            "required": True,
            "detail": f"storage check failed: {exc}",
            "bucket": CAPTURES_BUCKET,
        }

    return {
        "ok": True,
        "required": True,
        "detail": "storage ready",
        "bucket": CAPTURES_BUCKET,
    }


def _check_taxonomy_model() -> dict:
    try:
        taxonomy = clip_service._load_taxonomy()
    except Exception as exc:
        return {
            "ok": False,
            "required": True,
            "detail": f"taxonomy/model check failed: {exc}",
            "model": settings.CLIP_MODEL_NAME,
        }

    return {
        "ok": True,
        "required": True,
        "detail": "taxonomy ready; model configured for lazy load",
        "model": settings.CLIP_MODEL_NAME,
        "taxonomy_labels": len(taxonomy),
        "model_loaded": clip_service._loaded,
    }


def _check_gemini() -> dict:
    if settings.GEMINI_API_KEY:
        return {
            "ok": True,
            "required": False,
            "detail": "gemini configured",
            "model": settings.GEMINI_MODEL,
        }

    return {
        "ok": False,
        "required": False,
        "detail": "GEMINI_API_KEY not configured; capture remains available without Gemini tags",
        "model": settings.GEMINI_MODEL,
    }


def get_demo_health_report() -> dict:
    checks = {
        "database": _check_database(),
        "storage": _check_storage(),
        "taxonomy": _check_taxonomy_model(),
        "gemini": _check_gemini(),
    }

    critical_failures = sum(
        1
        for check in checks.values()
        if check["required"] and not check["ok"]
    )
    degraded = sum(
        1
        for check in checks.values()
        if not check["ok"]
    ) - critical_failures
    healthy = sum(1 for check in checks.values() if check["ok"])

    if critical_failures:
        status = "error"
    elif degraded:
        status = "degraded"
    else:
        status = "ok"

    errors = [
        check["detail"]
        for check in checks.values()
        if not check["ok"]
    ]

    return {
        "status": status,
        "service": "sakad-backend",
        "checks": checks,
        "summary": {
            "healthy": healthy,
            "degraded": degraded,
            "critical_failures": critical_failures,
        },
        "errors": errors,
    }
