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

    supabase_stub = ModuleType("services.supabase_client")
    supabase_stub.supabase = SimpleNamespace()

    sys.modules["dotenv"] = dotenv_stub
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


def test_delete_stale_rows_removes_only_missing_labels() -> None:
    with _load_module() as seed_taxonomy:
        delete_query = MagicMock()
        delete_query.eq.return_value.execute.return_value = SimpleNamespace(data=[{"ok": True}])

        table = MagicMock()
        table.delete.return_value = delete_query

        seed_taxonomy.supabase = MagicMock()
        seed_taxonomy.supabase.table.return_value = table

        existing = {
            "Western Americana": {"id": "1", "label": "Western Americana"},
            "Memphis Design": {"id": "2", "label": "Memphis Design"},
            "Vaporwave": {"id": "3", "label": "Vaporwave"},
        }

        deleted_count = seed_taxonomy.delete_stale_rows(existing, {"Western Americana", "Vaporwave"})

        assert deleted_count == 1
        seed_taxonomy.supabase.table.assert_called_with("taxonomy")
        delete_query.eq.assert_called_once_with("label", "Memphis Design")


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
