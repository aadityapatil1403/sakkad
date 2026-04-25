import base64

from fastapi import FastAPI
from fastapi.testclient import TestClient


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, data):
        self.data = data
        self.in_filters: list[tuple[str, list[str]]] = []

    def select(self, *_args, **_kwargs):
        return self

    def in_(self, key: str, value: list[str]):
        self.in_filters.append((key, value))
        return self

    def execute(self):
        rows = list(self.data)
        for key, value in self.in_filters:
            rows = [row for row in rows if row.get(key) in value]
        return FakeResponse(rows)


class FakeSupabase:
    def __init__(self, *, captures_data):
        self.captures_data = captures_data

    def table(self, name: str):
        if name == "captures":
            return FakeQuery(self.captures_data)
        raise AssertionError(f"Unexpected table: {name}")


_SAMPLE_CAPTURE = {
    "id": "capture-1",
    "session_id": "session-1",
    "image_url": "https://example.com/img.jpg",
    "taxonomy_matches": {"Quiet Luxury": 0.88, "Tailoring": 0.74},
    "layer1_tags": ["monochrome", "structured"],
    "layer2_tags": ["tailored-coat"],
    "reference_matches": [],
    "created_at": "2026-04-24T10:00:00Z",
}

_FAKE_B64 = base64.b64encode(b"fake-png-bytes").decode("utf-8")


def _make_client(monkeypatch, *, captures_data, sketch_result: str | None = _FAKE_B64) -> TestClient:
    from routes.generate import router

    app = FastAPI()
    app.include_router(router)
    monkeypatch.setattr(
        "routes.generate.supabase",
        FakeSupabase(captures_data=captures_data),
    )
    monkeypatch.setattr(
        "routes.generate.generate_fashion_sketch",
        lambda **_kwargs: sketch_result,
    )
    return TestClient(app)


def test_generate_image_returns_base64_on_success(monkeypatch) -> None:
    # Arrange
    client = _make_client(monkeypatch, captures_data=[_SAMPLE_CAPTURE])

    # Act
    response = client.post(
        "/api/generate/image",
        json={"statement": "A tailored silhouette in muted tones.", "capture_ids": ["capture-1"]},
    )

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["image_b64"] == _FAKE_B64
    assert payload["mime_type"] == "image/png"
    assert payload["statement"] == "A tailored silhouette in muted tones."
    assert len(payload["taxonomy_influences"]) == 2
    assert payload["taxonomy_influences"][0]["label"] == "Quiet Luxury"
    assert payload["taxonomy_influences"][0]["score"] == 0.88


def test_generate_image_returns_503_when_sketch_fails(monkeypatch) -> None:
    # Arrange
    client = _make_client(monkeypatch, captures_data=[_SAMPLE_CAPTURE], sketch_result=None)

    # Act
    response = client.post(
        "/api/generate/image",
        json={"statement": "A layered look.", "capture_ids": ["capture-1"]},
    )

    # Assert
    assert response.status_code == 503
    assert response.json() == {"detail": "Sketch generation unavailable"}


def test_generate_image_returns_404_when_captures_not_found(monkeypatch) -> None:
    # Arrange
    client = _make_client(monkeypatch, captures_data=[])

    # Act
    response = client.post(
        "/api/generate/image",
        json={"statement": "Minimal drape.", "capture_ids": ["nonexistent"]},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Captures not found"}


def test_generate_image_returns_422_for_empty_statement(monkeypatch) -> None:
    # Arrange
    client = _make_client(monkeypatch, captures_data=[_SAMPLE_CAPTURE])

    # Act
    response = client.post(
        "/api/generate/image",
        json={"statement": "   ", "capture_ids": ["capture-1"]},
    )

    # Assert
    assert response.status_code == 422
    assert response.json() == {"detail": "statement must not be empty"}


def test_generate_image_returns_422_for_empty_capture_ids(monkeypatch) -> None:
    # Arrange
    client = _make_client(monkeypatch, captures_data=[])

    # Act
    response = client.post(
        "/api/generate/image",
        json={"statement": "Minimal drape.", "capture_ids": []},
    )

    # Assert
    assert response.status_code == 422
    assert response.json() == {"detail": "capture_ids must not be empty"}


def test_generate_image_aggregates_taxonomy_across_captures(monkeypatch) -> None:
    # Arrange — two captures, overlapping taxonomy; max score should win
    captures = [
        {**_SAMPLE_CAPTURE, "id": "c1", "taxonomy_matches": {"Gorpcore": 0.90, "Techwear": 0.60}},
        {**_SAMPLE_CAPTURE, "id": "c2", "taxonomy_matches": {"Gorpcore": 0.70, "Minimal": 0.80}},
    ]
    client = _make_client(monkeypatch, captures_data=captures)

    # Act
    response = client.post(
        "/api/generate/image",
        json={"statement": "Functional layers.", "capture_ids": ["c1", "c2"]},
    )

    # Assert
    assert response.status_code == 200
    influences = {i["label"]: i["score"] for i in response.json()["taxonomy_influences"]}
    assert influences["Gorpcore"] == 0.9  # max of 0.90, 0.70
    assert influences["Minimal"] == 0.8
    assert influences["Techwear"] == 0.6
