from pathlib import Path

from scripts.seed_demo_captures import (
    ensure_demo_sessions,
    evaluate_capture_result,
    ensure_runtime_environment,
    render_report_markdown,
    resolve_dataset_entries,
    try_upload_source_asset,
)


def test_resolve_dataset_entries_marks_missing_and_available_assets(tmp_path: Path) -> None:
    existing = tmp_path / "existing.jpg"
    existing.write_bytes(b"img")

    manifest = [
        {
            "filename": "existing.jpg",
            "session_alias": "session_fashion",
            "expected_taxonomy": ["Workwear"],
        },
        {
            "filename": "missing.jpg",
            "session_alias": "session_mixed",
            "expected_taxonomy": ["Monochrome"],
        },
    ]

    resolved = resolve_dataset_entries(manifest, tmp_path)

    assert resolved[0]["asset_status"] == "available"
    assert resolved[0]["local_path"] == str(existing)
    assert resolved[1]["asset_status"] == "missing"
    assert resolved[1]["local_path"] == str(tmp_path / "missing.jpg")


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.status_code = 200
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.counter = 0

    def post(self, path: str) -> _FakeResponse:
        self.calls.append(path)
        self.counter += 1
        return _FakeResponse({"id": f"session-{self.counter}"})


def test_ensure_demo_sessions_starts_one_session_per_alias() -> None:
    client = _FakeClient()

    session_map = ensure_demo_sessions(
        client,
        ["session_fashion", "session_abstract", "session_mixed"],
    )

    assert session_map == {
        "session_fashion": "session-1",
        "session_abstract": "session-2",
        "session_mixed": "session-3",
    }
    assert client.calls == [
        "/api/sessions/start",
        "/api/sessions/start",
        "/api/sessions/start",
    ]


def test_evaluate_capture_result_flags_wrong_taxonomy_and_low_reference() -> None:
    entry = {
        "filename": "western.jpg",
        "expected_taxonomy": ["Western Americana"],
        "acceptable_taxonomy": ["Cowboy Core"],
        "session_alias": "session_fashion",
        "asset_status": "available",
    }
    payload = {
        "taxonomy_matches": {"Gorpcore": 0.92, "Western Americana": 0.61},
        "reference_matches": [{"title": "Look 1", "score": 0.02}],
    }

    result = evaluate_capture_result(entry, payload)

    assert result["pass"] is False
    assert result["actual_top_match"] == "Gorpcore"
    assert "taxonomy mismatch" in result["notes"][0].lower()
    assert any("reference score" in note.lower() for note in result["notes"])


def test_render_report_markdown_includes_rows_and_missing_assets() -> None:
    summary = {
        "manifest_entries": [
            {
                "filename": "western.jpg",
                "bucket": "western / americana",
                "expected_taxonomy": ["Western Americana"],
                "asset_status": "available",
            },
            {
                "filename": "architectural_shadow_01.jpg",
                "bucket": "abstract / environmental",
                "expected_taxonomy": ["Avant-garde"],
                "asset_status": "missing",
            },
        ],
        "results": [
            {
                "image": "western.jpg",
                "expected": "Western Americana",
                "actual_top_match": "Western Americana",
                "pass": True,
                "notes": [],
                "top_reference": "Ralph Lauren Campaign (0.84)",
            },
            {
                "image": "stone_wall.jpg",
                "expected": "Avant-garde",
                "actual_top_match": "Workwear",
                "pass": False,
                "notes": ["taxonomy mismatch"],
                "top_reference": "None",
            },
        ],
        "missing_assets": [
            {
                "filename": "architectural_shadow_01.jpg",
                "bucket": "abstract / environmental",
                "notes": "Manual add required",
            }
        ],
        "recommended_images": ["western.jpg", "workwear.jpg"],
    }

    markdown = render_report_markdown(summary)

    assert "| western.jpg | Western Americana | Western Americana | PASS |" in markdown
    assert "| architectural_shadow_01.jpg | Avant-garde | Missing local asset | FAIL |" in markdown
    assert "architectural_shadow_01.jpg" in markdown
    assert "western.jpg" in markdown


def test_ensure_runtime_environment_requires_supabase_settings(monkeypatch) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)

    try:
        ensure_runtime_environment()
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected missing env vars to raise RuntimeError")

    assert "SUPABASE_URL" in message
    assert "SUPABASE_SERVICE_KEY" in message


class _FakeStorageResponse:
    def __init__(self, error: object = None) -> None:
        self.error = error


class _FakeBucketClient:
    def __init__(self, *, upload_error: object = None) -> None:
        self.upload_error = upload_error

    def upload(self, **_kwargs) -> _FakeStorageResponse:
        return _FakeStorageResponse(error=self.upload_error)

    def get_public_url(self, path: str) -> str:
        return f"https://example.com/{path}"


class _FakeStorageClient:
    def __init__(self, *, upload_error: object = None) -> None:
        self.upload_error = upload_error

    def from_(self, _bucket: str) -> _FakeBucketClient:
        return _FakeBucketClient(upload_error=self.upload_error)


class _FakeSupabase:
    def __init__(self, *, upload_error: object = None) -> None:
        self.storage = _FakeStorageClient(upload_error=upload_error)


def test_try_upload_source_asset_degrades_when_specs_bucket_is_missing() -> None:
    source_url, notes = try_upload_source_asset(
        _FakeSupabase(upload_error="Bucket not found"),
        filename="western.jpg",
        image_bytes=b"img",
        content_type="image/jpeg",
    )

    assert source_url is None
    assert any("specs-bucket upload skipped" in note.lower() for note in notes)
