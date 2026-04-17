#!/usr/bin/env python3
"""Offline classifier ablation harness for the 10-image fashion evaluation set."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from services.clip_service import get_image_embedding, get_text_embedding
from services.gemini_service import get_layer1_tags, get_layer2_tags
from services.supabase_client import supabase

DEFAULT_MANIFEST = BACKEND_DIR / "eval" / "classifier_manifest.json"
TEST_IMAGES_DIR = BACKEND_DIR / "test-images"
FASHION_DOMAIN = "fashion_streetwear"


@dataclass(frozen=True)
class Config:
    name: str
    image_weight: float
    text_weight: float
    text_variant: str | None


CONFIGS: list[Config] = [
    Config("fashion_image_only", 1.0, 0.0, None),
    Config("fashion_text_layer1", 0.0, 1.0, "layer1"),
    Config("fashion_text_layer2", 0.0, 1.0, "layer2"),
    Config("fashion_text_layer1_layer2", 0.0, 1.0, "layer1_layer2"),
    Config("fashion_blend_08_02", 0.8, 0.2, "layer1_layer2"),
    Config("fashion_blend_07_03", 0.7, 0.3, "layer1_layer2"),
    Config("fashion_blend_06_04", 0.6, 0.4, "layer1_layer2"),
    Config("fashion_blend_05_05", 0.5, 0.5, "layer1_layer2"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run classifier ablations on the evaluation image set.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-json", type=Path, default=None)
    return parser.parse_args()


def load_manifest(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text())


def load_taxonomy() -> list[dict[str, Any]]:
    response = supabase.table("taxonomy").select("id, label, domain, embedding").execute()
    rows = response.data or []
    parsed: list[dict[str, Any]] = []
    for row in rows:
        raw = row.get("embedding")
        if raw is None:
            continue
        embedding = ast.literal_eval(raw) if isinstance(raw, str) else raw
        parsed.append({
            "id": row["id"],
            "label": row["label"],
            "domain": row["domain"],
            "embedding": np.array(embedding, dtype=np.float32),
        })
    return parsed


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    return vector / norm if norm > 0 else vector


def build_text_variants(layer1: list[str], layer2: list[str]) -> dict[str, str]:
    variants = {
        "layer1": " ".join(layer1),
        "layer2": " ".join(layer2),
        "layer1_layer2": " ".join(layer1 + layer2),
        "sentence": (
            "fashion outfit with "
            + ", ".join(layer1)
            + ". specific styling details: "
            + ", ".join(layer2)
        ),
    }
    return {name: text for name, text in variants.items() if text.strip()}


def classify(
    *,
    taxonomy: list[dict[str, Any]],
    image_embedding: np.ndarray,
    text_embedding: np.ndarray | None,
    image_weight: float,
    text_weight: float,
) -> list[dict[str, Any]]:
    if text_embedding is None or text_weight == 0.0:
        blended = image_embedding
    elif image_weight == 0.0:
        blended = text_embedding
    else:
        blended = image_weight * image_embedding + text_weight * text_embedding
    blended = normalize_vector(blended)

    text_matrix = np.stack([row["embedding"] for row in taxonomy])
    logits = 100.0 * (text_matrix @ blended)
    exp = np.exp(logits - logits.max())
    probs = exp / exp.sum()
    top_idx = np.argsort(probs)[::-1][:5]
    return [
        {
            "label": taxonomy[i]["label"],
            "domain": taxonomy[i]["domain"],
            "score": round(float(probs[i]), 4),
            "rank": rank + 1,
        }
        for rank, i in enumerate(top_idx)
    ]


def evaluate_prediction(
    *,
    predictions: list[dict[str, Any]],
    expected_primary: list[str],
    acceptable_secondary: list[str],
) -> dict[str, Any]:
    labels = [pred["label"] for pred in predictions]
    all_expected = expected_primary + acceptable_secondary
    top1_hit = labels[0] in all_expected if labels else False
    top3_hit = any(label in all_expected for label in labels[:3])
    primary_rank = next((idx + 1 for idx, label in enumerate(labels) if label in expected_primary), None)
    return {
        "top1_hit": top1_hit,
        "top3_hit": top3_hit,
        "primary_rank": primary_rank,
    }


def mean_rank(ranks: list[int | None]) -> float | None:
    values = [rank for rank in ranks if rank is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def main() -> None:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    taxonomy_fashion = [row for row in load_taxonomy() if row["domain"] == FASHION_DOMAIN]

    per_image_data: dict[str, dict[str, Any]] = {}
    for entry in manifest:
        image_name = entry["image"]
        print(f"Precomputing {image_name}...", flush=True)
        image_path = TEST_IMAGES_DIR / image_name
        image_bytes = image_path.read_bytes()
        image_embedding = normalize_vector(np.array(get_image_embedding(image_bytes), dtype=np.float32))
        layer1 = get_layer1_tags(image_bytes)
        layer2 = get_layer2_tags(image_bytes, layer1) if layer1 else []

        text_variants_raw = build_text_variants(layer1, layer2)
        text_embeddings = {
            name: normalize_vector(np.array(get_text_embedding(text), dtype=np.float32))
            for name, text in text_variants_raw.items()
        }

        per_image_data[image_name] = {
            "entry": entry,
            "layer1": layer1,
            "layer2": layer2,
            "image_embedding": image_embedding,
            "text_embeddings": text_embeddings,
        }

    report: dict[str, Any] = {"configs": []}
    for config in CONFIGS:
        print(f"Scoring config {config.name}...", flush=True)
        image_results = []
        ranks: list[int | None] = []
        top1_hits = 0
        top3_hits = 0

        for image_name, data in per_image_data.items():
            text_embedding = None if config.text_variant is None else data["text_embeddings"].get(config.text_variant)
            predictions = classify(
                taxonomy=taxonomy_fashion,
                image_embedding=data["image_embedding"],
                text_embedding=text_embedding,
                image_weight=config.image_weight,
                text_weight=config.text_weight,
            )
            metrics = evaluate_prediction(
                predictions=predictions,
                expected_primary=data["entry"]["expected_primary_labels"],
                acceptable_secondary=data["entry"].get("acceptable_secondary_labels", []),
            )
            top1_hits += int(metrics["top1_hit"])
            top3_hits += int(metrics["top3_hit"])
            ranks.append(metrics["primary_rank"])
            image_results.append({
                "image": image_name,
                "expected_primary_labels": data["entry"]["expected_primary_labels"],
                "acceptable_secondary_labels": data["entry"].get("acceptable_secondary_labels", []),
                "layer1": data["layer1"],
                "layer2": data["layer2"],
                "predictions": predictions,
                **metrics,
            })

        summary = {
            "config": config.name,
            "image_weight": config.image_weight,
            "text_weight": config.text_weight,
            "text_variant": config.text_variant,
            "top1_hits": top1_hits,
            "top3_hits": top3_hits,
            "mean_primary_rank": mean_rank(ranks),
            "image_results": image_results,
        }
        report["configs"].append(summary)

    report["configs"].sort(
        key=lambda item: (
            -item["top1_hits"],
            -item["top3_hits"],
            item["mean_primary_rank"] if item["mean_primary_rank"] is not None else 999.0,
        )
    )

    for config in report["configs"]:
        print(
            f"{config['config']}: top1={config['top1_hits']}/{len(manifest)} "
            f"top3={config['top3_hits']}/{len(manifest)} "
            f"mean_primary_rank={config['mean_primary_rank']}"
        )

    if args.output_json:
        args.output_json.write_text(json.dumps(report, indent=2))
        print(f"\nWrote report to {args.output_json}")


if __name__ == "__main__":
    main()
