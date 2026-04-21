from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.capture import router as capture_router
from routes.gallery import router as gallery_router
from routes.sessions import router as sessions_router


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, data):
        self.data = data

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        return FakeResponse(self.data)


class FakeSupabase:
    def __init__(self, *, captures_data, sessions_data=None):
        self.captures_data = captures_data
        self.sessions_data = sessions_data or []

    def table(self, name):
        if name == "captures":
            return FakeQuery(self.captures_data)
        if name == "sessions":
            return FakeQuery(self.sessions_data)
        raise AssertionError(f"Unexpected table: {name}")


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(capture_router)
    app.include_router(gallery_router)
    app.include_router(sessions_router)
    return app


def test_get_capture_returns_normalized_enriched_capture(monkeypatch) -> None:
    capture_row = {
        "id": "capture-1",
        "session_id": None,
        "image_url": "https://example.com/look.jpg",
        "created_at": "2026-04-21T10:00:00Z",
        "taxonomy_matches": [{"label": "Gorpcore", "score": 0.91}],
        "tags": {"palette": ["#111111"]},
        "layer1_tags": ["technical"],
        "layer2_tags": ["outdoor-shell"],
        "reference_matches": [{"brand": "Arc'teryx", "title": "Shell", "score": 0.88}],
        "reference_explanation": None,
    }

    monkeypatch.setattr(
        "routes.capture.supabase",
        FakeSupabase(captures_data=[capture_row]),
    )

    client = TestClient(_build_app())
    response = client.get("/api/captures/capture-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "capture-1"
    assert payload["taxonomy_matches"] == {"Gorpcore": 0.91}
    assert payload["tags"] == {
        "palette": ["#111111"],
        "attributes": None,
        "mood": None,
        "layer2": None,
    }
    assert payload["reference_matches"] == [{
        "brand": "Arc'teryx",
        "title": "Shell",
        "score": 0.88,
        "description": None,
    }]
    assert payload["reference_explanation"] is None


def test_get_capture_returns_404_when_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        "routes.capture.supabase",
        FakeSupabase(captures_data=[]),
    )

    client = TestClient(_build_app())
    response = client.get("/api/captures/missing-capture")

    assert response.status_code == 404
    assert response.json() == {"detail": "Capture not found"}


def test_get_capture_returns_500_when_lookup_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        "routes.capture.supabase",
        FakeSupabase(captures_data=None),
    )

    client = TestClient(_build_app())
    response = client.get("/api/captures/capture-1")

    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to fetch capture"}


def test_gallery_returns_taxonomy_matches_as_object(monkeypatch) -> None:
    monkeypatch.setattr(
        "routes.gallery.supabase",
        FakeSupabase(captures_data=[{
            "id": "capture-2",
            "session_id": "session-2",
            "image_url": "https://example.com/gallery.jpg",
            "created_at": "2026-04-21T10:05:00Z",
            "taxonomy_matches": [{"label": "Minimal", "score": 0.77}],
            "tags": None,
            "layer1_tags": None,
            "layer2_tags": None,
            "reference_matches": None,
            "reference_explanation": None,
        }]),
    )

    client = TestClient(_build_app())
    response = client.get("/api/gallery")

    assert response.status_code == 200
    payload = response.json()[0]
    assert payload["taxonomy_matches"] == {"Minimal": 0.77}
    assert payload["tags"] == {
        "palette": None,
        "attributes": None,
        "mood": None,
        "layer2": None,
    }


def test_session_detail_returns_taxonomy_matches_as_object(monkeypatch) -> None:
    monkeypatch.setattr(
        "routes.sessions.supabase",
        FakeSupabase(
            sessions_data=[{"id": "session-1"}],
            captures_data=[{
                "id": "capture-3",
                "session_id": "session-1",
                "image_url": "https://example.com/session.jpg",
                "created_at": "2026-04-21T10:10:00Z",
                "taxonomy_matches": [{"label": "Utility", "score": 0.82}],
                "tags": {"palette": ["#222222"], "attributes": ["structured"]},
                "layer1_tags": ["structured"],
                "layer2_tags": ["workwear-jacket"],
                "reference_matches": [{"brand": "Carhartt", "title": "Jacket", "score": 0.8}],
                "reference_explanation": "Shared utility styling cues.",
            }],
        ),
    )

    client = TestClient(_build_app())
    response = client.get("/api/sessions/session-1")

    assert response.status_code == 200
    capture = response.json()["captures"][0]
    assert capture["taxonomy_matches"] == {"Utility": 0.82}
