# sakad-backend/tests/test_capture_classify.py
"""
Tests for _classify() in routes/capture.py.
"""
from unittest.mock import patch

import numpy as np


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
    def _run(
        self,
        image_embedding: list[float],
        text_embedding: list[float] | None,
        *,
        image_weight: float = 1.0,
        text_weight: float = 0.0,
    ) -> list[dict]:
        from routes.capture import _classify

        with (
            patch("routes.capture._load_taxonomy", return_value=_FAKE_TAXONOMY),
            patch("routes.capture.IMAGE_WEIGHT", image_weight),
            patch("routes.capture.TEXT_WEIGHT", text_weight),
        ):
            return _classify(image_embedding, text_embedding)

    def test_no_text_embedding_returns_top_label_matching_image_vector(self) -> None:
        result = self._run([1.0, 0.0, 0.0], text_embedding=None)
        assert result[0]["label"] == "label-A"

    def test_text_embedding_shifts_top_result(self) -> None:
        result_no_text = self._run([1.0, 0.0, 0.0], text_embedding=None)
        result_with_text = self._run(
            [1.0, 0.0, 0.0],
            text_embedding=[0.0, 1.0, 0.0],
            image_weight=0.8,
            text_weight=0.2,
        )
        assert result_no_text[0]["label"] == "label-A"
        assert result_with_text[0]["label"] == "label-A"
        assert result_with_text[1]["label"] == "label-B"

    def test_returns_all_labels_when_taxonomy_has_3(self) -> None:
        result = self._run([1.0, 0.0, 0.0], text_embedding=None)
        assert len(result) == 3

    def test_result_has_required_keys(self) -> None:
        result = self._run([1.0, 0.0, 0.0], text_embedding=None)
        for item in result:
            assert "id" in item
            assert "label" in item
            assert "domain" in item
            assert "score" in item

    def test_empty_taxonomy_raises_runtime_error(self) -> None:
        from routes.capture import _classify
        import pytest

        with patch("routes.capture._load_taxonomy", return_value=[]):
            with pytest.raises(ValueError):
                _classify([1.0, 0.0, 0.0], text_embedding=None)

    def test_scores_sum_to_1(self) -> None:
        result = self._run([1.0, 0.0, 0.0], text_embedding=None)
        total = sum(r["score"] for r in result)
        assert abs(total - 1.0) < 1e-3


class TestCaptureTextEmbeddingPath:
    def test_image_only_runtime_skips_text_embedding(self) -> None:
        from unittest.mock import MagicMock, patch

        with patch("routes.capture.get_text_embedding") as mock_get_text_embedding, \
             patch("routes.capture._load_taxonomy", return_value=_FAKE_TAXONOMY), \
             patch("routes.capture._classify", return_value=[]) as mock_classify, \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags", return_value=["black"]), \
             patch("routes.capture.get_layer2_tags", return_value=[]), \
             patch("routes.capture.get_reference_matches", return_value=[]), \
             patch("routes.capture.generate_reference_explanation", return_value=None), \
             patch("routes.capture.supabase") as mock_supa, \
             patch("routes.capture._extract_palette", return_value=["#000000"]):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{"id": "1"}])

            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            from routes.capture import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            import io
            response = client.post(
                "/api/capture",
                files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
            )

        assert response.status_code == 200
        mock_get_text_embedding.assert_not_called()
        mock_classify.assert_called_once()
        _, kwargs = mock_classify.call_args
        assert kwargs.get("text_embedding") is None or mock_classify.call_args[0][1] is None


class TestCaptureFallbacks:
    def test_capture_succeeds_when_gemini_tag_generation_fails(self) -> None:
        from unittest.mock import MagicMock, patch

        with patch("routes.capture._load_taxonomy", return_value=_FAKE_TAXONOMY), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags", return_value=[]), \
             patch("routes.capture.get_layer2_tags", return_value=[]), \
             patch("routes.capture.get_reference_matches", return_value=[{"id": "ref-1", "title": "Look 1", "score": 0.91}]), \
             patch("routes.capture.generate_reference_explanation", return_value="Looks aligned with Look 1"), \
             patch("routes.capture.supabase") as mock_supa, \
             patch("routes.capture._extract_palette", return_value=["#000000"]):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{
                "id": "1",
                "taxonomy_matches": [{"label": "label-A", "score": 1.0}],
                "reference_matches": [{"id": "ref-1", "title": "Look 1", "score": 0.91}],
                "reference_explanation": "Looks aligned with Look 1",
                "tags": {"palette": ["#000000"]},
                "layer1_tags": None,
                "layer2_tags": None,
            }])

            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            from routes.capture import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            import io
            response = client.post(
                "/api/capture",
                files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["reference_matches"][0]["id"] == "ref-1"
        assert payload["tags"]["palette"] == ["#000000"]

    def test_capture_succeeds_when_explanation_generation_fails(self) -> None:
        from unittest.mock import MagicMock, patch

        with patch("routes.capture._load_taxonomy", return_value=_FAKE_TAXONOMY), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags", return_value=["black"]), \
             patch("routes.capture.get_layer2_tags", return_value=["wide-leg"]), \
             patch("routes.capture.get_reference_matches", return_value=[{"id": "ref-1", "title": "Look 1", "score": 0.91}]), \
             patch("routes.capture.generate_reference_explanation", side_effect=RuntimeError("Gemini unavailable")), \
             patch("routes.capture.supabase") as mock_supa, \
             patch("routes.capture._extract_palette", return_value=["#000000"]):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{
                "id": "1",
                "taxonomy_matches": [{"label": "label-A", "score": 1.0}],
                "reference_matches": [{"id": "ref-1", "title": "Look 1", "score": 0.91}],
                "reference_explanation": None,
                "tags": {"palette": ["#000000"]},
                "layer1_tags": ["black"],
                "layer2_tags": ["wide-leg"],
            }])

            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            from routes.capture import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            import io
            response = client.post(
                "/api/capture",
                files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
            )

        assert response.status_code == 200
        insert_payload = mock_supa.table().insert.call_args.args[0]
        assert insert_payload["reference_matches"][0]["id"] == "ref-1"
        assert insert_payload["reference_explanation"] is None

    def test_capture_persists_session_id_when_provided(self) -> None:
        from unittest.mock import MagicMock, patch

        with patch("routes.capture._load_taxonomy", return_value=_FAKE_TAXONOMY), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags", return_value=["black"]), \
             patch("routes.capture.get_layer2_tags", return_value=["wide-leg"]), \
             patch("routes.capture.get_reference_matches", return_value=[]), \
             patch("routes.capture.generate_reference_explanation", return_value=None), \
             patch("routes.capture.supabase") as mock_supa, \
             patch("routes.capture._extract_palette", return_value=["#000000"]):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{"id": "1", "session_id": "session-1"}])

            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            from routes.capture import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            import io
            response = client.post(
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
        from unittest.mock import MagicMock, patch

        with patch("routes.capture._missing_capture_enrichment_columns", set()), \
             patch("routes.capture._load_taxonomy", return_value=_FAKE_TAXONOMY), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags", return_value=["black"]), \
             patch("routes.capture.get_layer2_tags", return_value=["wide-leg"]), \
             patch("routes.capture.get_reference_matches", return_value=[{"id": "ref-1", "title": "Look 1", "score": 0.91}]), \
             patch("routes.capture.generate_reference_explanation", return_value="Looks aligned with Look 1"), \
             patch("routes.capture.supabase") as mock_supa, \
             patch("routes.capture._extract_palette", return_value=["#000000"]):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_insert = mock_supa.table().insert
            mock_insert.return_value.execute.side_effect = [
                RuntimeError("column reference_matches does not exist"),
                MagicMock(data=[{"id": "1"}]),
            ]

            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            from routes.capture import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            import io
            response = client.post(
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
        from unittest.mock import MagicMock, patch

        with patch("routes.capture._missing_capture_enrichment_columns", set()), \
             patch("routes.capture._load_taxonomy", return_value=_FAKE_TAXONOMY), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags", return_value=["black"]), \
             patch("routes.capture.get_layer2_tags", return_value=["wide-leg"]), \
             patch("routes.capture.get_reference_matches", return_value=[{"id": "ref-1", "title": "Look 1", "score": 0.91}]), \
             patch("routes.capture.generate_reference_explanation", return_value="Looks aligned with Look 1"), \
             patch("routes.capture.supabase") as mock_supa, \
             patch("routes.capture._extract_palette", return_value=["#000000"]):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_insert = mock_supa.table().insert
            mock_insert.return_value.execute.side_effect = [
                RuntimeError("Could not find the 'reference_explanation' column of 'captures' in the schema cache"),
                MagicMock(data=[{"id": "1"}]),
            ]

            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            from routes.capture import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            import io
            response = client.post(
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
        from unittest.mock import MagicMock, patch
        import pytest

        with patch("routes.capture._missing_capture_enrichment_columns", set()), \
             patch("routes.capture._load_taxonomy", return_value=_FAKE_TAXONOMY), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags", return_value=["black"]), \
             patch("routes.capture.get_layer2_tags", return_value=["wide-leg"]), \
             patch("routes.capture.get_reference_matches", return_value=[]), \
             patch("routes.capture.generate_reference_explanation", return_value=None), \
             patch("routes.capture.supabase") as mock_supa, \
             patch("routes.capture._extract_palette", return_value=["#000000"]):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.side_effect = RuntimeError("temporary database outage")

            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            from routes.capture import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            import io
            with pytest.raises(RuntimeError, match="temporary database outage"):
                client.post(
                    "/api/capture",
                    files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
                )

        assert mock_supa.table().insert().execute.call_count == 1

    def test_image_first_taxonomy_path_still_skips_text_embedding_with_enrichment(self) -> None:
        from unittest.mock import MagicMock, patch

        with patch("routes.capture.get_text_embedding") as mock_get_text_embedding, \
             patch("routes.capture._load_taxonomy", return_value=_FAKE_TAXONOMY), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags", return_value=["black"]), \
             patch("routes.capture.get_layer2_tags", return_value=["wide-leg"]), \
             patch("routes.capture.get_reference_matches", return_value=[]), \
             patch("routes.capture.generate_reference_explanation", return_value=None), \
             patch("routes.capture.supabase") as mock_supa, \
             patch("routes.capture._extract_palette", return_value=["#000000"]):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{"id": "1"}])

            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            from routes.capture import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            import io
            response = client.post(
                "/api/capture",
                files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
            )

        assert response.status_code == 200
        mock_get_text_embedding.assert_not_called()
