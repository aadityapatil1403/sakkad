from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.sessions import router


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, data, *, execute_side_effect: Exception | None = None):
        self.data = data
        self.execute_side_effect = execute_side_effect

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.execute_side_effect is not None:
            raise self.execute_side_effect
        return FakeResponse(self.data)


class FakeSupabase:
    def __init__(self, *, sessions_data, captures_data, captures_error: Exception | None = None):
        self.sessions_data = sessions_data
        self.captures_data = captures_data
        self.captures_error = captures_error

    def table(self, name):
        if name == "sessions":
            return FakeQuery(self.sessions_data)
        if name == "captures":
            return FakeQuery(self.captures_data, execute_side_effect=self.captures_error)
        raise AssertionError(f"Unexpected table: {name}")


def _client_with_supabase(
    monkeypatch,
    *,
    sessions_data,
    captures_data,
    captures_error: Exception | None = None,
) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    monkeypatch.setattr(
        "routes.sessions.supabase",
        FakeSupabase(
            sessions_data=sessions_data,
            captures_data=captures_data,
            captures_error=captures_error,
        ),
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
            "taxonomy_matches": {"Gorpcore": 0.91},
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
    assert payload["captures"][0]["taxonomy_matches"]["Gorpcore"] == 0.91
    assert payload["captures"][0]["tags"]["palette"] == ["#111111", "#eeeeee"]
    assert payload["captures"][0]["tags"]["attributes"] is None
    assert payload["captures"][0]["tags"]["mood"] is None
    assert payload["captures"][0]["tags"]["layer2"] is None
    assert payload["captures"][0]["layer1_tags"] == ["technical"]
    assert payload["captures"][0]["layer2_tags"] == ["outdoor-shell"]
    assert payload["captures"][0]["reference_matches"][0]["brand"] is None
    assert payload["captures"][0]["reference_matches"][0]["title"] == "Arc'teryx shell"
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
            "taxonomy_matches": {"Minimal": 0.7},
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
    assert capture["taxonomy_matches"]["Minimal"] == 0.7
    assert capture["tags"] == {
        "palette": None,
        "attributes": None,
        "mood": None,
        "layer2": None,
    }
    assert capture["layer1_tags"] is None
    assert capture["layer2_tags"] is None
    assert capture["reference_matches"] is None
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
            "taxonomy_matches": {"Utility": 0.82},
            "tags": {"palette": ["#123456"]},
            "layer1_tags": ["structured"],
            "layer2_tags": ["workwear-jacket"],
        }],
    )

    response = client.get("/api/sessions/session-3")

    assert response.status_code == 200
    capture = response.json()["captures"][0]
    assert capture["image_url"] == "https://example.com/no-reference-columns.jpg"
    assert capture["reference_matches"] is None
    assert capture["reference_explanation"] is None


def test_get_session_degrades_to_empty_captures_when_session_id_column_is_missing(monkeypatch) -> None:
    client = _client_with_supabase(
        monkeypatch,
        sessions_data=[{"id": "session-legacy"}],
        captures_data=[],
        captures_error=RuntimeError("column session_id does not exist"),
    )

    response = client.get("/api/sessions/session-legacy")

    assert response.status_code == 200
    assert response.json() == {
        "session": {"id": "session-legacy"},
        "captures": [],
    }


def test_get_session_reflection_returns_render_ready_text(monkeypatch) -> None:
    client = _client_with_supabase(
        monkeypatch,
        sessions_data=[{"id": "session-4"}],
        captures_data=[{
            "id": "capture-4",
            "session_id": "session-4",
            "image_url": "https://example.com/reflection.jpg",
            "created_at": "2026-04-17T12:30:00Z",
            "taxonomy_matches": {"Utility": 0.82},
            "tags": {"palette": ["#123456"]},
            "layer1_tags": ["structured"],
            "layer2_tags": ["workwear-jacket"],
            "reference_matches": [{"title": "Field jacket", "score": 0.74}],
            "reference_explanation": "Workwear cues match the reference.",
        }],
    )
    monkeypatch.setattr(
        "routes.sessions.generate_session_reflection",
        lambda **_kwargs: "The session leans into structured utility dressing. The references keep it grounded in practical outerwear.",
    )

    response = client.get("/api/sessions/session-4/reflection")

    assert response.status_code == 200
    assert response.json() == {
        "session_id": "session-4",
        "reflection": "The session leans into structured utility dressing. The references keep it grounded in practical outerwear.",
        "fallback_used": False,
        "capture_count": 1,
    }


def test_get_session_reflection_returns_fallback_when_gemini_fails(monkeypatch) -> None:
    client = _client_with_supabase(
        monkeypatch,
        sessions_data=[{"id": "session-5"}],
        captures_data=[{
            "id": "capture-5",
            "session_id": "session-5",
            "image_url": "https://example.com/reflection.jpg",
            "created_at": "2026-04-17T12:30:00Z",
            "taxonomy_matches": {"Minimal": 0.91},
            "tags": {"palette": ["#f5f5f5"]},
            "layer1_tags": ["clean"],
            "layer2_tags": ["tailored-coat"],
            "reference_matches": [{"title": "Quiet luxury coat", "score": 0.74}],
            "reference_explanation": "Clean tailoring drives the match.",
        }],
    )
    monkeypatch.setattr("routes.sessions.generate_session_reflection", lambda **_kwargs: None)

    response = client.get("/api/sessions/session-5/reflection")

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "session-5"
    assert payload["fallback_used"] is True
    assert payload["capture_count"] == 1
    assert "Minimal" in payload["reflection"]


def test_get_session_reflection_returns_404_when_session_has_no_captures(monkeypatch) -> None:
    client = _client_with_supabase(
        monkeypatch,
        sessions_data=[{"id": "session-6"}],
        captures_data=[],
    )

    response = client.get("/api/sessions/session-6/reflection")

    assert response.status_code == 404
    assert response.json() == {"detail": "Session has no captures to summarize"}


def test_get_session_reflection_returns_fallback_when_gemini_returns_empty_string(monkeypatch) -> None:
    # Arrange: gemini_service normalizes empty strings to None; mock returns None
    client = _client_with_supabase(
        monkeypatch,
        sessions_data=[{"id": "session-7"}],
        captures_data=[{
            "id": "capture-7",
            "session_id": "session-7",
            "image_url": "https://example.com/empty-text.jpg",
            "created_at": "2026-04-21T08:00:00Z",
            "taxonomy_matches": {"Workwear": 0.85},
            "tags": {"palette": ["#8B4513"]},
            "layer1_tags": ["rugged"],
            "layer2_tags": ["denim-jacket"],
            "reference_matches": [{"title": "Carhartt WIP", "score": 0.80}],
            "reference_explanation": "Workwear heritage cues align.",
        }],
    )
    # generate_session_reflection returns None (as it does for empty responses)
    monkeypatch.setattr("routes.sessions.generate_session_reflection", lambda **_kwargs: None)

    # Act
    response = client.get("/api/sessions/session-7/reflection")

    # Assert: fallback text is used when generate_session_reflection returns None
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "session-7"
    assert payload["fallback_used"] is True
    assert payload["capture_count"] == 1
    assert "Workwear" in payload["reflection"]


def test_get_session_reflection_returns_503_for_legacy_schema(monkeypatch) -> None:
    client = _client_with_supabase(
        monkeypatch,
        sessions_data=[{"id": "session-legacy"}],
        captures_data=[],
        captures_error=RuntimeError("column session_id does not exist"),
    )

    response = client.get("/api/sessions/session-legacy/reflection")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Session reflection is unavailable until captures.session_id is migrated",
    }
