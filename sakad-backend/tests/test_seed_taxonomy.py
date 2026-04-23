import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch


MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "seed_taxonomy.py"


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

    config_stub = ModuleType("config")
    config_stub.settings = SimpleNamespace(TAXONOMY_EMBEDDING_MODEL="Marqo/marqo-fashionSigLIP")

    supabase_stub = ModuleType("services.supabase_client")
    supabase_stub.supabase = SimpleNamespace()

    sys.modules["dotenv"] = dotenv_stub
    sys.modules["config"] = config_stub
    sys.modules["services"] = services_pkg
    sys.modules["services.clip_service"] = clip_stub
    sys.modules["services.supabase_client"] = supabase_stub

    try:
        spec = importlib.util.spec_from_file_location("seed_taxonomy_test_module", MODULE_PATH)
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


def test_delete_stale_rows_removes_only_missing_labels_in_represented_domains() -> None:
    with _load_module() as seed_taxonomy:
        delete_query = MagicMock()
        delete_query.in_.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[{"ok": True}])

        table = MagicMock()
        table.delete.return_value = delete_query

        seed_taxonomy.supabase = MagicMock()
        seed_taxonomy.supabase.table.return_value = table

        existing = {
            "Western Americana": {"id": "1", "label": "Western Americana"},
            "Memphis Design": {"id": "2", "label": "Memphis Design"},
            "Vaporwave": {"id": "3", "label": "Vaporwave"},
        }

        deleted_count = seed_taxonomy.delete_stale_rows(
            existing,
            {"Western Americana", "Vaporwave"},
            domains={"fashion_streetwear", "abstract_visual"},
        )

        assert deleted_count == 1
        seed_taxonomy.supabase.table.assert_called_with("taxonomy")
        delete_query.in_.assert_called_once_with("domain", ["abstract_visual", "fashion_streetwear"])
        delete_query.in_.return_value.eq.assert_called_once_with("label", "Memphis Design")


def test_fetch_existing_rows_filters_by_represented_domains() -> None:
    with _load_module() as seed_taxonomy:
        execute_query = MagicMock()
        execute_query.execute.return_value = SimpleNamespace(
            data=[
                {"id": "1", "label": "Western Americana"},
                {"id": "2", "label": "Wet Pavement"},
            ]
        )
        select_query = MagicMock()
        select_query.in_.return_value = execute_query

        seed_taxonomy.supabase = MagicMock()
        seed_taxonomy.supabase.table.return_value.select.return_value = select_query

        rows = seed_taxonomy.fetch_existing_rows({"fashion_streetwear", "abstract_visual"})

        assert rows == {
            "Western Americana": {"id": "1", "label": "Western Americana"},
            "Wet Pavement": {"id": "2", "label": "Wet Pavement"},
        }
        seed_taxonomy.supabase.table.assert_called_once_with("taxonomy")
        seed_taxonomy.supabase.table.return_value.select.assert_called_once_with("id, label")
        select_query.in_.assert_called_once_with("domain", ["abstract_visual", "fashion_streetwear"])


def test_build_row_preserves_existing_id_and_references() -> None:
    with _load_module() as seed_taxonomy:
        seed_taxonomy.get_text_embedding = MagicMock(return_value=[0.9, 0.1])

        entry = {
            "label": "Cowboy Core",
            "domain": "fashion_streetwear",
            "description": "western denim and cowboy boots",
            "visual_references": ["Levi's western"],
        }

        row = seed_taxonomy.build_row(entry, existing_id="stable-id")

        assert row["id"] == "stable-id"
        assert row["label"] == "Cowboy Core"
        assert row["related_references"] == ["Levi's western"]
        assert row["embedding"] == [0.9, 0.1]
        assert row["embedding_model"] == "Marqo/marqo-fashionSigLIP"


def test_build_row_generates_uuid_for_new_label() -> None:
    with _load_module() as seed_taxonomy:
        seed_taxonomy.get_text_embedding = MagicMock(return_value=[0.3, 0.7])

        entry = {
            "label": "Western Americana",
            "domain": "fashion_streetwear",
            "description": "ranchwear and rodeo tailoring",
        }

        row = seed_taxonomy.build_row(entry, existing_id=None)

        assert isinstance(row["id"], str)
        assert len(row["id"]) == 36
        assert row["related_references"] == []


def test_parse_args_defaults_to_replacing_stale_rows() -> None:
    with _load_module() as seed_taxonomy, patch.object(sys, "argv", ["seed_taxonomy.py"]):
        args = seed_taxonomy.parse_args()

    assert args.keep_stale is False


def test_parse_args_can_keep_stale_rows_when_requested() -> None:
    with _load_module() as seed_taxonomy, patch.object(sys, "argv", ["seed_taxonomy.py", "--keep-stale"]):
        args = seed_taxonomy.parse_args()

    assert args.keep_stale is True


def test_get_seed_domains_returns_all_represented_domains() -> None:
    with _load_module() as seed_taxonomy:
        domains = seed_taxonomy.get_seed_domains(
            [
                {"label": "A", "domain": "fashion_streetwear"},
                {"label": "B", "domain": "abstract_visual"},
                {"label": "C", "domain": "fashion_streetwear"},
            ]
        )

        assert domains == {"fashion_streetwear", "abstract_visual"}


def test_main_fetches_and_deletes_with_all_represented_domains() -> None:
    with _load_module() as seed_taxonomy:
        seed_taxonomy.load_entries = MagicMock(
            return_value=[
                {"label": "A", "domain": "fashion_streetwear", "description": "desc A"},
                {"label": "B", "domain": "abstract_visual", "description": "desc B"},
            ]
        )
        seed_taxonomy.fetch_existing_rows = MagicMock(
            return_value={"A": {"id": "1"}, "legacy": {"id": "2"}}
        )
        seed_taxonomy.build_row = MagicMock(side_effect=[{"label": "A"}, {"label": "B"}])
        seed_taxonomy.delete_stale_rows = MagicMock(return_value=1)
        seed_taxonomy.parse_args = MagicMock(return_value=SimpleNamespace(keep_stale=False))

        execute_result = SimpleNamespace(data=[{"ok": True}])
        upsert_query = MagicMock()
        upsert_query.execute.return_value = execute_result
        table = MagicMock()
        table.upsert.return_value = upsert_query

        seed_taxonomy.supabase = MagicMock()
        seed_taxonomy.supabase.table.return_value = table

        seed_taxonomy.main()

        assert table.upsert.call_count == 2
        seed_taxonomy.fetch_existing_rows.assert_called_once_with(
            {"fashion_streetwear", "abstract_visual"}
        )
        seed_taxonomy.delete_stale_rows.assert_called_once_with(
            {"A": {"id": "1"}, "legacy": {"id": "2"}},
            {"A", "B"},
            domains={"fashion_streetwear", "abstract_visual"},
        )
