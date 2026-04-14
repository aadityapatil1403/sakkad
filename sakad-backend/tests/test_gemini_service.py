# sakad-backend/tests/test_gemini_service.py
import json
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(text: str) -> MagicMock:
    """Build a fake GenerateContentResponse with .text == text."""
    resp = MagicMock()
    resp.text = text
    return resp


# ---------------------------------------------------------------------------
# get_layer1_tags
# ---------------------------------------------------------------------------

class TestGetLayer1Tags:
    def test_returns_10_strings_on_valid_response(self) -> None:
        tags = ["black", "leather", "oversized", "shiny", "structured",
                "indigo", "denim", "wide", "burgundy", "matte"]
        payload = json.dumps(tags)

        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = _mock_response(payload)
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == tags

    def test_returns_empty_list_when_json_invalid(self) -> None:
        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = _mock_response("not json")
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []

    def test_returns_empty_list_when_list_not_10(self) -> None:
        payload = json.dumps(["black", "leather"])  # only 2 items

        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = _mock_response(payload)
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []

    def test_returns_empty_list_on_api_exception(self) -> None:
        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = RuntimeError("API down")
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []


# ---------------------------------------------------------------------------
# get_layer2_tags
# ---------------------------------------------------------------------------

class TestGetLayer2Tags:
    _layer1 = ["black", "leather", "oversized", "shiny", "structured",
                "indigo", "denim", "wide", "burgundy", "matte"]

    def test_returns_10_hyphenated_strings_on_valid_response(self) -> None:
        tags = ["wide-leg", "moto-collar", "leather-jacket", "oversized-denim",
                "burgundy-loafer", "white-sock", "cropped-torso",
                "zip-closure", "ribbed-knit", "straight-hem"]
        payload = json.dumps(tags)

        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = _mock_response(payload)
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == tags

    def test_returns_empty_list_when_json_invalid(self) -> None:
        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = _mock_response("not json")
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == []

    def test_filters_out_items_without_exactly_one_hyphen(self) -> None:
        tags = ["wide-leg", "no-hyphen-here", "valid-tag",
                "another-good", "bad", "ok-word",
                "fine-item", "extra--dash", "good-one", "last-tag"]
        # Items with 0 hyphens ("bad") or 2+ hyphens ("no-hyphen-here" has 2, "extra--dash")
        # should be dropped, causing the list to fail validation → return []
        payload = json.dumps(tags)

        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = _mock_response(payload)
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == []

    def test_returns_empty_list_on_api_exception(self) -> None:
        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = RuntimeError("API down")
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == []
