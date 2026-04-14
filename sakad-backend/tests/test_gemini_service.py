# sakad-backend/tests/test_gemini_service.py
import json
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(text: str) -> MagicMock:
    """Build a fake generate_content response with .text == text."""
    resp = MagicMock()
    resp.text = text
    return resp


def _make_mock_client(response_text: str | None = None, side_effect: Exception | None = None) -> MagicMock:
    """Build a mock genai.Client whose models.generate_content returns the given response."""
    mock_client = MagicMock()
    if side_effect is not None:
        mock_client.models.generate_content.side_effect = side_effect
    else:
        mock_client.models.generate_content.return_value = _mock_response(response_text or "")
    return mock_client


# ---------------------------------------------------------------------------
# get_layer1_tags
# ---------------------------------------------------------------------------

class TestGetLayer1Tags:
    def test_returns_10_strings_on_valid_response(self) -> None:
        tags = ["black", "leather", "oversized", "shiny", "structured",
                "indigo", "denim", "wide", "burgundy", "matte"]
        payload = json.dumps(tags)

        with patch("services.gemini_service._get_client", return_value=_make_mock_client(payload)):
            import services.gemini_service as gs
            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == tags

    def test_returns_empty_list_when_json_invalid(self) -> None:
        with patch("services.gemini_service._get_client", return_value=_make_mock_client("not json")):
            import services.gemini_service as gs
            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []

    def test_returns_empty_list_when_list_not_10(self) -> None:
        payload = json.dumps(["black", "leather"])  # only 2 items

        with patch("services.gemini_service._get_client", return_value=_make_mock_client(payload)):
            import services.gemini_service as gs
            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []

    def test_returns_empty_list_on_api_exception(self) -> None:
        with patch(
            "services.gemini_service._get_client",
            return_value=_make_mock_client(side_effect=RuntimeError("API down")),
        ):
            import services.gemini_service as gs
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

        with patch("services.gemini_service._get_client", return_value=_make_mock_client(payload)):
            import services.gemini_service as gs
            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == tags

    def test_returns_empty_list_when_json_invalid(self) -> None:
        with patch("services.gemini_service._get_client", return_value=_make_mock_client("not json")):
            import services.gemini_service as gs
            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == []

    def test_filters_out_items_without_exactly_one_hyphen(self) -> None:
        tags = ["wide-leg", "no-hyphen-here", "valid-tag",
                "another-good", "bad", "ok-word",
                "fine-item", "extra--dash", "good-one", "last-tag"]
        payload = json.dumps(tags)

        with patch("services.gemini_service._get_client", return_value=_make_mock_client(payload)):
            import services.gemini_service as gs
            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == []

    def test_returns_empty_list_on_api_exception(self) -> None:
        with patch(
            "services.gemini_service._get_client",
            return_value=_make_mock_client(side_effect=RuntimeError("API down")),
        ):
            import services.gemini_service as gs
            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == []
