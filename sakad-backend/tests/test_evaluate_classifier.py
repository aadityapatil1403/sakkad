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


def test_filter_taxonomy_domains_keeps_requested_domains_only() -> None:
    module = _load_module()
    taxonomy = [
        {"label": "Tailoring", "domain": "fashion_streetwear"},
        {"label": "Botanical Organic", "domain": "abstract_visual"},
        {"label": "Rothko", "domain": "art_reference"},
    ]

    filtered = module.filter_taxonomy_domains(
        taxonomy,
        {"fashion_streetwear", "abstract_visual"},
    )

    assert [row["label"] for row in filtered] == ["Tailoring", "Botanical Organic"]


def test_parse_args_defaults_to_fashion_only_domain() -> None:
    module = _load_module()
    original_argv = sys.argv
    sys.argv = ["evaluate_classifier.py"]
    try:
        args = module.parse_args()
    finally:
        sys.argv = original_argv

    assert args.domains == ["fashion_streetwear"]


def test_parse_args_accepts_multiple_domains() -> None:
    module = _load_module()
    original_argv = sys.argv
    sys.argv = [
        "evaluate_classifier.py",
        "--domains",
        "fashion_streetwear",
        "abstract_visual",
    ]
    try:
        args = module.parse_args()
    finally:
        sys.argv = original_argv

    assert args.domains == ["fashion_streetwear", "abstract_visual"]


def test_classify_caps_mixed_domain_predictions() -> None:
    module = _load_module()
    taxonomy = [
        {"label": "Tailoring", "domain": "fashion_streetwear", "embedding": module.np.array([1.0, 0.0], dtype=module.np.float32)},
        {"label": "Old Money", "domain": "fashion_streetwear", "embedding": module.np.array([0.9, 0.0], dtype=module.np.float32)},
        {"label": "Workwear", "domain": "fashion_streetwear", "embedding": module.np.array([0.8, 0.0], dtype=module.np.float32)},
        {"label": "Streetwear", "domain": "fashion_streetwear", "embedding": module.np.array([0.7, 0.0], dtype=module.np.float32)},
        {"label": "Botanical Organic", "domain": "abstract_visual", "embedding": module.np.array([0.95, 0.0], dtype=module.np.float32)},
        {"label": "Wet Pavement", "domain": "abstract_visual", "embedding": module.np.array([0.85, 0.0], dtype=module.np.float32)},
    ]

    predictions = module.classify(
        taxonomy=taxonomy,
        image_embedding=module.np.array([1.0, 0.0], dtype=module.np.float32),
        text_embedding=None,
        image_weight=1.0,
        text_weight=0.0,
    )

    assert list(predictions) == [
        "Tailoring",
        "Botanical Organic",
        "Old Money",
        "Workwear",
    ]
