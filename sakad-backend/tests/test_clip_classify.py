from unittest.mock import patch

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
    {
        "id": 4,
        "label": "label-D",
        "domain": "visual_environmental",
        "embedding": np.array([0.9, 0.1, 0.0], dtype=np.float32),
    },
]

_SINGLE_DOMAIN_TAXONOMY = _FAKE_TAXONOMY[:3]


class TestClipServiceClassify:
    def _run(self, image_embedding: list[float], taxonomy: list[dict]) -> dict[str, float]:
        from services.clip_service import classify

        with patch("services.clip_service._load_taxonomy", return_value=taxonomy):
            return classify(image_embedding)

    def test_returns_dict_of_label_to_score(self) -> None:
        result = self._run([1.0, 0.0, 0.0], _FAKE_TAXONOMY)

        assert isinstance(result, dict)
        assert all(isinstance(label, str) for label in result)
        assert all(isinstance(score, float) for score in result.values())

    def test_top_label_matches_closest_embedding(self) -> None:
        result = self._run([1.0, 0.0, 0.0], _FAKE_TAXONOMY)

        assert next(iter(result)) == "label-A"

    def test_scores_are_softmax_probabilities(self) -> None:
        result = self._run([1.0, 0.0, 0.0], _FAKE_TAXONOMY)

        assert abs(sum(result.values()) - 1.0) < 0.01
        assert all(0.0 <= score <= 1.0 for score in result.values())

    def test_domain_caps_applied_multi_domain(self) -> None:
        result = self._run([1.0, 0.0, 0.0], _FAKE_TAXONOMY)

        assert len(result) <= 4
        assert "label-D" in result

    def test_single_domain_fallback_returns_all_labels(self) -> None:
        result = self._run([1.0, 0.0, 0.0], _SINGLE_DOMAIN_TAXONOMY)

        assert len(result) == 3

    def test_empty_taxonomy_raises_runtime_error(self) -> None:
        from services.clip_service import classify

        with patch("services.clip_service._load_taxonomy", return_value=[]):
            with pytest.raises(RuntimeError):
                classify([1.0, 0.0, 0.0])

    def test_result_is_sorted_descending_by_score(self) -> None:
        result = self._run([1.0, 0.0, 0.0], _FAKE_TAXONOMY)

        assert list(result.values()) == sorted(result.values(), reverse=True)
