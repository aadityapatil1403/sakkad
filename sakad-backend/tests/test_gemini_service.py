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


# ---------------------------------------------------------------------------
# Timeout and API key guard tests
# ---------------------------------------------------------------------------

class TestClientTimeout:
    def test_get_client_passes_timeout_via_http_options(self) -> None:
        """_get_client must set a finite timeout so Gemini calls don't hang forever."""
        import services.gemini_service as gs
        from google.genai import types as genai_types

        with patch("services.gemini_service.genai.Client") as mock_client_cls:
            mock_client_cls.return_value = MagicMock()
            gs._get_client()

        mock_client_cls.assert_called_once()
        _, kwargs = mock_client_cls.call_args
        http_options = kwargs.get("http_options")
        assert http_options is not None, "http_options not passed to genai.Client"
        assert isinstance(http_options, genai_types.HttpOptions)
        assert http_options.timeout is not None, "timeout must be set (not None)"
        assert http_options.timeout > 0, "timeout must be a positive value"


class TestApiKeyGuard:
    def test_layer1_returns_empty_without_calling_client_when_key_is_unset(self) -> None:
        """get_layer1_tags must short-circuit and return [] when GEMINI_API_KEY is empty."""
        import services.gemini_service as gs

        with patch("services.gemini_service.settings") as mock_settings, \
             patch("services.gemini_service._get_client") as mock_get_client:
            mock_settings.GEMINI_API_KEY = ""
            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []
        mock_get_client.assert_not_called()

    def test_layer2_returns_empty_without_calling_client_when_key_is_unset(self) -> None:
        """get_layer2_tags must short-circuit and return [] when GEMINI_API_KEY is empty."""
        layer1 = ["black", "leather", "oversized", "shiny", "structured",
                  "indigo", "denim", "wide", "burgundy", "matte"]
        import services.gemini_service as gs

        with patch("services.gemini_service.settings") as mock_settings, \
             patch("services.gemini_service._get_client") as mock_get_client:
            mock_settings.GEMINI_API_KEY = ""
            result = gs.get_layer2_tags(b"fake-image-bytes", layer1)

        assert result == []
        mock_get_client.assert_not_called()
