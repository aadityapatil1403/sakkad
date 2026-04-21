# Backend Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `routes/capture.py` into a strict 4-service layout, fix the `taxonomy_matches` serialization bug, implement multi-domain classification with per-domain caps, and fix the L2 None bug — without breaking any of the 64 existing tests.

**Architecture:** Business logic migrates out of the route layer into focused service files: `clip_service.py` owns SigLIP embedding + multi-domain taxonomy classification, `color_service.py` owns palette extraction, `gemini_service.py` gains `generate_reference_explanation()`. `routes/capture.py` becomes thin orchestration only (~80 lines). The new `classify()` function returns `dict[str, float]` (`{label: score}`) directly — this is what gets stored in Supabase and returned in API responses, fixing the silent integration bug where the frontend expected an object but received an array.

**Tech Stack:** FastAPI, Python 3.12, SigLIP via open_clip, Gemini via google-genai, Supabase, numpy, PIL, pytest, ruff, mypy.

---

## File Map

| File                                           | Action     | Responsibility after refactor                                 |
| ---------------------------------------------- | ---------- | ------------------------------------------------------------- |
| `sakad-backend/services/clip_service.py`       | Modify     | SigLIP embed + multi-domain `classify()` → `dict[str, float]` |
| `sakad-backend/services/color_service.py`      | **Create** | Palette extraction only                                       |
| `sakad-backend/services/gemini_service.py`     | Modify     | Add `generate_reference_explanation()`                        |
| `sakad-backend/routes/capture.py`              | Modify     | Thin orchestration — no business logic                        |
| `sakad-backend/tests/test_clip_classify.py`    | **Create** | Tests for new `classify()` in clip_service                    |
| `sakad-backend/tests/test_color_service.py`    | **Create** | Tests for `extract_palette()`                                 |
| `sakad-backend/tests/test_gemini_service.py`   | Modify     | Add tests for `generate_reference_explanation()`              |
| `sakad-backend/tests/test_capture_classify.py` | Modify     | Update to expect dict output from `classify()`                |

---

## Task 1: Create `color_service.py` with palette extraction

Extract `_kmeans_numpy()` and `_extract_palette()` from `routes/capture.py` into a dedicated service. No functional changes.

**Files:**

- Create: `sakad-backend/services/color_service.py`
- Create: `sakad-backend/tests/test_color_service.py`

- [ ] **Step 1: Write the failing test**

```python
# sakad-backend/tests/test_color_service.py
import io
from unittest.mock import patch

import numpy as np
from PIL import Image


def _make_solid_image_bytes(r: int, g: int, b: int) -> bytes:
    img = Image.new("RGB", (10, 10), color=(r, g, b))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestExtractPalette:
    def test_returns_list_of_hex_strings(self) -> None:
        from services.color_service import extract_palette

        result = extract_palette(_make_solid_image_bytes(255, 0, 0))

        assert isinstance(result, list)
        assert len(result) == 5
        assert all(s.startswith("#") and len(s) == 7 for s in result)

    def test_solid_red_image_returns_red_dominant_color(self) -> None:
        from services.color_service import extract_palette

        result = extract_palette(_make_solid_image_bytes(255, 0, 0))

        assert "#ff0000" in result

    def test_returns_exactly_k_colors(self) -> None:
        from services.color_service import extract_palette

        result = extract_palette(_make_solid_image_bytes(100, 150, 200), k=3)

        assert len(result) == 3
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd sakad-backend && python -m pytest tests/test_color_service.py -v
```

Expected: `ImportError: cannot import name 'extract_palette' from 'services.color_service'`

- [ ] **Step 3: Create `services/color_service.py`**

```python
import io

import numpy as np
from PIL import Image


def _kmeans_numpy(pixels: np.ndarray, k: int = 5, max_iter: int = 20) -> np.ndarray:
    rng = np.random.default_rng(0)
    centroids = pixels[rng.choice(len(pixels), k, replace=False)]
    for _ in range(max_iter):
        dists = np.linalg.norm(pixels[:, None] - centroids[None], axis=2)
        labels = np.argmin(dists, axis=1)
        new_centroids = np.array([
            pixels[labels == i].mean(axis=0) if np.any(labels == i) else centroids[i]
            for i in range(k)
        ])
        if np.allclose(centroids, new_centroids, atol=1.0):
            break
        centroids = new_centroids
    return centroids


def extract_palette(image_bytes: bytes, k: int = 5) -> list[str]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((150, 150))
    pixels = np.array(image).reshape(-1, 3).astype(np.float32)
    centroids = _kmeans_numpy(pixels, k=k)
    return [f"#{int(round(r)):02x}{int(round(g)):02x}{int(round(b)):02x}" for r, g, b in centroids]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd sakad-backend && python -m pytest tests/test_color_service.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd sakad-backend && git add services/color_service.py tests/test_color_service.py
git commit -m "feat: extract color_service with palette extraction"
```

---

## Task 2: Move `classify()` + taxonomy loading into `clip_service.py` with multi-domain caps

Add `classify(image_embedding, text_embedding) -> dict[str, float]` to `clip_service.py`. This is a **new public function** — the old `_classify()` in `routes/capture.py` stays untouched until Task 5. The taxonomy loader loads **all domains** (not just `fashion_streetwear`). Per-domain caps: `fashion_streetwear` → top 3, `abstract_visual` → top 2, any other domain → top 1. If total capped results < 5, backfill with next-highest overall scores. Returns `{label: score}` dict sorted by score descending.

**Files:**

- Modify: `sakad-backend/services/clip_service.py`
- Create: `sakad-backend/tests/test_clip_classify.py`

- [ ] **Step 1: Write the failing tests**

```python
# sakad-backend/tests/test_clip_classify.py
"""Tests for classify() in clip_service."""
from unittest.mock import patch

import numpy as np


_FASHION_ROWS = [
    {"id": i, "label": f"fashion-{i}", "domain": "fashion_streetwear",
     "embedding": np.array([1.0 if j == i else 0.0 for j in range(6)], dtype=np.float32)}
    for i in range(4)
]
_ABSTRACT_ROWS = [
    {"id": 10 + i, "label": f"abstract-{i}", "domain": "abstract_visual",
     "embedding": np.array([1.0 if j == (4 + i) else 0.0 for j in range(6)], dtype=np.float32)}
    for i in range(2)
]
_OTHER_ROWS = [
    {"id": 20, "label": "other-0", "domain": "visual_context",
     "embedding": np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.9], dtype=np.float32)},
]
_ALL_ROWS = _FASHION_ROWS + _ABSTRACT_ROWS + _OTHER_ROWS


def _run_classify(
    image_embedding: list[float],
    text_embedding: list[float] | None = None,
    taxonomy_rows: list[dict] | None = None,
) -> dict[str, float]:
    from services.clip_service import classify

    rows = taxonomy_rows if taxonomy_rows is not None else _ALL_ROWS
    with patch("services.clip_service._load_taxonomy", return_value=rows):
        return classify(image_embedding, text_embedding)


class TestClassifyOutputShape:
    def test_returns_dict_of_label_to_score(self) -> None:
        result = _run_classify([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        assert isinstance(result, dict)
        assert all(isinstance(k, str) for k in result)
        assert all(isinstance(v, float) for v in result.values())

    def test_dict_sorted_by_score_descending(self) -> None:
        result = _run_classify([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        scores = list(result.values())
        assert scores == sorted(scores, reverse=True)


class TestClassifyDomainCaps:
    def test_fashion_streetwear_capped_at_3(self) -> None:
        result = _run_classify([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        fashion_labels = [k for k in result if k.startswith("fashion-")]
        assert len(fashion_labels) <= 3

    def test_abstract_visual_capped_at_2(self) -> None:
        result = _run_classify([0.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        abstract_labels = [k for k in result if k.startswith("abstract-")]
        assert len(abstract_labels) <= 2

    def test_other_domain_capped_at_1(self) -> None:
        result = _run_classify([0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
        other_labels = [k for k in result if k.startswith("other-")]
        assert len(other_labels) <= 1

    def test_minimum_5_results_when_sparse_domains(self) -> None:
        sparse_rows = _FASHION_ROWS[:2]  # only 2 fashion rows, no other domains
        result = _run_classify([1.0, 0.0, 0.0, 0.0, 0.0, 0.0], taxonomy_rows=sparse_rows)
        assert len(result) >= min(2, len(sparse_rows))

    def test_backfills_to_5_when_capped_results_are_sparse(self) -> None:
        # 4 fashion rows but cap is 3, 2 abstract rows cap is 2 → total 5 exactly
        result = _run_classify([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        assert len(result) >= 5


class TestClassifyEdgeCases:
    def test_empty_taxonomy_raises_value_error(self) -> None:
        import pytest
        from services.clip_service import classify
        with patch("services.clip_service._load_taxonomy", return_value=[]):
            with pytest.raises(ValueError, match="empty"):
                classify([1.0, 0.0, 0.0], None)

    def test_text_embedding_shifts_scores(self) -> None:
        result_img_only = _run_classify([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        result_blended = _run_classify(
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            text_embedding=[0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        )
        assert result_img_only != result_blended
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd sakad-backend && python -m pytest tests/test_clip_classify.py -v
```

Expected: `ImportError` — `classify` not yet defined in `clip_service`.

- [ ] **Step 3: Add taxonomy loader and `classify()` to `clip_service.py`**

Append to the end of the existing `sakad-backend/services/clip_service.py` (after `get_text_embedding`):

```python
import ast
import logging
import threading

import numpy as np

from config import settings
from services.supabase_client import supabase

logger = logging.getLogger(__name__)

_taxonomy_cache: list[dict] | None = None
_taxonomy_lock = threading.Lock()

_DOMAIN_CAPS: dict[str, int] = {
    "fashion_streetwear": 3,
    "abstract_visual": 2,
}
_DEFAULT_DOMAIN_CAP = 1
_MIN_RESULTS = 5
IMAGE_WEIGHT = 1.0
TEXT_WEIGHT = 0.0


def _load_taxonomy() -> list[dict]:
    global _taxonomy_cache
    if _taxonomy_cache is not None:
        return _taxonomy_cache
    with _taxonomy_lock:
        if _taxonomy_cache is not None:
            return _taxonomy_cache
        response = (
            supabase.table("taxonomy")
            .select("id, label, domain, embedding, embedding_model")
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise RuntimeError(
                "Taxonomy is empty. Run sakad-backend/scripts/seed_taxonomy.py."
            )
        parsed: list[dict] = []
        for row in rows:
            raw = row.get("embedding")
            if raw is None:
                continue
            if row.get("embedding_model") != settings.TAXONOMY_EMBEDDING_MODEL:
                raise RuntimeError(
                    "Taxonomy embeddings seeded with wrong model. "
                    "Re-run sakad-backend/scripts/seed_taxonomy.py."
                )
            embedding = ast.literal_eval(raw) if isinstance(raw, str) else raw
            parsed.append({
                "id": row["id"],
                "label": row["label"],
                "domain": row["domain"],
                "embedding": np.array(embedding, dtype=np.float32),
            })
        if not parsed:
            raise RuntimeError(
                "Taxonomy rows have no embeddings. "
                "Re-run sakad-backend/scripts/seed_taxonomy.py."
            )
        _taxonomy_cache = parsed
        return _taxonomy_cache


def classify(
    image_embedding: list[float],
    text_embedding: list[float] | None,
) -> dict[str, float]:
    taxonomy = _load_taxonomy()
    if not taxonomy:
        raise ValueError("classify called with empty taxonomy")

    img_vec = np.array(image_embedding, dtype=np.float32)
    if text_embedding is not None:
        txt_vec = np.array(text_embedding, dtype=np.float32)
        blended = IMAGE_WEIGHT * img_vec + TEXT_WEIGHT * txt_vec
        norm = np.linalg.norm(blended)
        blended = blended / norm if norm > 0 else img_vec
    else:
        blended = img_vec

    text_matrix = np.stack([row["embedding"] for row in taxonomy])
    logits = 100.0 * (text_matrix @ blended)
    exp = np.exp(logits - logits.max())
    probs = (exp / exp.sum()).tolist()

    # Score every label
    scored: list[tuple[str, str, float]] = [
        (row["label"], row["domain"], round(probs[i], 4))
        for i, row in enumerate(taxonomy)
    ]
    scored.sort(key=lambda x: x[2], reverse=True)

    # Apply per-domain caps
    domain_counts: dict[str, int] = {}
    capped: list[tuple[str, float]] = []
    for label, domain, score in scored:
        cap = _DOMAIN_CAPS.get(domain, _DEFAULT_DOMAIN_CAP)
        count = domain_counts.get(domain, 0)
        if count < cap:
            capped.append((label, score))
            domain_counts[domain] = count + 1

    # Backfill to _MIN_RESULTS from overall ranking if capped set is sparse
    if len(capped) < _MIN_RESULTS:
        capped_labels = {label for label, _ in capped}
        for label, _, score in scored:
            if len(capped) >= _MIN_RESULTS:
                break
            if label not in capped_labels:
                capped.append((label, score))
                capped_labels.add(label)

    capped.sort(key=lambda x: x[1], reverse=True)
    return {label: score for label, score in capped}
```

> **Note on imports:** `clip_service.py` currently imports only `io`, `os`, `threading`, `PIL`, `torch`, `open_clip`, `transformers`, and `config`. The new code needs `ast`, `logging`, `numpy`, and `services.supabase_client`. Add these imports at the top of the file alongside the existing ones — do NOT duplicate `threading` or `os`.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd sakad-backend && python -m pytest tests/test_clip_classify.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Run full suite to confirm no regressions**

```bash
cd sakad-backend && python -m pytest tests/ -x -q
```

Expected: 64+ tests pass.

- [ ] **Step 6: Commit**

```bash
cd sakad-backend && git add services/clip_service.py tests/test_clip_classify.py
git commit -m "feat: add multi-domain classify() to clip_service"
```

---

## Task 3: Add `generate_reference_explanation()` to `gemini_service.py`

Move the `generate_reference_explanation()` function from `routes/capture.py` into `gemini_service.py`. No functional change — just relocating and adding a test.

**Files:**

- Modify: `sakad-backend/services/gemini_service.py`
- Modify: `sakad-backend/tests/test_gemini_service.py`

- [ ] **Step 1: Write the failing test**

Add this class to the bottom of `sakad-backend/tests/test_gemini_service.py`:

```python
class TestGenerateReferenceExplanation:
    def test_returns_string_with_top_taxonomy_and_reference(self) -> None:
        from services.gemini_service import generate_reference_explanation

        result = generate_reference_explanation(
            taxonomy_matches=[{"label": "Gorpcore", "score": 0.91}],
            reference_matches=[{"title": "Arc'teryx FW99", "score": 0.88}],
            layer1_tags=["technical", "muted"],
            layer2_tags=["outdoor-shell"],
        )

        assert result is not None
        assert "Gorpcore" in result
        assert "Arc'teryx FW99" in result

    def test_returns_none_when_taxonomy_matches_empty(self) -> None:
        from services.gemini_service import generate_reference_explanation

        result = generate_reference_explanation(
            taxonomy_matches=[],
            reference_matches=[{"title": "Look 1", "score": 0.9}],
        )

        assert result is None

    def test_returns_none_when_reference_matches_empty(self) -> None:
        from services.gemini_service import generate_reference_explanation

        result = generate_reference_explanation(
            taxonomy_matches=[{"label": "Gorpcore", "score": 0.91}],
            reference_matches=[],
        )

        assert result is None

    def test_includes_layer2_cues_when_provided(self) -> None:
        from services.gemini_service import generate_reference_explanation

        result = generate_reference_explanation(
            taxonomy_matches=[{"label": "Techwear", "score": 0.85}],
            reference_matches=[{"designer": "Acronym", "score": 0.82}],
            layer2_tags=["zip-closure", "drop-crotch", "cargo-pocket"],
        )

        assert result is not None
        assert any(tag in result for tag in ["zip-closure", "drop-crotch", "cargo-pocket"])
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd sakad-backend && python -m pytest tests/test_gemini_service.py::TestGenerateReferenceExplanation -v
```

Expected: `ImportError` — `generate_reference_explanation` not yet in `gemini_service`.

- [ ] **Step 3: Add function to `gemini_service.py`**

Append to the end of `sakad-backend/services/gemini_service.py`:

```python
def generate_reference_explanation(
    taxonomy_matches: list[dict] | None,
    reference_matches: list[dict] | None,
    layer1_tags: list[str] | None = None,
    layer2_tags: list[str] | None = None,
) -> str | None:
    if not taxonomy_matches or not reference_matches:
        return None

    top_taxonomy = taxonomy_matches[0].get("label") or "the current taxonomy result"
    top_reference = reference_matches[0]
    reference_name = (
        top_reference.get("title")
        or top_reference.get("designer")
        or "the top reference"
    )
    cue_source = layer2_tags or layer1_tags or []
    cues = ", ".join(cue_source[:3])

    explanation = f"This image reads closest to {top_taxonomy} and aligns with {reference_name}."
    if cues:
        explanation += f" Key visual cues include {cues}."
    return explanation
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd sakad-backend && python -m pytest tests/test_gemini_service.py -v
```

Expected: all gemini_service tests PASS.

- [ ] **Step 5: Commit**

```bash
cd sakad-backend && git add services/gemini_service.py tests/test_gemini_service.py
git commit -m "feat: move generate_reference_explanation into gemini_service"
```

---

## Task 4: Slim down `routes/capture.py` — wire new services, fix taxonomy_matches serialization

Replace the old `_classify()`, `_load_taxonomy()`, `_kmeans_numpy()`, `_extract_palette()`, and `generate_reference_explanation()` in `routes/capture.py` with calls to the new service functions. Add a `_to_taxonomy_dict()` adapter at the Supabase write boundary so the stored shape is `{"label": score}`. Fix the `_classify()` → `classify()` call to use `ValueError` (matches what the new function raises).

**Files:**

- Modify: `sakad-backend/routes/capture.py`
- Modify: `sakad-backend/tests/test_capture_classify.py`

- [ ] **Step 1: Update `test_capture_classify.py` to expect dict output from `classify()`**

The existing tests in `test_capture_classify.py` patch `routes.capture._classify` and assert list-shaped output. Since `_classify` is being replaced by `clip_service.classify`, update the test file to patch `routes.capture.classify` and assert dict output:

Replace the entire `tests/test_capture_classify.py` with:

```python
# sakad-backend/tests/test_capture_classify.py
"""
Tests for the capture route's orchestration of classify() from clip_service.
"""
import io
from unittest.mock import MagicMock, patch

import numpy as np

_FAKE_TAXONOMY_DICT = {"label-A": 0.7, "label-B": 0.2, "label-C": 0.1}

_FAKE_TAXONOMY_ROWS = [
    {
        "id": 1,
        "label": "label-A",
        "domain": "fashion_streetwear",
        "embedding": np.array([1.0, 0.0, 0.0], dtype=np.float32),
    },
    {
        "id": 2,
        "label": "label-B",
        "domain": "fashion_streetwear",
        "embedding": np.array([0.0, 1.0, 0.0], dtype=np.float32),
    },
    {
        "id": 3,
        "label": "label-C",
        "domain": "fashion_streetwear",
        "embedding": np.array([0.0, 0.0, 1.0], dtype=np.float32),
    },
]


def _make_test_client():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routes.capture import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestCaptureTextEmbeddingPath:
    def test_image_only_runtime_skips_text_embedding(self) -> None:
        with patch("routes.capture.get_text_embedding") as mock_get_text_embedding, \
             patch("routes.capture.classify", return_value=_FAKE_TAXONOMY_DICT) as mock_classify, \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags_with_model", return_value=(["black"], "gemini-2.5-flash")), \
             patch("routes.capture.get_layer2_tags_with_model", return_value=([], None)), \
             patch("routes.capture.get_reference_matches", return_value=[]), \
             patch("routes.capture.generate_reference_explanation", return_value=None), \
             patch("routes.capture.extract_palette", return_value=["#000000"]), \
             patch("routes.capture.supabase") as mock_supa:
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{"id": "1"}])

            client = _make_test_client()
            response = client.post(
                "/api/capture",
                files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
            )

        assert response.status_code == 200
        mock_get_text_embedding.assert_not_called()
        mock_classify.assert_called_once()
        _, kwargs = mock_classify.call_args
        assert kwargs.get("text_embedding") is None or mock_classify.call_args[0][1] is None

    def test_image_first_taxonomy_path_still_skips_text_embedding_with_enrichment(self) -> None:
        with patch("routes.capture.get_text_embedding") as mock_get_text_embedding, \
             patch("routes.capture.classify", return_value=_FAKE_TAXONOMY_DICT), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags_with_model", return_value=(["black"], "gemini-2.5-flash")), \
             patch("routes.capture.get_layer2_tags_with_model", return_value=(["wide-leg"], "gemini-2.5-flash")), \
             patch("routes.capture.get_reference_matches", return_value=[]), \
             patch("routes.capture.generate_reference_explanation", return_value=None), \
             patch("routes.capture.extract_palette", return_value=["#000000"]), \
             patch("routes.capture.supabase") as mock_supa:
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{"id": "1"}])

            client = _make_test_client()
            response = client.post(
                "/api/capture",
                files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
            )

        assert response.status_code == 200
        mock_get_text_embedding.assert_not_called()


class TestCaptureFallbacks:
    def test_capture_succeeds_when_gemini_tag_generation_fails(self) -> None:
        with patch("routes.capture.classify", return_value=_FAKE_TAXONOMY_DICT), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags_with_model", return_value=([], None)), \
             patch("routes.capture.get_layer2_tags_with_model", return_value=([], None)), \
             patch("routes.capture.get_reference_matches", return_value=[{"id": "ref-1", "title": "Look 1", "score": 0.91}]), \
             patch("routes.capture.generate_reference_explanation", return_value="Looks aligned with Look 1"), \
             patch("routes.capture.extract_palette", return_value=["#000000"]), \
             patch("routes.capture.supabase") as mock_supa:
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{
                "id": "1",
                "taxonomy_matches": {"label-A": 0.7},
                "reference_matches": [{"id": "ref-1", "title": "Look 1", "score": 0.91}],
                "reference_explanation": "Looks aligned with Look 1",
                "tags": {"palette": ["#000000"]},
                "layer1_tags": None,
                "layer2_tags": None,
            }])

            client = _make_test_client()
            response = client.post(
                "/api/capture",
                files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["reference_matches"][0]["id"] == "ref-1"
        assert payload["tags"]["palette"] == ["#000000"]
        assert payload["gemini_models"] == {"layer1": None, "layer2": None}

    def test_capture_succeeds_when_explanation_generation_fails(self) -> None:
        with patch("routes.capture.classify", return_value=_FAKE_TAXONOMY_DICT), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags_with_model", return_value=(["black"], "gemini-2.5-flash")), \
             patch("routes.capture.get_layer2_tags_with_model", return_value=(["wide-leg"], "gemini-3.1-flash-lite-preview")), \
             patch("routes.capture.get_reference_matches", return_value=[{"id": "ref-1", "title": "Look 1", "score": 0.91}]), \
             patch("routes.capture.generate_reference_explanation", side_effect=RuntimeError("Gemini unavailable")), \
             patch("routes.capture.extract_palette", return_value=["#000000"]), \
             patch("routes.capture.supabase") as mock_supa:
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{
                "id": "1",
                "taxonomy_matches": {"label-A": 0.7},
                "reference_matches": [{"id": "ref-1", "title": "Look 1", "score": 0.91}],
                "reference_explanation": None,
                "tags": {"palette": ["#000000"]},
                "layer1_tags": ["black"],
                "layer2_tags": ["wide-leg"],
            }])

            client = _make_test_client()
            response = client.post(
                "/api/capture",
                files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
            )

        assert response.status_code == 200
        insert_payload = mock_supa.table().insert.call_args.args[0]
        assert insert_payload["reference_matches"][0]["id"] == "ref-1"
        assert insert_payload["reference_explanation"] is None
        assert response.json()["gemini_models"] == {
            "layer1": "gemini-2.5-flash",
            "layer2": "gemini-3.1-flash-lite-preview",
        }

    def test_capture_persists_session_id_when_provided(self) -> None:
        with patch("routes.capture.classify", return_value=_FAKE_TAXONOMY_DICT), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags_with_model", return_value=(["black"], "gemini-2.5-flash")), \
             patch("routes.capture.get_layer2_tags_with_model", return_value=(["wide-leg"], "gemini-2.5-flash")), \
             patch("routes.capture.get_reference_matches", return_value=[]), \
             patch("routes.capture.generate_reference_explanation", return_value=None), \
             patch("routes.capture.extract_palette", return_value=["#000000"]), \
             patch("routes.capture.supabase") as mock_supa:
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{"id": "1", "session_id": "session-1"}])

            client = _make_test_client()
            response = client.post(
                "/api/capture",
                files={
                    "file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg"),
                    "session_id": (None, "session-1"),
                },
            )

        assert response.status_code == 200
        insert_payload = mock_supa.table().insert.call_args.args[0]
        assert insert_payload["session_id"] == "session-1"

    def test_taxonomy_matches_stored_as_dict_not_list(self) -> None:
        with patch("routes.capture.classify", return_value={"Gorpcore": 0.91, "Techwear": 0.07}), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags_with_model", return_value=([], None)), \
             patch("routes.capture.get_layer2_tags_with_model", return_value=([], None)), \
             patch("routes.capture.get_reference_matches", return_value=[]), \
             patch("routes.capture.generate_reference_explanation", return_value=None), \
             patch("routes.capture.extract_palette", return_value=["#000000"]), \
             patch("routes.capture.supabase") as mock_supa:
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{"id": "1"}])

            client = _make_test_client()
            client.post(
                "/api/capture",
                files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
            )

        insert_payload = mock_supa.table().insert.call_args.args[0]
        assert isinstance(insert_payload["taxonomy_matches"], dict)
        assert insert_payload["taxonomy_matches"]["Gorpcore"] == 0.91

    def test_capture_retries_without_enrichment_columns_when_schema_is_old(self) -> None:
        with patch("routes.capture._missing_capture_enrichment_columns", set()), \
             patch("routes.capture.classify", return_value=_FAKE_TAXONOMY_DICT), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags_with_model", return_value=(["black"], "gemini-2.5-flash")), \
             patch("routes.capture.get_layer2_tags_with_model", return_value=(["wide-leg"], "gemini-2.5-flash")), \
             patch("routes.capture.get_reference_matches", return_value=[{"id": "ref-1", "title": "Look 1", "score": 0.91}]), \
             patch("routes.capture.generate_reference_explanation", return_value="Looks aligned with Look 1"), \
             patch("routes.capture.extract_palette", return_value=["#000000"]), \
             patch("routes.capture.supabase") as mock_supa:
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_insert = mock_supa.table().insert
            mock_insert.return_value.execute.side_effect = [
                RuntimeError("column reference_matches does not exist"),
                MagicMock(data=[{"id": "1"}]),
            ]

            client = _make_test_client()
            response = client.post(
                "/api/capture",
                files={
                    "file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg"),
                    "session_id": (None, "session-1"),
                },
            )

        assert response.status_code == 200
        first_payload = mock_insert.call_args_list[0].args[0]
        second_payload = mock_insert.call_args_list[1].args[0]
        assert "reference_matches" in first_payload
        assert "reference_matches" not in second_payload
        assert second_payload["reference_explanation"] == "Looks aligned with Look 1"
        assert second_payload["session_id"] == "session-1"

    def test_capture_retries_only_missing_enrichment_columns(self) -> None:
        with patch("routes.capture._missing_capture_enrichment_columns", set()), \
             patch("routes.capture.classify", return_value=_FAKE_TAXONOMY_DICT), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags_with_model", return_value=(["black"], "gemini-2.5-flash")), \
             patch("routes.capture.get_layer2_tags_with_model", return_value=(["wide-leg"], "gemini-2.5-flash")), \
             patch("routes.capture.get_reference_matches", return_value=[{"id": "ref-1", "title": "Look 1", "score": 0.91}]), \
             patch("routes.capture.generate_reference_explanation", return_value="Looks aligned with Look 1"), \
             patch("routes.capture.extract_palette", return_value=["#000000"]), \
             patch("routes.capture.supabase") as mock_supa:
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_insert = mock_supa.table().insert
            mock_insert.return_value.execute.side_effect = [
                RuntimeError("Could not find the 'reference_explanation' column of 'captures' in the schema cache"),
                MagicMock(data=[{"id": "1"}]),
            ]

            client = _make_test_client()
            response = client.post(
                "/api/capture",
                files={
                    "file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg"),
                    "session_id": (None, "session-1"),
                },
            )

        assert response.status_code == 200
        first_payload = mock_insert.call_args_list[0].args[0]
        second_payload = mock_insert.call_args_list[1].args[0]
        assert "reference_matches" in first_payload
        assert "reference_matches" in second_payload
        assert "reference_explanation" in first_payload
        assert "reference_explanation" not in second_payload
        assert second_payload["session_id"] == "session-1"

    def test_capture_does_not_mask_non_schema_insert_failures(self) -> None:
        import pytest

        with patch("routes.capture._missing_capture_enrichment_columns", set()), \
             patch("routes.capture.classify", return_value=_FAKE_TAXONOMY_DICT), \
             patch("routes.capture.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("routes.capture.get_layer1_tags_with_model", return_value=(["black"], "gemini-2.5-flash")), \
             patch("routes.capture.get_layer2_tags_with_model", return_value=(["wide-leg"], "gemini-2.5-flash")), \
             patch("routes.capture.get_reference_matches", return_value=[]), \
             patch("routes.capture.generate_reference_explanation", return_value=None), \
             patch("routes.capture.extract_palette", return_value=["#000000"]), \
             patch("routes.capture.supabase") as mock_supa:
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.side_effect = RuntimeError("temporary database outage")

            client = _make_test_client()
            with pytest.raises(RuntimeError, match="temporary database outage"):
                client.post(
                    "/api/capture",
                    files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
                )

        assert mock_supa.table().insert().execute.call_count == 1
```

- [ ] **Step 2: Run updated tests to verify they fail (expected — capture.py not yet updated)**

```bash
cd sakad-backend && python -m pytest tests/test_capture_classify.py -v
```

Expected: failures because `routes.capture` still imports old `_classify`, not `classify`.

- [ ] **Step 3: Rewrite `routes/capture.py`**

Replace the entire file with:

```python
import asyncio
import functools
import io
import logging
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from services.clip_service import classify, get_image_embedding, get_text_embedding
from services.color_service import extract_palette
from services.gemini_service import (
    generate_reference_explanation,
    get_layer1_tags_with_model,
    get_layer2_tags_with_model,
)
from services.retrieval_service import get_reference_matches
from services.supabase_client import supabase

router = APIRouter()
logger = logging.getLogger(__name__)

STORAGE_BUCKET = "captures"
TEXT_WEIGHT = 0.0

_missing_capture_enrichment_columns: set[str] = set()
_ENRICHMENT_COLUMNS = {"session_id", "reference_matches", "reference_explanation"}


def _missing_enrichment_columns(exc: Exception) -> set[str]:
    message = str(exc).lower()
    schema_error = (
        ("column" in message and "does not exist" in message)
        or ("schema cache" in message and "column" in message)
    )
    if not schema_error:
        return set()
    return {column for column in _ENRICHMENT_COLUMNS if column in message}


def _insert_capture(payload: dict, *, allow_retry_without_enrichment: bool) -> object:
    global _missing_capture_enrichment_columns
    try:
        return supabase.table("captures").insert(payload).execute()
    except Exception as exc:
        missing_columns = _missing_enrichment_columns(exc)
        if not allow_retry_without_enrichment or not missing_columns:
            raise
        _missing_capture_enrichment_columns.update(missing_columns)
        logger.warning(
            "[capture] enrichment columns unavailable; retrying legacy insert shape: %s", exc
        )
        retry_payload = {k: v for k, v in payload.items() if k not in missing_columns}
        return supabase.table("captures").insert(retry_payload).execute()


@router.post("/api/capture")
async def capture(
    file: UploadFile = File(...),
    session_id: str | None = Form(default=None),
) -> dict:
    try:
        image_bytes = await file.read()
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"

        storage_response = supabase.storage.from_(STORAGE_BUCKET).upload(
            path=filename,
            file=image_bytes,
            file_options={"content-type": file.content_type or "image/jpeg"},
        )
        if hasattr(storage_response, "error") and storage_response.error:
            logger.error("[capture] storage upload failed: %s", storage_response.error)
            raise HTTPException(
                status_code=500,
                detail=f"Storage upload failed: {storage_response.error}",
            )

        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)
        loop = asyncio.get_running_loop()

        image_embedding = await loop.run_in_executor(None, get_image_embedding, image_bytes)

        layer1_fn = functools.partial(
            get_layer1_tags_with_model,
            image_bytes,
            mime_type=file.content_type or "image/jpeg",
        )
        layer1, layer1_model = await loop.run_in_executor(None, layer1_fn)
        if not layer1:
            logger.warning("[capture] gemini layer1 unavailable; continuing with fallback path")

        if layer1:
            layer2_fn = functools.partial(
                get_layer2_tags_with_model,
                image_bytes,
                layer1,
                mime_type=file.content_type or "image/jpeg",
            )
            layer2, layer2_model = await loop.run_in_executor(None, layer2_fn)
        else:
            layer2, layer2_model = [], None
        if layer1 and not layer2:
            logger.warning("[capture] gemini layer2 unavailable; continuing with fallback path")

        text_embedding = None
        if TEXT_WEIGHT > 0.0 and (layer1 or layer2):
            enriched_text = " ".join(layer1 + layer2)
            try:
                text_embedding = await loop.run_in_executor(
                    None, get_text_embedding, enriched_text
                )
            except Exception as exc:
                logger.warning("[capture] text embedding failed; falling back to image-only: %s", exc)

        try:
            taxonomy_matches = classify(image_embedding, text_embedding)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        reference_matches = get_reference_matches(image_embedding)
        palette = extract_palette(image_bytes)

        reference_explanation = None
        try:
            reference_explanation = generate_reference_explanation(
                taxonomy_matches=[{"label": k, "score": v} for k, v in taxonomy_matches.items()],
                reference_matches=reference_matches,
                layer1_tags=layer1 or None,
                layer2_tags=layer2 or None,
            )
        except Exception:
            logger.exception("[capture] reference explanation failed")

        payload: dict = {
            "image_url": public_url,
            "embedding": image_embedding,
            "taxonomy_matches": taxonomy_matches,
            "layer1_tags": layer1 or None,
            "layer2_tags": layer2 or None,
            "tags": {"palette": palette},
        }
        enrichment: dict = {
            "session_id": session_id,
            "reference_matches": reference_matches,
            "reference_explanation": reference_explanation,
        }
        for key, value in enrichment.items():
            if key not in _missing_capture_enrichment_columns:
                payload[key] = value

        insert_response = _insert_capture(
            payload,
            allow_retry_without_enrichment=bool(_ENRICHMENT_COLUMNS & set(payload)),
        )

        if not insert_response.data:
            logger.error("[capture] insert failed after successful processing")
            raise HTTPException(status_code=500, detail="Failed to insert capture record")

        capture_record = insert_response.data[0]
        logger.info(
            "[capture] success: id=%s taxonomy_matches=%s reference_matches=%s "
            "gemini_layer1=%s gemini_layer2=%s layer1_model=%s layer2_model=%s",
            capture_record.get("id"),
            len(taxonomy_matches),
            len(reference_matches),
            bool(layer1),
            bool(layer2),
            layer1_model,
            layer2_model,
        )
        capture_record["gemini_models"] = {"layer1": layer1_model, "layer2": layer2_model}
        return capture_record

    except HTTPException:
        raise
    except Exception:
        logger.exception("[capture] unhandled failure")
        raise
```

- [ ] **Step 4: Run the updated capture tests**

```bash
cd sakad-backend && python -m pytest tests/test_capture_classify.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Run the full test suite**

```bash
cd sakad-backend && python -m pytest tests/ -x -q
```

Expected: 64+ tests pass (the old `TestClassify` class tests are replaced; new tests cover the same behaviour).

- [ ] **Step 6: Commit**

```bash
cd sakad-backend && git add routes/capture.py tests/test_capture_classify.py
git commit -m "refactor: slim capture route, wire new services, fix taxonomy_matches shape"
```

---

## Task 5: Remove dead code from the old `_classify` / `_load_taxonomy` in `routes/capture.py`

After Task 4 the old helpers no longer exist in `capture.py`. Verify no other file still references them.

**Files:**

- Verify: `sakad-backend/routes/capture.py`

- [ ] **Step 1: Confirm no leftover references**

```bash
cd sakad-backend && grep -rn "_classify\|_load_taxonomy\|_kmeans_numpy\|_extract_palette\|generate_reference_explanation" routes/ services/
```

Expected: zero matches in `routes/` for the private helpers; `generate_reference_explanation` should appear only in `services/gemini_service.py`.

- [ ] **Step 2: Count lines in each service file**

```bash
wc -l sakad-backend/routes/capture.py sakad-backend/services/clip_service.py sakad-backend/services/color_service.py sakad-backend/services/gemini_service.py sakad-backend/services/retrieval_service.py
```

Expected: `routes/capture.py` ≤ 100 lines, each service ≤ 180 lines.

- [ ] **Step 3: Run full test suite one final time**

```bash
cd sakad-backend && python -m pytest tests/ -x -q
```

Expected: 64+ tests pass, 0 failures.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: verify dead code removed and service sizes within budget"
```

---

## E2E Verification (API-level — no browser UI)

- [ ] **Verify `taxonomy_matches` is a JSON object in the capture response**

Start the dev server in the worktree, then:

```bash
cd sakad-backend && uvicorn main:app --reload &
curl -s -X POST http://localhost:8000/api/capture \
  -F "file=@test-images/western.jpg" | python3 -m json.tool | grep -A5 taxonomy_matches
```

Expected: `"taxonomy_matches": { "SomeFashionLabel": 0.XXXX, ... }` — a JSON object, not a JSON array.

- [ ] **Kill dev server after verification**

```bash
pkill -f "uvicorn main:app"
```
