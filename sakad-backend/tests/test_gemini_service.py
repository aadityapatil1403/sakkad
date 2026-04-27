# sakad-backend/tests/test_gemini_service.py
import json
from unittest.mock import MagicMock, patch

from google.genai import errors


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
        payload = json.dumps({"tags": tags})

        with patch("services.gemini_service._get_client", return_value=_make_mock_client(payload)):
            import services.gemini_service as gs
            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == tags

    def test_returns_empty_list_when_json_invalid(self) -> None:
        with patch("services.gemini_service._get_client", return_value=_make_mock_client("not json")), \
             patch("services.gemini_service.logger") as mock_logger:
            import services.gemini_service as gs
            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []
        mock_logger.log.assert_called_once()
        assert "schema parsing failed" in mock_logger.log.call_args.args[3]

    def test_returns_empty_list_when_list_not_10(self) -> None:
        payload = json.dumps({"tags": ["black", "leather"]})  # only 2 items

        with patch("services.gemini_service._get_client", return_value=_make_mock_client(payload)), \
             patch("services.gemini_service.logger") as mock_logger:
            import services.gemini_service as gs
            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []
        mock_logger.log.assert_called_once()
        assert "schema parsing failed" in mock_logger.log.call_args.args[3]

    def test_returns_empty_list_on_api_exception(self) -> None:
        with patch(
            "services.gemini_service._get_client",
            return_value=_make_mock_client(side_effect=RuntimeError("API down")),
        ):
            import services.gemini_service as gs
            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []

    def test_uses_configured_model_name(self) -> None:
        tags = ["black", "leather", "oversized", "shiny", "structured",
                "indigo", "denim", "wide", "burgundy", "matte"]
        payload = json.dumps({"tags": tags})
        mock_client = _make_mock_client(payload)

        with patch("services.gemini_service._get_client", return_value=mock_client), \
             patch("services.gemini_service.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "key"
            mock_settings.GEMINI_MODEL = "gemini-primary"
            mock_settings.GEMINI_FALLBACK_MODELS = ""
            import services.gemini_service as gs
            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == tags
        assert mock_client.models.generate_content.call_args.kwargs["model"] == "gemini-primary"

    def test_returns_model_name_with_tags(self) -> None:
        tags = ["black", "leather", "oversized", "shiny", "structured",
                "indigo", "denim", "wide", "burgundy", "matte"]
        payload = json.dumps({"tags": tags})

        with patch("services.gemini_service._get_client", return_value=_make_mock_client(payload)), \
             patch("services.gemini_service.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "key"
            mock_settings.GEMINI_MODEL = "gemini-primary"
            mock_settings.GEMINI_FALLBACK_MODELS = ""
            import services.gemini_service as gs
            result_tags, model_name = gs.get_layer1_tags_with_model(b"fake-image-bytes")

        assert result_tags == tags
        assert model_name == "gemini-primary"

    def test_falls_back_after_capacity_error(self) -> None:
        tags = ["black", "leather", "oversized", "shiny", "structured",
                "indigo", "denim", "wide", "burgundy", "matte"]
        payload = json.dumps({"tags": tags})
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            errors.ServerError(
                503,
                {
                    "error": {
                        "code": 503,
                        "message": "This model is currently experiencing high demand.",
                        "status": "UNAVAILABLE",
                    },
                },
                MagicMock(),
            ),
            _mock_response(payload),
        ]

        with patch("services.gemini_service._get_client", return_value=mock_client), \
             patch("services.gemini_service.settings") as mock_settings, \
             patch("services.gemini_service.logger") as mock_logger:
            mock_settings.GEMINI_API_KEY = "key"
            mock_settings.GEMINI_MODEL = "gemini-primary"
            mock_settings.GEMINI_FALLBACK_MODELS = "gemini-fallback"
            import services.gemini_service as gs
            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == tags
        assert mock_client.models.generate_content.call_count == 2
        first_call = mock_client.models.generate_content.call_args_list[0]
        second_call = mock_client.models.generate_content.call_args_list[1]
        assert first_call.kwargs["model"] == "gemini-primary"
        assert second_call.kwargs["model"] == "gemini-fallback"
        mock_logger.warning.assert_called()

    def test_returns_empty_list_when_all_models_return_503(self) -> None:
        server_error = errors.ServerError(
            503,
            {"error": {"code": 503, "message": "UNAVAILABLE", "status": "UNAVAILABLE"}},
            MagicMock(),
        )
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [server_error, server_error]

        with patch("services.gemini_service._get_client", return_value=mock_client), \
             patch("services.gemini_service.settings") as mock_settings, \
             patch("services.gemini_service.time") as mock_time:
            mock_settings.GEMINI_API_KEY = "key"
            mock_settings.GEMINI_MODEL = "gemini-primary"
            mock_settings.GEMINI_FALLBACK_MODELS = "gemini-fallback"
            import services.gemini_service as gs
            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []
        assert mock_client.models.generate_content.call_count == 2
        mock_time.sleep.assert_called_once_with(1)

    def test_sleeps_before_fallback_on_transient_error(self) -> None:
        tags = ["black", "leather", "oversized", "shiny", "structured",
                "indigo", "denim", "wide", "burgundy", "matte"]
        payload = json.dumps({"tags": tags})
        server_error = errors.ServerError(
            503,
            {"error": {"code": 503, "message": "UNAVAILABLE", "status": "UNAVAILABLE"}},
            MagicMock(),
        )
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [server_error, _mock_response(payload)]

        with patch("services.gemini_service._get_client", return_value=mock_client), \
             patch("services.gemini_service.settings") as mock_settings, \
             patch("services.gemini_service.time") as mock_time:
            mock_settings.GEMINI_API_KEY = "key"
            mock_settings.GEMINI_MODEL = "gemini-primary"
            mock_settings.GEMINI_FALLBACK_MODELS = "gemini-fallback"
            import services.gemini_service as gs
            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == tags
        mock_time.sleep.assert_called_once_with(1)


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
        payload = json.dumps({"tags": tags})

        with patch("services.gemini_service._get_client", return_value=_make_mock_client(payload)):
            import services.gemini_service as gs
            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == tags

    def test_returns_empty_list_when_json_invalid(self) -> None:
        with patch("services.gemini_service._get_client", return_value=_make_mock_client("not json")), \
             patch("services.gemini_service.logger") as mock_logger:
            import services.gemini_service as gs
            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == []
        mock_logger.log.assert_called_once()
        assert "schema parsing failed" in mock_logger.log.call_args.args[3]

    def test_filters_out_items_without_exactly_one_hyphen(self) -> None:
        tags = ["wide-leg", "no-hyphen-here", "valid-tag",
                "another-good", "bad", "ok-word",
                "fine-item", "extra--dash", "good-one", "last-tag"]
        payload = json.dumps({"tags": tags})

        with patch("services.gemini_service._get_client", return_value=_make_mock_client(payload)), \
             patch("services.gemini_service.logger") as mock_logger:
            import services.gemini_service as gs
            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == []
        mock_logger.log.assert_called_once()
        assert "tag validation failed" in mock_logger.log.call_args.args[3]
        assert "'tag': 'bad'" in str(mock_logger.log.call_args.args[5])
        assert "expected exactly one hyphen" in str(mock_logger.log.call_args.args[5])

    def test_returns_empty_list_on_api_exception(self) -> None:
        with patch(
            "services.gemini_service._get_client",
            return_value=_make_mock_client(side_effect=RuntimeError("API down")),
        ):
            import services.gemini_service as gs
            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == []

    def test_normalizes_whitespace_and_unicode_hyphens_before_validation(self) -> None:
        tags = ["wide - leg", "moto–collar", "leather-jacket", "oversized-denim",
                "burgundy-loafer", "white-sock", "cropped-torso",
                "zip-closure", "ribbed-knit", "straight-hem"]
        payload = json.dumps({"tags": tags})

        with patch("services.gemini_service._get_client", return_value=_make_mock_client(payload)):
            import services.gemini_service as gs
            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result[:2] == ["wide-leg", "moto-collar"]

    def test_salvages_multi_hyphen_compounds_by_merging_prefix_tokens(self) -> None:
        tags = ["v-neck-collar", "wide-leg-denim", "short-sleeve-shirt", "oversized-denim",
                "burgundy-loafer", "white-sock", "cropped-torso",
                "zip-closure", "ribbed-knit", "straight-hem"]
        payload = json.dumps({"tags": tags})

        with patch("services.gemini_service._get_client", return_value=_make_mock_client(payload)):
            import services.gemini_service as gs
            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result[:3] == ["vneck-collar", "wideleg-denim", "shortsleeve-shirt"]

    def test_returns_empty_list_when_schema_shape_is_wrong(self) -> None:
        payload = json.dumps(["wide-leg", "moto-collar"])

        with patch("services.gemini_service._get_client", return_value=_make_mock_client(payload)), \
             patch("services.gemini_service.logger") as mock_logger:
            import services.gemini_service as gs
            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == []
        mock_logger.log.assert_called_once()
        assert "schema parsing failed" in mock_logger.log.call_args.args[3]


# ---------------------------------------------------------------------------
# Timeout and API key guard tests
# ---------------------------------------------------------------------------

class TestLayer1Validation:
    """Layer-1 tags must be single words (no spaces, no hyphens, non-empty)."""

    def _run_layer1(self, tags: list) -> list[str]:
        import json
        import services.gemini_service as gs
        payload = json.dumps({"tags": tags})
        with patch("services.gemini_service._get_client", return_value=_make_mock_client(payload)):
            return gs.get_layer1_tags(b"fake-image-bytes")

    def test_rejects_tags_with_spaces(self) -> None:
        # "dark blue" is two words — should reject the whole batch
        tags = ["black", "leather", "oversized", "shiny", "structured",
                "dark blue", "denim", "wide", "burgundy", "matte"]
        assert self._run_layer1(tags) == []

    def test_rejects_tags_with_hyphens(self) -> None:
        # "wide-leg" is a hyphenated compound — belongs in layer2, not layer1
        tags = ["black", "leather", "oversized", "shiny", "structured",
                "wide-leg", "denim", "wide", "burgundy", "matte"]
        assert self._run_layer1(tags) == []

    def test_rejects_empty_string_tags(self) -> None:
        tags = ["black", "leather", "oversized", "shiny", "structured",
                "", "denim", "wide", "burgundy", "matte"]
        assert self._run_layer1(tags) == []

    def test_accepts_valid_single_word_tags(self) -> None:
        tags = ["black", "leather", "oversized", "shiny", "structured",
                "indigo", "denim", "wide", "burgundy", "matte"]
        assert self._run_layer1(tags) == tags


class TestGenerateShortText:
    def test_returns_text_on_valid_json_response(self) -> None:
        payload = json.dumps({"text": "A short creative summary."})

        with patch("services.gemini_service._get_text_client", return_value=_make_mock_client(payload)):
            import services.gemini_service as gs

            result = gs.generate_short_text(
                task="creative_summary",
                context="Top labels: Minimal",
                fallback_instructions="Keep it short.",
            )

        assert result == "A short creative summary."

    def test_returns_none_on_api_exception(self) -> None:
        with patch(
            "services.gemini_service._get_text_client",
            return_value=_make_mock_client(side_effect=RuntimeError("API down")),
        ):
            import services.gemini_service as gs

            result = gs.generate_short_text(
                task="creative_summary",
                context="Top labels: Minimal",
                fallback_instructions="Keep it short.",
            )

        assert result is None


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
        assert http_options.timeout == 60_000


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


class TestGeminiFallbackBehavior:
    def test_capacity_error_without_fallback_returns_empty_without_exception_log(self) -> None:
        import services.gemini_service as gs

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("temporary capacity error")

        with patch("services.gemini_service._get_client", return_value=mock_client), \
             patch("services.gemini_service._is_retryable_error", return_value=True), \
             patch("services.gemini_service.settings") as mock_settings, \
             patch("services.gemini_service.logger") as mock_logger:
            mock_settings.GEMINI_API_KEY = "key"
            mock_settings.GEMINI_MODEL = "gemini-primary"
            mock_settings.GEMINI_FALLBACK_MODELS = ""
            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []
        mock_logger.warning.assert_called_once()
        mock_logger.exception.assert_not_called()
