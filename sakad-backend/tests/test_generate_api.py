from fastapi import FastAPI
from fastapi.testclient import TestClient


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, data):
        self.data = data
        self.filters: list[tuple[str, object]] = []
        self.in_filters: list[tuple[str, list[str]]] = []

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, key: str, value: object):
        self.filters.append((key, value))
        return self

    def in_(self, key: str, value: list[str]):
        self.in_filters.append((key, value))
        return self

    def execute(self):
        rows = list(self.data)
        for key, value in self.filters:
            rows = [row for row in rows if row.get(key) == value]
        for key, value in self.in_filters:
            rows = [row for row in rows if row.get(key) in value]
        return FakeResponse(rows)


class FakeSupabase:
    def __init__(self, *, sessions_data, captures_data):
        self.sessions_data = sessions_data
        self.captures_data = captures_data

    def table(self, name: str):
        if name == "sessions":
            return FakeQuery(self.sessions_data)
        if name == "captures":
            return FakeQuery(self.captures_data)
        raise AssertionError(f"Unexpected table: {name}")


_SESSION_1 = "10000000-0000-0000-0000-000000000001"
_SESSION_2 = "10000000-0000-0000-0000-000000000002"
_CAPTURE_1 = "20000000-0000-0000-0000-000000000001"
_CAPTURE_2 = "20000000-0000-0000-0000-000000000002"


def _client_with_dependencies(
    monkeypatch,
    *,
    sessions_data,
    captures_data,
    generated_text: str | None = "A concise creative summary.",
) -> TestClient:
    from routes.generate import router

    app = FastAPI()
    app.include_router(router)
    monkeypatch.setattr(
        "routes.generate.supabase",
        FakeSupabase(sessions_data=sessions_data, captures_data=captures_data),
    )
    monkeypatch.setattr(
        "routes.generate.generate_short_text",
        lambda **_kwargs: generated_text,
    )
    return TestClient(app)


def test_generate_returns_render_ready_text_for_session(monkeypatch) -> None:
    client = _client_with_dependencies(
        monkeypatch,
        sessions_data=[{"id": "10000000-0000-0000-0000-000000000001"}],
        captures_data=[{
            "id": "20000000-0000-0000-0000-000000000001",
            "session_id": "10000000-0000-0000-0000-000000000001",
            "image_url": "https://example.com/look.jpg",
            "taxonomy_matches": {"Gorpcore": 0.91, "Utility": 0.77},
            "layer1_tags": ["technical", "muted"],
            "layer2_tags": ["shell-jacket"],
            "reference_matches": [{"title": "Arc'teryx shell", "score": 0.88}],
            "created_at": "2026-04-21T10:00:00Z",
        }],
        generated_text="Use technical layers and grounded neutrals for a city-outdoor silhouette.",
    )

    response = client.post(
        "/api/generate",
        json={"kind": "styling_direction", "session_id": "10000000-0000-0000-0000-000000000001"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "kind": "styling_direction",
        "text": "Use technical layers and grounded neutrals for a city-outdoor silhouette.",
        "fallback_used": False,
        "source": {"session_id": "10000000-0000-0000-0000-000000000001", "capture_ids": ["20000000-0000-0000-0000-000000000001"]},
    }


def test_generate_returns_fallback_text_when_gemini_fails(monkeypatch) -> None:
    client = _client_with_dependencies(
        monkeypatch,
        sessions_data=[{"id": "10000000-0000-0000-0000-000000000001"}],
        captures_data=[{
            "id": "20000000-0000-0000-0000-000000000001",
            "session_id": "10000000-0000-0000-0000-000000000001",
            "image_url": "https://example.com/look.jpg",
            "taxonomy_matches": {"Minimal": 0.83},
            "layer1_tags": ["clean"],
            "layer2_tags": ["tailored-coat"],
            "reference_matches": [{"title": "Quiet luxury coat", "score": 0.79}],
            "created_at": "2026-04-21T10:00:00Z",
        }],
        generated_text=None,
    )

    response = client.post(
        "/api/generate",
        json={"kind": "creative_summary", "session_id": "10000000-0000-0000-0000-000000000001"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "creative_summary"
    assert payload["fallback_used"] is True
    assert payload["source"] == {"session_id": "10000000-0000-0000-0000-000000000001", "capture_ids": ["20000000-0000-0000-0000-000000000001"]}
    assert "Minimal" in payload["text"]


def test_generate_returns_404_for_missing_session(monkeypatch) -> None:
    client = _client_with_dependencies(
        monkeypatch,
        sessions_data=[],
        captures_data=[],
    )

    response = client.post(
        "/api/generate",
        json={"kind": "inspiration_prompt", "session_id": "10000000-0000-0000-0000-999999999999"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found"}


def test_generate_returns_404_for_empty_session(monkeypatch) -> None:
    client = _client_with_dependencies(
        monkeypatch,
        sessions_data=[{"id": "10000000-0000-0000-0000-000000000001"}],
        captures_data=[],
    )

    response = client.post(
        "/api/generate",
        json={"kind": "inspiration_prompt", "session_id": "10000000-0000-0000-0000-000000000001"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Session has no captures to summarize"}


def test_generate_with_capture_ids_returns_generated_text(monkeypatch) -> None:
    # Arrange
    client = _client_with_dependencies(
        monkeypatch,
        sessions_data=[],
        captures_data=[{
            "id": "20000000-0000-0000-0000-000000000010",
            "session_id": "10000000-0000-0000-0000-000000000010",
            "image_url": "https://example.com/cap10.jpg",
            "taxonomy_matches": {"Techwear": 0.88},
            "layer1_tags": ["urban"],
            "layer2_tags": ["cargo-pant"],
            "reference_matches": [{"title": "Y-3 collab", "score": 0.81}],
            "created_at": "2026-04-21T09:00:00Z",
        }],
        generated_text="Lean into utility details with a clean silhouette.",
    )

    # Act
    response = client.post(
        "/api/generate",
        json={"kind": "styling_direction", "capture_ids": ["20000000-0000-0000-0000-000000000010"]},
    )

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "styling_direction"
    assert payload["text"] == "Lean into utility details with a clean silhouette."
    assert payload["fallback_used"] is False
    assert payload["source"]["capture_ids"] == ["20000000-0000-0000-0000-000000000010"]
    assert payload["source"]["session_id"] == "10000000-0000-0000-0000-000000000010"


def test_generate_with_capture_ids_returns_fallback_when_gemini_fails(monkeypatch) -> None:
    # Arrange
    client = _client_with_dependencies(
        monkeypatch,
        sessions_data=[],
        captures_data=[{
            "id": "20000000-0000-0000-0000-000000000011",
            "session_id": "10000000-0000-0000-0000-000000000011",
            "image_url": "https://example.com/cap11.jpg",
            "taxonomy_matches": {"Gorpcore": 0.79},
            "layer1_tags": ["technical"],
            "layer2_tags": ["shell-jacket"],
            "reference_matches": [],
            "created_at": "2026-04-21T09:00:00Z",
        }],
        generated_text=None,
    )

    # Act
    response = client.post(
        "/api/generate",
        json={"kind": "inspiration_prompt", "capture_ids": ["20000000-0000-0000-0000-000000000011"]},
    )

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "inspiration_prompt"
    assert payload["fallback_used"] is True
    assert "Gorpcore" in payload["text"]
    assert payload["source"]["capture_ids"] == ["20000000-0000-0000-0000-000000000011"]


def test_generate_with_capture_ids_returns_404_when_captures_not_found(monkeypatch) -> None:
    # Arrange
    client = _client_with_dependencies(
        monkeypatch,
        sessions_data=[],
        captures_data=[],
    )

    # Act
    response = client.post(
        "/api/generate",
        json={"kind": "creative_summary", "capture_ids": ["00000000-0000-0000-0000-999999999999"]},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Captures not found"}


def test_generate_returns_422_for_unsupported_kind(monkeypatch) -> None:
    # Arrange: Pydantic rejects the invalid kind before the route runs
    client = _client_with_dependencies(
        monkeypatch,
        sessions_data=[],
        captures_data=[],
    )

    # Act
    response = client.post(
        "/api/generate",
        json={"kind": "invalid_kind", "session_id": "10000000-0000-0000-0000-000000000001"},
    )

    # Assert: Literal type enforcement returns 422
    assert response.status_code == 422


def test_generate_returns_422_when_both_session_id_and_capture_ids_provided(monkeypatch) -> None:
    # Arrange
    client = _client_with_dependencies(
        monkeypatch,
        sessions_data=[],
        captures_data=[],
    )

    # Act
    response = client.post(
        "/api/generate",
        json={"kind": "creative_summary", "session_id": "10000000-0000-0000-0000-000000000001", "capture_ids": ["20000000-0000-0000-0000-000000000001"]},
    )

    # Assert
    assert response.status_code == 422
    assert response.json() == {"detail": "Provide exactly one of session_id or capture_ids"}


def test_generate_returns_422_when_neither_session_id_nor_capture_ids_provided(monkeypatch) -> None:
    # Arrange
    client = _client_with_dependencies(
        monkeypatch,
        sessions_data=[],
        captures_data=[],
    )

    # Act
    response = client.post(
        "/api/generate",
        json={"kind": "styling_direction"},
    )

    # Assert
    assert response.status_code == 422
    assert response.json() == {"detail": "Provide exactly one of session_id or capture_ids"}


def test_generate_returns_422_for_empty_capture_ids(monkeypatch) -> None:
    # Arrange
    client = _client_with_dependencies(
        monkeypatch,
        sessions_data=[],
        captures_data=[],
    )

    # Act
    response = client.post(
        "/api/generate",
        json={"kind": "inspiration_prompt", "capture_ids": []},
    )

    # Assert: empty list is falsy, so XOR check triggers 422
    assert response.status_code == 422
    assert response.json() == {"detail": "Provide exactly one of session_id or capture_ids"}
