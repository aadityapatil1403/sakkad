import importlib.util
import sys
from pathlib import Path
from types import ModuleType


MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "evaluate_classifier.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("evaluate_classifier_test_module", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_missing_text_features_are_marked_explicitly() -> None:
    module = _load_module()
    config = module.Config("fashion_text_layer1", 0.0, 1.0, "layer1")
    data = {
        "entry": {
            "expected_primary_labels": ["Western Americana"],
            "acceptable_secondary_labels": ["Cowboy Core"],
        },
        "layer1": [],
        "layer2": [],
    }

    result = module._missing_text_result(
        image_name="western.jpg",
        data=data,
        config=config,
    )

    assert result["predictions"] == []
    assert result["missing_text_features"] is True
    assert result["missing_text_variant"] == "layer1"
    assert result["top1_hit"] is False
    assert result["primary_rank"] is None
