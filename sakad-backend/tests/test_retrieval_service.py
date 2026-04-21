from types import SimpleNamespace
from unittest.mock import patch

from services import retrieval_service


def test_retrieval_returns_stable_shape_and_ranking() -> None:
    rows = [
        {
            "id": "ref-1",
            "designer": "Designer A",
            "brand": "Brand A",
            "collection_or_era": "SS99",
            "title": "Look 1",
            "description": "First look",
            "image_url": "https://example.com/1.jpg",
            "embedding": [1.0, 0.0],
        },
        {
            "id": "ref-2",
            "designer": "Designer B",
            "brand": "Brand B",
            "collection_or_era": "FW02",
            "title": "Look 2",
            "description": "Second look",
            "image_url": "https://example.com/2.jpg",
            "embedding": [0.6, 0.8],
        },
    ]

    with patch("services.retrieval_service._reference_cache", None), \
         patch("services.retrieval_service.supabase") as mock_supa:
        mock_supa.table().select().execute.return_value = SimpleNamespace(data=rows)

        result = retrieval_service.get_reference_matches([1.0, 0.0], limit=2)

    assert [item["id"] for item in result] == ["ref-1", "ref-2"]
    for item in result:
        assert set(item) == {
            "id",
            "designer",
            "brand",
            "collection_or_era",
            "title",
            "description",
            "image_url",
            "score",
        }


def test_empty_corpus_returns_empty_list_and_logs() -> None:
    with patch("services.retrieval_service._reference_cache", None), \
         patch("services.retrieval_service.supabase") as mock_supa, \
         patch("services.retrieval_service.logger") as mock_logger:
        mock_supa.table().select().execute.return_value = SimpleNamespace(data=[])

        result = retrieval_service.get_reference_matches([1.0, 0.0])

    assert result == []
    mock_logger.info.assert_called()


def test_malformed_rows_do_not_crash_request_path() -> None:
    rows = [
        {
            "id": "bad-row",
            "designer": "Broken",
            "brand": "Broken",
            "collection_or_era": "Broken",
            "title": "Broken",
            "description": "Broken",
            "image_url": None,
            "embedding": "not-a-vector",
        },
        {
            "id": "good-row",
            "designer": "Designer A",
            "brand": "Brand A",
            "collection_or_era": "SS99",
            "title": "Look 1",
            "description": "First look",
            "image_url": None,
            "embedding": [1.0, 0.0],
        },
    ]

    with patch("services.retrieval_service._reference_cache", None), \
         patch("services.retrieval_service.supabase") as mock_supa:
        mock_supa.table().select().execute.return_value = SimpleNamespace(data=rows)

        result = retrieval_service.get_reference_matches([1.0, 0.0])

    assert [item["id"] for item in result] == ["good-row"]


def test_limit_handling_respects_requested_count() -> None:
    rows = [
        {
            "id": f"ref-{idx}",
            "designer": f"Designer {idx}",
            "brand": f"Brand {idx}",
            "collection_or_era": f"Era {idx}",
            "title": f"Look {idx}",
            "description": f"Description {idx}",
            "image_url": None,
            "embedding": [1.0 - (idx * 0.1), idx * 0.1],
        }
        for idx in range(4)
    ]

    with patch("services.retrieval_service._reference_cache", None), \
         patch("services.retrieval_service.supabase") as mock_supa:
        mock_supa.table().select().execute.return_value = SimpleNamespace(data=rows)

        result = retrieval_service.get_reference_matches([1.0, 0.0], limit=2)

    assert len(result) == 2


def test_missing_reference_corpus_degrades_to_empty_results() -> None:
    with patch("services.retrieval_service._reference_cache", None), \
         patch("services.retrieval_service._reference_corpus_available", True), \
         patch("services.retrieval_service.supabase") as mock_supa, \
         patch("services.retrieval_service.logger") as mock_logger:
        mock_supa.table().select().execute.side_effect = RuntimeError("relation reference_corpus does not exist")

        result = retrieval_service.get_reference_matches([1.0, 0.0])

    assert result == []
    mock_logger.warning.assert_called()


def test_transient_reference_corpus_error_does_not_disable_future_retries() -> None:
    rows = [{
        "id": "ref-1",
        "designer": "Designer A",
        "brand": "Brand A",
        "collection_or_era": "SS99",
        "title": "Look 1",
        "description": "First look",
        "image_url": "https://example.com/1.jpg",
        "embedding": [1.0, 0.0],
    }]

    with patch("services.retrieval_service._reference_cache", None), \
         patch("services.retrieval_service._reference_corpus_available", True), \
         patch("services.retrieval_service.supabase") as mock_supa:
        mock_supa.table().select().execute.side_effect = [
            RuntimeError("temporary timeout"),
            SimpleNamespace(data=rows),
        ]

        first_result = retrieval_service.get_reference_matches([1.0, 0.0])
        second_result = retrieval_service.get_reference_matches([1.0, 0.0])

    assert first_result == []
    assert [item["id"] for item in second_result] == ["ref-1"]
