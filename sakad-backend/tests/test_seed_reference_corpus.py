import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch


MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "seed_reference_corpus.py"


@contextmanager
def _load_module() -> ModuleType:
    original_modules = {
        name: sys.modules.get(name)
        for name in ("dotenv", "services", "services.clip_service", "services.supabase_client")
    }

    dotenv_stub = ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None

    services_pkg = ModuleType("services")
    services_pkg.__path__ = []

    clip_stub = ModuleType("services.clip_service")
    clip_stub.get_text_embedding = lambda text: [0.1, 0.2]

    supabase_stub = ModuleType("services.supabase_client")
    supabase_stub.supabase = SimpleNamespace()

    sys.modules["dotenv"] = dotenv_stub
    sys.modules["services"] = services_pkg
    sys.modules["services.clip_service"] = clip_stub
    sys.modules["services.supabase_client"] = supabase_stub

    try:
        spec = importlib.util.spec_from_file_location("seed_reference_corpus_test_module", MODULE_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module
    finally:
        for name, original in original_modules.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


def test_delete_stale_rows_removes_only_missing_ids() -> None:
    with _load_module() as seed_reference_corpus:
        delete_query = MagicMock()
        delete_query.eq.return_value.execute.return_value = SimpleNamespace(data=[{"ok": True}])

        table = MagicMock()
        table.delete.return_value = delete_query

        seed_reference_corpus.supabase = MagicMock()
        seed_reference_corpus.supabase.table.return_value = table

        existing = {
            "a": {"id": "a"},
            "b": {"id": "b"},
            "c": {"id": "c"},
        }

        deleted_count = seed_reference_corpus.delete_stale_rows(existing, {"a", "c"})

        assert deleted_count == 1
        seed_reference_corpus.supabase.table.assert_called_with("reference_corpus")
        delete_query.eq.assert_called_once_with("id", "b")


def test_build_embedding_text_includes_core_fields() -> None:
    with _load_module() as seed_reference_corpus:
        entry = {
            "id": "stable-id",
            "designer": "Yohji Yamamoto",
            "brand": "Yohji Yamamoto",
            "collection_or_era": "1990s tailoring",
            "title": "Monastic black drape tailoring",
            "description": "Severe black tailoring with elongated lines.",
            "taxonomy_tags": ["avant_garde", "draping"],
            "metadata": {"bucket": "avant_garde"},
        }

        text = seed_reference_corpus.build_embedding_text(entry)

        assert "Designer: Yohji Yamamoto" in text
        assert "Collection or era: 1990s tailoring" in text
        assert "Bucket: avant_garde" in text
        assert "Tags: avant_garde, draping" in text


def test_build_row_persists_json_embedding_and_metadata_defaults() -> None:
    with _load_module() as seed_reference_corpus:
        seed_reference_corpus.get_text_embedding = MagicMock(return_value=[0.9, 0.1])

        entry = {
            "id": "stable-id",
            "designer": "Martin Margiela",
            "brand": "Maison Martin Margiela",
            "collection_or_era": "Artisanal",
            "title": "Deconstruction and exposed process",
            "description": "Visible process and reconstructed garments.",
            "taxonomy_tags": ["deconstruction"],
            "image_url": None,
        }

        row = seed_reference_corpus.build_row(entry)

        assert row["id"] == "stable-id"
        assert row["embedding"] == [0.9, 0.1]
        assert row["taxonomy_tags"] == ["deconstruction"]
        assert row["metadata"] == {}


def test_validate_entry_rejects_missing_required_fields() -> None:
    with _load_module() as seed_reference_corpus:
        entry = {
            "id": "stable-id",
            "designer": "Rick Owens",
        }

        try:
            seed_reference_corpus.validate_entry(entry, 1)
        except ValueError as exc:
            assert "missing required field(s)" in str(exc)
        else:
            raise AssertionError("validate_entry should reject incomplete entries")


def test_parse_args_can_keep_stale_rows_when_requested() -> None:
    with _load_module() as seed_reference_corpus, patch.object(
        sys, "argv", ["seed_reference_corpus.py", "--keep-stale"]
    ):
        args = seed_reference_corpus.parse_args()

    assert args.keep_stale is True


def test_main_deletes_stale_rows_only_after_successful_upserts() -> None:
    with _load_module() as seed_reference_corpus:
        seed_reference_corpus.parse_args = MagicMock(return_value=SimpleNamespace(keep_stale=False))
        seed_reference_corpus.load_entries = MagicMock(return_value=[
            {
                "id": "a",
                "designer": "Designer A",
                "brand": "Brand A",
                "collection_or_era": "Era A",
                "title": "Look A",
                "description": "Desc A",
                "taxonomy_tags": ["tag-a"],
            }
        ])
        seed_reference_corpus.fetch_existing_rows = MagicMock(return_value={"stale": {"id": "stale"}})
        seed_reference_corpus.build_row = MagicMock(return_value={"id": "a", "embedding": [0.1, 0.2]})
        seed_reference_corpus.delete_stale_rows = MagicMock(return_value=1)

        table = MagicMock()
        table.upsert.return_value.execute.return_value = SimpleNamespace(data=[{"id": "a"}])
        seed_reference_corpus.supabase = MagicMock()
        seed_reference_corpus.supabase.table.return_value = table

        seed_reference_corpus.main()

        seed_reference_corpus.delete_stale_rows.assert_called_once_with(
            {"stale": {"id": "stale"}},
            {"a"},
        )
        assert table.upsert.return_value.execute.called
