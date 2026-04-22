from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import health as health_routes
from routes.health import router
from services import health_service


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _report(
    *,
    status: str,
    database_ok: bool = True,
    storage_ok: bool = True,
    taxonomy_ok: bool = True,
    gemini_ok: bool = True,
) -> dict:
    return {
        "status": status,
        "service": "sakad-backend",
        "checks": {
            "database": {"ok": database_ok, "required": True, "detail": "database ready"},
            "storage": {"ok": storage_ok, "required": True, "detail": "storage ready"},
            "taxonomy": {"ok": taxonomy_ok, "required": True, "detail": "taxonomy ready"},
            "gemini": {"ok": gemini_ok, "required": False, "detail": "gemini ready"},
        },
        "summary": {
            "healthy": sum((database_ok, storage_ok, taxonomy_ok, gemini_ok)),
            "degraded": int(not gemini_ok),
            "critical_failures": sum((not database_ok, not storage_ok, not taxonomy_ok)),
        },
        "errors": [],
    }


def test_health_returns_full_report_when_all_dependencies_are_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        health_routes,
        "get_demo_health_report",
        lambda: _report(status="ok"),
        raising=False,
    )

    response = _build_client().get("/api/health")

    assert response.status_code == 200
    assert response.json() == _report(status="ok")


def test_health_returns_200_with_degraded_status_for_non_critical_failures(monkeypatch) -> None:
    monkeypatch.setattr(
        health_routes,
        "get_demo_health_report",
        lambda: _report(status="degraded", gemini_ok=False),
        raising=False,
    )

    response = _build_client().get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["gemini"]["ok"] is False


def test_health_returns_503_when_a_required_dependency_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        health_routes,
        "get_demo_health_report",
        lambda: _report(status="error", database_ok=False),
        raising=False,
    )

    response = _build_client().get("/api/health")

    assert response.status_code == 503
    assert response.json()["status"] == "error"
    assert response.json()["checks"]["database"]["ok"] is False


def test_supabase_health_returns_only_supabase_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(
        health_routes,
        "get_demo_health_report",
        lambda: _report(status="degraded", gemini_ok=False),
        raising=False,
    )

    response = _build_client().get("/api/health/supabase")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {
            "database": {"ok": True, "required": True, "detail": "database ready"},
            "storage": {"ok": True, "required": True, "detail": "storage ready"},
        },
        "errors": [],
    }


def test_supabase_health_ignores_non_supabase_failures(monkeypatch) -> None:
    monkeypatch.setattr(
        health_routes,
        "get_demo_health_report",
        lambda: _report(status="error", taxonomy_ok=False),
        raising=False,
    )

    response = _build_client().get("/api/health/supabase")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {
            "database": {"ok": True, "required": True, "detail": "database ready"},
            "storage": {"ok": True, "required": True, "detail": "storage ready"},
        },
        "errors": [],
    }


def test_health_service_marks_optional_failures_as_degraded(monkeypatch) -> None:
    monkeypatch.setattr(health_service, "_check_database", lambda: {"ok": True, "required": True, "detail": "db"})
    monkeypatch.setattr(health_service, "_check_storage", lambda: {"ok": True, "required": True, "detail": "storage"})
    monkeypatch.setattr(health_service, "_check_taxonomy_model", lambda: {"ok": True, "required": True, "detail": "taxonomy"})
    monkeypatch.setattr(health_service, "_check_gemini", lambda: {"ok": False, "required": False, "detail": "gemini missing"})

    report = health_service.get_demo_health_report()

    assert report["status"] == "degraded"
    assert report["summary"] == {
        "healthy": 3,
        "degraded": 1,
        "critical_failures": 0,
    }
    assert report["errors"] == ["gemini missing"]


def test_health_service_marks_required_failures_as_error(monkeypatch) -> None:
    monkeypatch.setattr(health_service, "_check_database", lambda: {"ok": False, "required": True, "detail": "db down"})
    monkeypatch.setattr(health_service, "_check_storage", lambda: {"ok": True, "required": True, "detail": "storage"})
    monkeypatch.setattr(health_service, "_check_taxonomy_model", lambda: {"ok": True, "required": True, "detail": "taxonomy"})
    monkeypatch.setattr(health_service, "_check_gemini", lambda: {"ok": True, "required": False, "detail": "gemini"})

    report = health_service.get_demo_health_report()

    assert report["status"] == "error"
    assert report["summary"] == {
        "healthy": 3,
        "degraded": 0,
        "critical_failures": 1,
    }
    assert report["errors"] == ["db down"]
