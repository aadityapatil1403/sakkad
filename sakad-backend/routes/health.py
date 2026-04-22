from fastapi import APIRouter
from fastapi.responses import JSONResponse

from services.health_service import get_demo_health_report

router = APIRouter()


@router.get("/api/health")
async def health():
    report = get_demo_health_report()
    status_code = 503 if report["status"] == "error" else 200
    return JSONResponse(content=report, status_code=status_code)


@router.get("/api/health/supabase")
async def supabase_health():
    report = get_demo_health_report()
    supabase_checks = {
        "database": report["checks"]["database"],
        "storage": report["checks"]["storage"],
    }
    supabase_errors = [
        check["detail"]
        for check in supabase_checks.values()
        if not check["ok"]
    ]
    supabase_status = "error" if supabase_errors else "ok"
    supabase_report = {
        "status": supabase_status,
        "checks": supabase_checks,
        "errors": supabase_errors,
    }
    status_code = 503 if supabase_status == "error" else 200
    return JSONResponse(content=supabase_report, status_code=status_code)
