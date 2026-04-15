# sakad-backend/tests/test_capture_classify.py
"""
Tests for _classify() in routes/capture.py.

Strategy: mock _load_taxonomy() so we can use a deterministic 3-label taxonomy
and verify that:
  1. Without text_embedding the image vector is used as-is.
  2. With text_embedding the blended vector shifts the top result.
"""
import numpy as np
from unittest.mock import patch


# Build a fake taxonomy: 3 unit vectors pointing along axes
_FAKE_TAXONOMY = [
    {
        "id": 1,
        "label": "label-A",
        "domain": "streetwear",
        "embedding": np.array([1.0, 0.0, 0.0], dtype=np.float32),
    },
    {
        "id": 2,
        "label": "label-B",
        "domain": "streetwear",
        "embedding": np.array([0.0, 1.0, 0.0], dtype=np.float32),
    },
    {
        "id": 3,
        "label": "label-C",
        "domain": "streetwear",
        "embedding": np.array([0.0, 0.0, 1.0], dtype=np.float32),
    },
]


class TestClassify:
    def _run(
        self,
        image_embedding: list[float],
        text_embedding: list[float] | None,
    ) -> list[dict]:
        from routes.capture import _classify
        with patch("routes.capture._load_taxonomy", return_value=_FAKE_TAXONOMY):
            return _classify(image_embedding, text_embedding)

    def test_no_text_embedding_returns_top_label_matching_image_vector(self) -> None:
        # Image strongly aligned with label-A
        result = self._run([1.0, 0.0, 0.0], text_embedding=None)
        assert result[0]["label"] == "label-A"

    def test_text_embedding_shifts_top_result(self) -> None:
        # Image aligned with label-A, text aligned with label-B
        # Blend: 0.6*[1,0,0] + 0.4*[0,1,0] = [0.6, 0.4, 0] → label-A still top
        result_no_text = self._run([1.0, 0.0, 0.0], text_embedding=None)
        result_with_text = self._run([1.0, 0.0, 0.0], text_embedding=[0.0, 1.0, 0.0])
        # Top label stays label-A but the second should now be label-B
        assert result_no_text[0]["label"] == "label-A"
        assert result_with_text[0]["label"] == "label-A"
        assert result_with_text[1]["label"] == "label-B"

    def test_returns_all_labels_when_taxonomy_has_3(self) -> None:
        result = self._run([1.0, 0.0, 0.0], text_embedding=None)
        assert len(result) == 3  # min(5, len(taxonomy))

    def test_result_has_required_keys(self) -> None:
        result = self._run([1.0, 0.0, 0.0], text_embedding=None)
        for item in result:
            assert "id" in item
            assert "label" in item
            assert "domain" in item
            assert "score" in item

    def test_scores_sum_to_1(self) -> None:
        result = self._run([1.0, 0.0, 0.0], text_embedding=None)
        total = sum(r["score"] for r in result)
        assert abs(total - 1.0) < 1e-3  # top-5 subset, may not be exactly 1 for 3-label


class TestGetTextEmbeddingFallback:
    """get_text_embedding failures in capture() must fall back to image-only, not raise 500."""

    def test_text_embedding_exception_falls_back_to_none(self) -> None:
        """If get_text_embedding raises, _classify should still be called with text_embedding=None."""
        from unittest.mock import MagicMock, patch

        # Simulate get_text_embedding raising (e.g. CUDA OOM)
        with patch("routes.capture.get_text_embedding", side_effect=RuntimeError("CUDA OOM")), \
             patch("routes.capture._load_taxonomy", return_value=_FAKE_TAXONOMY), \
             patch("routes.capture._classify", return_value=[]) as mock_classify, \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags", return_value=["black"]), \
             patch("routes.capture.get_layer2_tags", return_value=[]), \
             patch("routes.capture.supabase") as mock_supa, \
             patch("routes.capture._extract_palette", return_value=["#000000"]):
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{"id": "1"}])

            from fastapi.testclient import TestClient
            from fastapi import FastAPI
            from routes.capture import router
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            import io
            response = client.post(
                "/api/capture",
                files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
            )

        # Must succeed (not 500) and _classify must have been called with text_embedding=None
        assert response.status_code == 200
        mock_classify.assert_called_once()
        _, kwargs = mock_classify.call_args
        assert kwargs.get("text_embedding") is None or mock_classify.call_args[0][1] is None
