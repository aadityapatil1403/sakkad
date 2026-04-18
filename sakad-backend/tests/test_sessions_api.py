from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.sessions import router


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

    def execute(self):
        return FakeResponse(self.data)


class FakeSupabase:
    def __init__(self, *, sessions_data, captures_data):
        self.sessions_data = sessions_data
        self.captures_data = captures_data

    def table(self, name):
        if name == "sessions":
            return FakeQuery(self.sessions_data)
        if name == "captures":
            return FakeQuery(self.captures_data)
        raise AssertionError(f"Unexpected table: {name}")


def _client_with_supabase(monkeypatch, *, sessions_data, captures_data) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    monkeypatch.setattr(
        "routes.sessions.supabase",
        FakeSupabase(sessions_data=sessions_data, captures_data=captures_data),
    )
    return TestClient(app)


def test_get_session_returns_session_detail_with_enriched_captures(monkeypatch) -> None:
    client = _client_with_supabase(
        monkeypatch,
        sessions_data=[{
            "id": "session-1",
            "started_at": "2026-04-17T10:00:00Z",
            "ended_at": None,
        }],
        captures_data=[{
            "id": "capture-1",
            "session_id": "session-1",
            "image_url": "https://example.com/look.jpg",
            "created_at": "2026-04-17T10:01:00Z",
            "taxonomy_matches": [{"label": "Gorpcore", "score": 0.91}],
            "tags": {"palette": ["#111111", "#eeeeee"]},
            "layer1_tags": ["technical"],
            "layer2_tags": ["outdoor-shell"],
            "reference_matches": [{"id": "ref-1", "title": "Arc'teryx shell", "score": 0.88}],
            "reference_explanation": "Technical outerwear and muted palette align with the reference.",
        }],
    )

    response = client.get("/api/sessions/session-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["session"]["id"] == "session-1"
    assert len(payload["captures"]) == 1
    assert payload["captures"][0]["image_url"] == "https://example.com/look.jpg"
    assert payload["captures"][0]["taxonomy_matches"][0]["label"] == "Gorpcore"
    assert payload["captures"][0]["tags"]["palette"] == ["#111111", "#eeeeee"]
    assert payload["captures"][0]["layer1_tags"] == ["technical"]
    assert payload["captures"][0]["layer2_tags"] == ["outdoor-shell"]
    assert payload["captures"][0]["reference_matches"][0]["id"] == "ref-1"
    assert payload["captures"][0]["reference_explanation"] is not None


def test_get_session_returns_404_when_missing(monkeypatch) -> None:
    client = _client_with_supabase(
        monkeypatch,
        sessions_data=[],
        captures_data=[],
    )

    response = client.get("/api/sessions/missing-session")

    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found"}


def test_get_session_normalizes_missing_optional_capture_fields(monkeypatch) -> None:
    client = _client_with_supabase(
        monkeypatch,
        sessions_data=[{"id": "session-2"}],
        captures_data=[{
            "id": "capture-2",
            "session_id": "session-2",
            "image_url": "https://example.com/plain.jpg",
            "created_at": "2026-04-17T11:00:00Z",
            "taxonomy_matches": [{"label": "Minimal", "score": 0.7}],
            "tags": None,
            "layer1_tags": None,
            "layer2_tags": None,
            "reference_matches": None,
            "reference_explanation": None,
        }],
    )

    response = client.get("/api/sessions/session-2")

    assert response.status_code == 200
    capture = response.json()["captures"][0]
    assert capture["taxonomy_matches"][0]["label"] == "Minimal"
    assert capture["tags"] == {"palette": []}
    assert capture["layer1_tags"] == []
    assert capture["layer2_tags"] == []
    assert capture["reference_matches"] == []
    assert capture["reference_explanation"] is None


def test_get_session_keeps_captures_when_reference_fields_are_absent(monkeypatch) -> None:
    client = _client_with_supabase(
        monkeypatch,
        sessions_data=[{"id": "session-3"}],
        captures_data=[{
            "id": "capture-3",
            "session_id": "session-3",
            "image_url": "https://example.com/no-reference-columns.jpg",
            "created_at": "2026-04-17T12:00:00Z",
            "taxonomy_matches": [{"label": "Utility", "score": 0.82}],
            "tags": {"palette": ["#123456"]},
            "layer1_tags": ["structured"],
            "layer2_tags": ["workwear-jacket"],
        }],
    )

    response = client.get("/api/sessions/session-3")

    assert response.status_code == 200
    capture = response.json()["captures"][0]
    assert capture["image_url"] == "https://example.com/no-reference-columns.jpg"
    assert capture["reference_matches"] == []
    assert capture["reference_explanation"] is None
