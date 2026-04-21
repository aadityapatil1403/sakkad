from unittest.mock import patch


class TestGenerateReferenceExplanation:
    def test_returns_none_when_no_taxonomy_matches(self) -> None:
        from services.enrich_service import generate_reference_explanation

        result = generate_reference_explanation(
            taxonomy_matches={},
            reference_matches=[{"id": "r1", "title": "Look 1", "score": 0.9}],
            layer1_tags=["black"],
            layer2_tags=None,
        )

        assert result is None

    def test_returns_none_when_no_reference_matches(self) -> None:
        from services.enrich_service import generate_reference_explanation

        result = generate_reference_explanation(
            taxonomy_matches={"Gorpcore": 0.91},
            reference_matches=[],
            layer1_tags=["black"],
            layer2_tags=None,
        )

        assert result is None

    def test_explanation_mentions_top_taxonomy_label(self) -> None:
        from services.enrich_service import generate_reference_explanation

        result = generate_reference_explanation(
            taxonomy_matches={"Gorpcore": 0.91, "Techwear": 0.7},
            reference_matches=[{"id": "r1", "title": "Arc'teryx shell", "score": 0.88}],
            layer1_tags=["technical", "black"],
            layer2_tags=["outdoor-shell"],
        )

        assert result is not None
        assert "Gorpcore" in result

    def test_explanation_mentions_reference_name(self) -> None:
        from services.enrich_service import generate_reference_explanation

        result = generate_reference_explanation(
            taxonomy_matches={"Gorpcore": 0.91},
            reference_matches=[{"id": "r1", "title": "Arc'teryx shell", "score": 0.88}],
            layer1_tags=None,
            layer2_tags=None,
        )

        assert result is not None
        assert "Arc'teryx shell" in result


class TestEnrichCapture:
    def test_enrich_capture_returns_required_keys(self) -> None:
        from services.enrich_service import enrich_capture

        with (
            patch("services.enrich_service.get_image_embedding", return_value=[1.0, 0.0, 0.0]),
            patch(
                "services.enrich_service.get_layer1_tags_with_model",
                return_value=(["black"], "gemini-2.5-flash"),
            ),
            patch(
                "services.enrich_service.get_layer2_tags_with_model",
                return_value=(["wide-leg"], "gemini-2.5-flash"),
            ),
            patch("services.enrich_service.classify", return_value={"Gorpcore": 0.91}),
            patch("services.enrich_service.extract_palette", return_value=["#000000"]),
            patch(
                "services.enrich_service.get_reference_matches",
                return_value=[{"id": "r1", "title": "Look 1", "score": 0.9}],
            ),
            patch(
                "services.enrich_service.generate_reference_explanation",
                return_value="Reads closest to Gorpcore.",
            ),
        ):
            result = enrich_capture(b"fake_image_bytes", session_id=None)

        required = {
            "embedding",
            "taxonomy_matches",
            "layer1_tags",
            "layer2_tags",
            "tags",
            "reference_matches",
            "reference_explanation",
            "gemini_models",
            "session_id",
        }
        assert required.issubset(result.keys())

    def test_enrich_capture_layer2_none_guard(self) -> None:
        from services.enrich_service import enrich_capture

        with (
            patch("services.enrich_service.get_image_embedding", return_value=[1.0, 0.0, 0.0]),
            patch(
                "services.enrich_service.get_layer1_tags_with_model",
                return_value=(["black"], "gemini-2.5-flash"),
            ),
            patch(
                "services.enrich_service.get_layer2_tags_with_model",
                return_value=(None, None),
            ),
            patch("services.enrich_service.classify", return_value={"Gorpcore": 0.91}),
            patch("services.enrich_service.extract_palette", return_value=["#000000"]),
            patch("services.enrich_service.get_reference_matches", return_value=[]),
            patch("services.enrich_service.generate_reference_explanation", return_value=None),
        ):
            result = enrich_capture(b"fake_image_bytes", session_id=None)

        assert result["layer2_tags"] is None

    def test_enrich_capture_gemini_failure_is_best_effort(self) -> None:
        from services.enrich_service import enrich_capture

        with (
            patch("services.enrich_service.get_image_embedding", return_value=[1.0, 0.0, 0.0]),
            patch(
                "services.enrich_service.get_layer1_tags_with_model",
                side_effect=RuntimeError("Gemini down"),
            ),
            patch("services.enrich_service.classify", return_value={"Gorpcore": 0.91}),
            patch("services.enrich_service.extract_palette", return_value=["#000000"]),
            patch("services.enrich_service.get_reference_matches", return_value=[]),
            patch("services.enrich_service.generate_reference_explanation", return_value=None),
        ):
            result = enrich_capture(b"fake_image_bytes", session_id="session-1")

        assert result["layer1_tags"] is None
        assert result["layer2_tags"] is None
        assert result["session_id"] == "session-1"

    def test_enrich_capture_persists_session_id(self) -> None:
        from services.enrich_service import enrich_capture

        with (
            patch("services.enrich_service.get_image_embedding", return_value=[1.0, 0.0, 0.0]),
            patch(
                "services.enrich_service.get_layer1_tags_with_model",
                return_value=([], None),
            ),
            patch("services.enrich_service.classify", return_value={"Gorpcore": 0.91}),
            patch("services.enrich_service.extract_palette", return_value=["#000000"]),
            patch("services.enrich_service.get_reference_matches", return_value=[]),
            patch("services.enrich_service.generate_reference_explanation", return_value=None),
        ):
            result = enrich_capture(b"fake_image_bytes", session_id="session-1")

        assert result["session_id"] == "session-1"
