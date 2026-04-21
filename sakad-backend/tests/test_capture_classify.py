# sakad-backend/tests/test_capture_classify.py
"""
Tests for classify() in services/clip_service.py and capture pipeline integration.
"""
import io
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


_FAKE_TAXONOMY = [
    {
        "id": 1,
        "label": "label-A",
        "domain": "fashion_streetwear",
        "embedding": np.array([1.0, 0.0, 0.0], dtype=np.float32),
    },
    {
        "id": 2,
        "label": "label-B",
        "domain": "fashion_streetwear",
        "embedding": np.array([0.0, 1.0, 0.0], dtype=np.float32),
    },
    {
        "id": 3,
        "label": "label-C",
        "domain": "fashion_streetwear",
        "embedding": np.array([0.0, 0.0, 1.0], dtype=np.float32),
    },
]


class TestClassify:
    def _run(self, image_embedding: list[float]) -> dict[str, float]:
        from services.clip_service import classify

        with patch("services.clip_service._load_taxonomy", return_value=_FAKE_TAXONOMY):
            return classify(image_embedding)

    def test_no_text_embedding_returns_top_label_matching_image_vector(self) -> None:
        result = self._run([1.0, 0.0, 0.0])

        assert next(iter(result)) == "label-A"

    def test_top_result_ordering_reflects_cosine_similarity(self) -> None:
        result_a = self._run([1.0, 0.0, 0.0])
        result_b = self._run([0.0, 1.0, 0.0])

        assert next(iter(result_a)) == "label-A"
        assert next(iter(result_b)) == "label-B"

    def test_returns_all_labels_when_taxonomy_has_3(self) -> None:
        result = self._run([1.0, 0.0, 0.0])

        assert len(result) == 3

    def test_empty_taxonomy_raises_runtime_error(self) -> None:
        from services.clip_service import classify

        with patch("services.clip_service._load_taxonomy", return_value=[]):
            with pytest.raises(RuntimeError):
                classify([1.0, 0.0, 0.0])


class TestCaptureRouteIntegration:
    def _make_enriched(
        self,
        *,
        layer1: list[str] | None = None,
        layer2: list[str] | None = None,
        layer1_model: str | None = "gemini-2.5-flash",
        layer2_model: str | None = None,
        reference_matches: list[dict] | None = None,
        reference_explanation: str | None = None,
        session_id: str | None = None,
    ) -> dict:
        return {
            "embedding": [1.0, 0.0, 0.0],
            "taxonomy_matches": {"label-A": 0.9},
            "layer1_tags": layer1,
            "layer2_tags": layer2,
            "tags": {"palette": ["#000000"]},
            "reference_matches": reference_matches or [],
            "reference_explanation": reference_explanation,
            "gemini_models": {"layer1": layer1_model, "layer2": layer2_model},
            "session_id": session_id,
        }

    def _make_client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from routes.capture import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_capture_succeeds_when_gemini_tag_generation_fails(self) -> None:
        enriched = self._make_enriched(
            layer1=None,
            layer2=None,
            layer1_model=None,
            layer2_model=None,
            reference_matches=[{"id": "ref-1", "title": "Look 1", "score": 0.91}],
            reference_explanation="Looks aligned with Look 1",
        )

        with (
            patch("routes.capture.enrich_capture", return_value=enriched),
            patch("routes.capture.supabase") as mock_supa,
        ):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{
                **enriched,
                "id": "1",
                "image_url": "http://example.com/img.jpg",
            }])

            response = self._make_client().post(
                "/api/capture",
                files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["reference_matches"][0]["id"] == "ref-1"
        assert payload["tags"]["palette"] == ["#000000"]
        assert payload["gemini_models"] == {"layer1": None, "layer2": None}

    def test_capture_succeeds_when_explanation_generation_fails(self) -> None:
        enriched = self._make_enriched(
            layer1=["black"],
            layer2=["wide-leg"],
            layer1_model="gemini-2.5-flash",
            layer2_model="gemini-3.1-flash-lite-preview",
            reference_matches=[{"id": "ref-1", "title": "Look 1", "score": 0.91}],
            reference_explanation=None,
        )

        with (
            patch("routes.capture.enrich_capture", return_value=enriched),
            patch("routes.capture.supabase") as mock_supa,
        ):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{
                **enriched,
                "id": "1",
                "image_url": "http://example.com/img.jpg",
            }])

            response = self._make_client().post(
                "/api/capture",
                files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
            )

        assert response.status_code == 200
        assert response.json()["gemini_models"] == {
            "layer1": "gemini-2.5-flash",
            "layer2": "gemini-3.1-flash-lite-preview",
        }

    def test_capture_persists_session_id_when_provided(self) -> None:
        enriched = self._make_enriched(session_id="session-1")

        with (
            patch("routes.capture.enrich_capture", return_value=enriched),
            patch("routes.capture.supabase") as mock_supa,
        ):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{
                **enriched,
                "id": "1",
                "image_url": "http://example.com/img.jpg",
            }])

            response = self._make_client().post(
                "/api/capture",
                files={
                    "file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg"),
                    "session_id": (None, "session-1"),
                },
            )

        assert response.status_code == 200
        insert_payload = mock_supa.table().insert.call_args.args[0]
        assert insert_payload["session_id"] == "session-1"

    def test_capture_retries_without_enrichment_columns_when_schema_is_old(self) -> None:
        enriched = self._make_enriched(
            session_id="session-1",
            reference_matches=[{"id": "ref-1", "title": "Look 1", "score": 0.91}],
            reference_explanation="Looks aligned with Look 1",
        )

        with (
            patch("routes.capture._missing_capture_enrichment_columns", set()),
            patch("routes.capture.enrich_capture", return_value=enriched),
            patch("routes.capture.supabase") as mock_supa,
        ):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_insert = mock_supa.table().insert
            mock_insert.return_value.execute.side_effect = [
                RuntimeError("column reference_matches does not exist"),
                MagicMock(data=[{"id": "1"}]),
            ]

            response = self._make_client().post(
                "/api/capture",
                files={
                    "file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg"),
                    "session_id": (None, "session-1"),
                },
            )

        assert response.status_code == 200
        first_payload = mock_insert.call_args_list[0].args[0]
        second_payload = mock_insert.call_args_list[1].args[0]
        assert "reference_matches" in first_payload
        assert "reference_matches" not in second_payload
        assert second_payload["reference_explanation"] == "Looks aligned with Look 1"
        assert second_payload["session_id"] == "session-1"

    def test_capture_retries_only_missing_enrichment_columns(self) -> None:
        enriched = self._make_enriched(
            session_id="session-1",
            reference_matches=[{"id": "ref-1", "title": "Look 1", "score": 0.91}],
            reference_explanation="Looks aligned with Look 1",
        )

        with (
            patch("routes.capture._missing_capture_enrichment_columns", set()),
            patch("routes.capture.enrich_capture", return_value=enriched),
            patch("routes.capture.supabase") as mock_supa,
        ):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_insert = mock_supa.table().insert
            mock_insert.return_value.execute.side_effect = [
                RuntimeError("Could not find the 'reference_explanation' column of 'captures' in the schema cache"),
                MagicMock(data=[{"id": "1"}]),
            ]

            response = self._make_client().post(
                "/api/capture",
                files={
                    "file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg"),
                    "session_id": (None, "session-1"),
                },
            )

        assert response.status_code == 200
        first_payload = mock_insert.call_args_list[0].args[0]
        second_payload = mock_insert.call_args_list[1].args[0]
        assert "reference_matches" in first_payload
        assert "reference_matches" in second_payload
        assert "reference_explanation" in first_payload
        assert "reference_explanation" not in second_payload
        assert second_payload["session_id"] == "session-1"

    def test_capture_does_not_mask_non_schema_insert_failures(self) -> None:
        enriched = self._make_enriched()

        with (
            patch("routes.capture._missing_capture_enrichment_columns", set()),
            patch("routes.capture.enrich_capture", return_value=enriched),
            patch("routes.capture.supabase") as mock_supa,
        ):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.side_effect = RuntimeError("temporary database outage")

            with pytest.raises(RuntimeError, match="temporary database outage"):
                self._make_client().post(
                    "/api/capture",
                    files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
                )

        assert mock_supa.table().insert().execute.call_count == 1
