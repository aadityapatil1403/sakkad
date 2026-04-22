# Backend Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the Sakkad FastAPI backend into clean, modular service files — extracting palette, classification, and enrichment logic out of `routes/capture.py` — while fixing the `taxonomy_matches` shape (FIX 1), L2 None guard (FIX 2), and domain-aware classifier without softmax (FIX 3).

**Architecture:** File-by-file extraction with green tests at every checkpoint. Each step extracts one cohesive unit, updates affected tests immediately, and commits before moving to the next. The final result is `enrich_service.py` as the single orchestrator, `routes/capture.py` as a thin ~50-line handler, and `clip_service.py` extended with classify logic.

**Tech Stack:** FastAPI, Python 3.12, pytest, numpy, Pillow, open_clip, Supabase Python client. All commands run from `sakad-backend/`.

---

## File Map

| File                             | Status     | Change                                                  |
| -------------------------------- | ---------- | ------------------------------------------------------- |
| `services/color_service.py`      | **CREATE** | Extract palette logic                                   |
| `services/clip_service.py`       | **MODIFY** | Add `_load_taxonomy()`, `classify()`, `DOMAIN_CAPS`     |
| `services/enrich_service.py`     | **CREATE** | Orchestrator + `generate_reference_explanation`         |
| `routes/capture.py`              | **MODIFY** | Thin handler only; remove all extracted logic           |
| `scripts/evaluate_classifier.py` | **MODIFY** | Match new classify() shape — no softmax                 |
| `scripts/smoke_capture.sh`       | **MODIFY** | Assert `taxonomy_matches` is dict not list              |
| `scripts/verify_capture_eval.sh` | **MODIFY** | Update top-match print for dict shape                   |
| `tests/test_capture_classify.py` | **MODIFY** | Update assertions + patch paths for new shape           |
| `tests/test_color_service.py`    | **CREATE** | Tests for `extract_palette`                             |
| `tests/test_clip_classify.py`    | **CREATE** | Tests for `clip_service.classify`                       |
| `tests/test_enrich_service.py`   | **CREATE** | Tests for `enrich_capture`                              |
| Markdown root files              | **MOVE**   | Agent briefs → `docs/agents/`, plans → `docs/planning/` |
| `README.md`                      | **CREATE** | Project overview + run instructions                     |
| `API_CONTRACT.md`                | **CREATE** | All 8 endpoints documented                              |

---

## Task 1: Extract `color_service.py`

**Files:**

- Create: `sakad-backend/services/color_service.py`
- Create: `sakad-backend/tests/test_color_service.py`
- Modify: `sakad-backend/routes/capture.py` (import + call site only)

- [ ] **Step 1: Write the failing test**

Create `sakad-backend/tests/test_color_service.py`:

```python
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
import io


def _make_image_bytes(color: tuple[int, int, int] = (255, 0, 0)) -> bytes:
    img = Image.new("RGB", (10, 10), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestExtractPalette:
    def test_returns_five_hex_strings(self) -> None:
        from services.color_service import extract_palette

        result = extract_palette(_make_image_bytes())
        assert len(result) == 5
        for color in result:
            assert color.startswith("#")
            assert len(color) == 7

    def test_hex_strings_are_lowercase(self) -> None:
        from services.color_service import extract_palette

        result = extract_palette(_make_image_bytes())
        for color in result:
            assert color == color.lower()

    def test_solid_red_image_produces_red_dominant_color(self) -> None:
        from services.color_service import extract_palette

        result = extract_palette(_make_image_bytes((255, 0, 0)))
        # At least one centroid should be close to red (#ff0000 or similar)
        reds = [c for c in result if c.startswith("#f") or c.startswith("#e")]
        assert len(reds) >= 1
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd sakad-backend && python -m pytest tests/test_color_service.py -v
```

Expected: `ModuleNotFoundError: No module named 'services.color_service'`

- [ ] **Step 3: Create `services/color_service.py`**

Copy the two private helpers and expose `extract_palette`. Do not modify `capture.py` yet.

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


def extract_palette(image_bytes: bytes) -> list[str]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((150, 150))
    pixels = np.array(image).reshape(-1, 3).astype(np.float32)
    centroids = _kmeans_numpy(pixels)
    return [f"#{int(round(r)):02x}{int(round(g)):02x}{int(round(b)):02x}" for r, g, b in centroids]
```

- [ ] **Step 4: Run color tests — must pass**

```bash
cd sakad-backend && python -m pytest tests/test_color_service.py -v
```

Expected: 3 tests PASS

- [ ] **Step 5: Wire `routes/capture.py` to use `color_service`**

In `sakad-backend/routes/capture.py`:

1. Add import at top (after existing service imports):

   ```python
   from services.color_service import extract_palette as _extract_palette
   ```

2. Delete the two private functions `_kmeans_numpy` and `_extract_palette` (lines 193–214 in the original).

The call site `palette = _extract_palette(image_bytes)` at line 285 already uses the name `_extract_palette`, so it continues to work via the import alias.

- [ ] **Step 6: Run full test suite — must stay green**

```bash
cd sakad-backend && python -m pytest tests/ -x -q
```

Expected: 64+ tests pass, 0 failures.

- [ ] **Step 7: Commit**

```bash
git add sakad-backend/services/color_service.py \
        sakad-backend/tests/test_color_service.py \
        sakad-backend/routes/capture.py
git commit -m "refactor: extract color_service.extract_palette from capture.py"
```

---

## Task 2: Extend `clip_service.py` — classify + FIX 1 + FIX 3

**Files:**

- Modify: `sakad-backend/services/clip_service.py`
- Create: `sakad-backend/tests/test_clip_classify.py`
- Modify: `sakad-backend/tests/test_capture_classify.py` (update assertions + patch paths)
- Modify: `sakad-backend/scripts/evaluate_classifier.py` (match new classify shape)

- [ ] **Step 1: Write failing tests for the new `clip_service.classify`**

Create `sakad-backend/tests/test_clip_classify.py`:

```python
import numpy as np
import pytest
from unittest.mock import patch


_FAKE_TAXONOMY = [
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
    {
        "id": 4,
        "label": "label-D",
        "domain": "visual_environmental",
        "embedding": np.array([0.9, 0.1, 0.0], dtype=np.float32),
    },
]

_SINGLE_DOMAIN_TAXONOMY = [
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


class TestClipServiceClassify:
    def _run(self, image_embedding: list[float], taxonomy: list[dict]) -> dict[str, float]:
        from services.clip_service import classify

        with patch("services.clip_service._load_taxonomy", return_value=taxonomy):
            return classify(image_embedding)

    def test_returns_dict_of_label_to_score(self) -> None:
        result = self._run([1.0, 0.0, 0.0], _FAKE_TAXONOMY)
        assert isinstance(result, dict)
        for key, val in result.items():
            assert isinstance(key, str)
            assert isinstance(val, float)

    def test_top_label_matches_closest_embedding(self) -> None:
        result = self._run([1.0, 0.0, 0.0], _FAKE_TAXONOMY)
        assert next(iter(result)) == "label-A"

    def test_scores_do_not_sum_to_one(self) -> None:
        # Cosine sim without softmax — scores are independent, not a probability distribution
        result = self._run([1.0, 0.0, 0.0], _FAKE_TAXONOMY)
        assert abs(sum(result.values()) - 1.0) > 0.01

    def test_domain_caps_applied_multi_domain(self) -> None:
        # fashion_streetwear cap is 3, _default cap is 1
        # taxonomy has 3 fashion + 1 visual_environmental labels
        result = self._run([1.0, 0.0, 0.0], _FAKE_TAXONOMY)
        # With caps: up to 3 fashion + up to 1 visual — max 4 results
        assert len(result) <= 4

    def test_single_domain_fallback_returns_all_labels(self) -> None:
        result = self._run([1.0, 0.0, 0.0], _SINGLE_DOMAIN_TAXONOMY)
        assert len(result) == 3

    def test_empty_taxonomy_raises_runtime_error(self) -> None:
        from services.clip_service import classify

        with patch("services.clip_service._load_taxonomy", return_value=[]):
            with pytest.raises(RuntimeError):
                classify([1.0, 0.0, 0.0])

    def test_result_is_sorted_descending_by_score(self) -> None:
        result = self._run([1.0, 0.0, 0.0], _FAKE_TAXONOMY)
        scores = list(result.values())
        assert scores == sorted(scores, reverse=True)
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd sakad-backend && python -m pytest tests/test_clip_classify.py -v
```

Expected: `ImportError` — `classify` not found in `services.clip_service`

- [ ] **Step 3: Add `_load_taxonomy`, `classify`, and `DOMAIN_CAPS` to `clip_service.py`**

Append to `sakad-backend/services/clip_service.py` after the existing `get_text_embedding` function:

```python
import ast
from collections import defaultdict

import numpy as np
from config import settings
from services.supabase_client import supabase

_CLASSIFICATION_DOMAIN_ALL = None  # load all domains
_taxonomy_cache: list[dict] | None = None

DOMAIN_CAPS: dict[str, int] = {
    "fashion_streetwear": 3,
    "_default": 1,
}


def _load_taxonomy() -> list[dict]:
    global _taxonomy_cache
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
        embedding_model = row.get("embedding_model")
        if embedding_model != settings.TAXONOMY_EMBEDDING_MODEL:
            raise RuntimeError(
                "Taxonomy embeddings were seeded with a different model. "
                "Re-run sakad-backend/scripts/seed_taxonomy.py before serving captures."
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
            "Taxonomy rows are missing embeddings. "
            "Run sakad-backend/scripts/seed_taxonomy.py."
        )
    _taxonomy_cache = parsed
    return _taxonomy_cache


def _score_all(image_embedding: list[float], taxonomy: list[dict]) -> dict[str, float]:
    img_vec = np.array(image_embedding, dtype=np.float32)
    text_matrix = np.stack([row["embedding"] for row in taxonomy])
    # Cosine similarity: embeddings are pre-normalized (normalize=True in SigLIP load)
    sims = (text_matrix @ img_vec).tolist()
    return {row["label"]: round(float(sim), 4) for row, sim in zip(taxonomy, sims)}


def _group_by_domain(
    taxonomy: list[dict], scores: dict[str, float]
) -> dict[str, list[tuple[str, float]]]:
    by_domain: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for row in taxonomy:
        label = row["label"]
        by_domain[row["domain"]].append((label, scores[label]))
    return dict(by_domain)


def classify(image_embedding: list[float]) -> dict[str, float]:
    taxonomy = _load_taxonomy()
    if not taxonomy:
        raise RuntimeError("Taxonomy is empty.")
    scores = _score_all(image_embedding, taxonomy)
    by_domain = _group_by_domain(taxonomy, scores)

    if len(by_domain) == 1:
        # Single domain: return top-5 globally
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5])

    # Multi-domain: apply per-domain caps
    capped: list[tuple[str, float]] = []
    for domain, rows in by_domain.items():
        cap = DOMAIN_CAPS.get(domain, DOMAIN_CAPS["_default"])
        capped.extend(sorted(rows, key=lambda x: x[1], reverse=True)[:cap])

    return dict(sorted(capped, key=lambda x: x[1], reverse=True))
```

- [ ] **Step 4: Run new clip classify tests — must pass**

```bash
cd sakad-backend && python -m pytest tests/test_clip_classify.py -v
```

Expected: 7 tests PASS

- [ ] **Step 5: Update `tests/test_capture_classify.py`**

Replace the entire file content with the updated version that:

- Removes `test_result_has_required_keys` (deleted — dict has no id/domain keys)
- Removes `test_scores_sum_to_1` (deleted — cosine sim is not a probability distribution)
- Changes `pytest.raises(ValueError)` → `pytest.raises(RuntimeError)`
- Updates key-based result access instead of list-of-dict indexing
- Updates all patch paths from `routes.capture.*` to their new service homes

```python
# sakad-backend/tests/test_capture_classify.py
"""
Tests for classify() in services/clip_service.py and capture pipeline integration.
Patch paths updated after extraction from routes/capture.py.
"""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


_FAKE_TAXONOMY = [
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


class TestClassify:
    def _run(self, image_embedding: list[float]) -> dict[str, float]:
        from services.clip_service import classify

        with patch("services.clip_service._load_taxonomy", return_value=_FAKE_TAXONOMY):
            return classify(image_embedding)

    def test_no_text_embedding_returns_top_label_matching_image_vector(self) -> None:
        result = self._run([1.0, 0.0, 0.0])
        assert next(iter(result)) == "label-A"

    def test_top_result_ordering_reflects_cosine_similarity(self) -> None:
        result_a = self._run([1.0, 0.0, 0.0])
        result_b = self._run([0.0, 1.0, 0.0])
        assert next(iter(result_a)) == "label-A"
        assert next(iter(result_b)) == "label-B"

    def test_returns_all_labels_when_taxonomy_has_3(self) -> None:
        # Single domain → top-5 fallback; only 3 labels exist so all 3 returned
        result = self._run([1.0, 0.0, 0.0])
        assert len(result) == 3

    def test_empty_taxonomy_raises_runtime_error(self) -> None:
        from services.clip_service import classify

        with patch("services.clip_service._load_taxonomy", return_value=[]):
            with pytest.raises(RuntimeError):
                classify([1.0, 0.0, 0.0])


class TestCaptureRouteIntegration:
    """Route-level integration tests. After Task 4, the thin route calls enrich_capture
    as a black box, so we mock at that boundary rather than patching internal service symbols."""

    def _make_enriched(
        self,
        *,
        layer1: list[str] | None = None,
        layer2: list[str] | None = None,
        layer1_model: str | None = "gemini-2.5-flash",
        layer2_model: str | None = None,
        reference_matches: list[dict] | None = None,
        reference_explanation: str | None = None,
        session_id: str | None = None,
    ) -> dict:
        return {
            "embedding": [1.0, 0.0, 0.0],
            "taxonomy_matches": {"label-A": 0.9},
            "layer1_tags": layer1,
            "layer2_tags": layer2,
            "tags": {"palette": ["#000000"]},
            "reference_matches": reference_matches or [],
            "reference_explanation": reference_explanation,
            "session_id": session_id,
            "gemini_models": {"layer1": layer1_model, "layer2": layer2_model},
        }

    def _make_client_with_supabase(self, mock_supa: MagicMock) -> "TestClient":
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from routes.capture import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_capture_succeeds_when_gemini_tag_generation_fails(self) -> None:
        enriched = self._make_enriched(
            layer1=None, layer2=None, layer1_model=None, layer2_model=None,
            reference_matches=[{"id": "ref-1", "title": "Look 1", "score": 0.91}],
            reference_explanation="Looks aligned with Look 1",
        )
        with patch("routes.capture.enrich_capture", return_value=enriched), \
             patch("routes.capture.supabase") as mock_supa:
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{
                **enriched,
                "id": "1",
                "image_url": "http://example.com/img.jpg",
            }])
            client = self._make_client_with_supabase(mock_supa)

            import io
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
        enriched = self._make_enriched(
            layer1=["black"], layer2=["wide-leg"],
            layer1_model="gemini-2.5-flash",
            layer2_model="gemini-3.1-flash-lite-preview",
            reference_matches=[{"id": "ref-1", "title": "Look 1", "score": 0.91}],
            reference_explanation=None,
        )
        with patch("routes.capture.enrich_capture", return_value=enriched), \
             patch("routes.capture.supabase") as mock_supa:
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{
                **enriched,
                "id": "1",
                "image_url": "http://example.com/img.jpg",
            }])
            client = self._make_client_with_supabase(mock_supa)

            import io
            response = client.post(
                "/api/capture",
                files={"file": ("test.jpg", io.BytesIO(b"fake"), "image/jpeg")},
            )

        assert response.status_code == 200
        assert response.json()["gemini_models"] == {
            "layer1": "gemini-2.5-flash",
            "layer2": "gemini-3.1-flash-lite-preview",
        }

    def test_capture_persists_session_id_when_provided(self) -> None:
        enriched = self._make_enriched(session_id="session-1")
        with patch("routes.capture.enrich_capture", return_value=enriched), \
             patch("routes.capture.supabase") as mock_supa:
            mock_supa.storage.from_().upload.return_value = MagicMock(error=None)
            mock_supa.storage.from_().get_public_url.return_value = "http://example.com/img.jpg"
            mock_supa.table().insert().execute.return_value = MagicMock(data=[{
                **enriched,
                "id": "1",
                "image_url": "http://example.com/img.jpg",
            }])
            client = self._make_client_with_supabase(mock_supa)

            import io
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
```

- [ ] **Step 6: Update `scripts/evaluate_classifier.py` to match new classify shape**

Replace the `classify` function (lines 97–126) and update `evaluate_prediction` and the results building loop to use `dict[str, float]` instead of `list[dict]`:

```python
def classify(
    *,
    taxonomy: list[dict[str, Any]],
    image_embedding: np.ndarray,
    image_weight: float = 1.0,
    text_embedding: np.ndarray | None = None,
    text_weight: float = 0.0,
) -> dict[str, float]:
    from collections import defaultdict

    if text_embedding is None or text_weight == 0.0:
        blended = image_embedding
    elif image_weight == 0.0:
        blended = text_embedding
    else:
        blended = image_weight * image_embedding + text_weight * text_embedding
    blended = normalize_vector(blended)

    text_matrix = np.stack([row["embedding"] for row in taxonomy])
    sims = (text_matrix @ blended).tolist()
    scores = {row["label"]: round(float(sim), 4) for row, sim in zip(taxonomy, sims)}

    # Mirror prod domain-aware caps from clip_service.DOMAIN_CAPS
    DOMAIN_CAPS: dict[str, int] = {"fashion_streetwear": 3, "_default": 1}
    by_domain: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for row in taxonomy:
        label = row["label"]
        by_domain[row["domain"]].append((label, scores[label]))

    if len(by_domain) == 1:
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5])

    capped: list[tuple[str, float]] = []
    for domain, rows in by_domain.items():
        cap = DOMAIN_CAPS.get(domain, DOMAIN_CAPS["_default"])
        capped.extend(sorted(rows, key=lambda x: x[1], reverse=True)[:cap])
    return dict(sorted(capped, key=lambda x: x[1], reverse=True))
```

Also update `evaluate_prediction` to accept `dict[str, float]` (replace `predictions: list[dict]` → `predictions: dict[str, float]`):

```python
def evaluate_prediction(
    *,
    predictions: dict[str, float],
    expected_primary: list[str],
    acceptable_secondary: list[str],
) -> dict[str, Any]:
    labels = list(predictions.keys())
    all_expected = expected_primary + acceptable_secondary
    top1_hit = labels[0] in all_expected if labels else False
    top3_hit = any(label in all_expected for label in labels[:3])
    primary_rank = next((idx + 1 for idx, label in enumerate(labels) if label in expected_primary), None)
    return {
        "top1_hit": top1_hit,
        "top3_hit": top3_hit,
        "primary_rank": primary_rank,
    }
```

And update the results building in `main()` — the `predictions` appended to `image_results` should now be the dict items converted for display:

```python
image_results.append({
    "image": image_name,
    "expected_primary_labels": data["entry"]["expected_primary_labels"],
    "acceptable_secondary_labels": data["entry"].get("acceptable_secondary_labels", []),
    "layer1": data["layer1"],
    "layer2": data["layer2"],
    "predictions": [
        {"label": label, "score": score}
        for label, score in predictions.items()
    ],
    "missing_text_features": False,
    **metrics,
})
```

- [ ] **Step 7: Run full test suite — must stay green**

```bash
cd sakad-backend && python -m pytest tests/ -x -q
```

Expected: all tests pass (the old `test_capture_classify.py` tests now test via the new module paths).

- [ ] **Step 8: Commit**

```bash
git add sakad-backend/services/clip_service.py \
        sakad-backend/tests/test_clip_classify.py \
        sakad-backend/tests/test_capture_classify.py \
        sakad-backend/scripts/evaluate_classifier.py
git commit -m "refactor: add classify() to clip_service; apply FIX 1 (dict shape) + FIX 3 (domain-aware, no softmax)"
```

---

## Task 3: Create `enrich_service.py` + FIX 2

**Files:**

- Create: `sakad-backend/services/enrich_service.py`
- Create: `sakad-backend/tests/test_enrich_service.py`

The enrich service moves `generate_reference_explanation` out of `routes/capture.py` and adapts its signature to work with the new `dict[str, float]` taxonomy shape. It then orchestrates the full enrichment pipeline.

- [ ] **Step 1: Write failing tests for `enrich_service`**

Create `sakad-backend/tests/test_enrich_service.py`:

```python
from unittest.mock import patch, MagicMock
import pytest


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

        with patch("services.enrich_service.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("services.enrich_service.get_layer1_tags_with_model", return_value=(["black"], "gemini-2.5-flash")), \
             patch("services.enrich_service.get_layer2_tags_with_model", return_value=(["wide-leg"], "gemini-2.5-flash")), \
             patch("services.enrich_service.classify", return_value={"Gorpcore": 0.91}), \
             patch("services.enrich_service.extract_palette", return_value=["#000000"]), \
             patch("services.enrich_service.get_reference_matches", return_value=[{"id": "r1", "title": "Look 1", "score": 0.9}]), \
             patch("services.enrich_service.generate_reference_explanation", return_value="Reads closest to Gorpcore."):
            result = enrich_capture(b"fake_image_bytes", session_id=None)

        required = {"embedding", "taxonomy_matches", "layer1_tags", "layer2_tags",
                    "tags", "reference_matches", "reference_explanation",
                    "gemini_models", "session_id"}
        assert required.issubset(result.keys())

    def test_enrich_capture_layer2_none_guard(self) -> None:
        # FIX 2: layer2 returning None must be normalized to []
        from services.enrich_service import enrich_capture

        with patch("services.enrich_service.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("services.enrich_service.get_layer1_tags_with_model", return_value=(["black"], "gemini-2.5-flash")), \
             patch("services.enrich_service.get_layer2_tags_with_model", return_value=(None, None)), \
             patch("services.enrich_service.classify", return_value={"Gorpcore": 0.91}), \
             patch("services.enrich_service.extract_palette", return_value=["#000000"]), \
             patch("services.enrich_service.get_reference_matches", return_value=[]), \
             patch("services.enrich_service.generate_reference_explanation", return_value=None):
            result = enrich_capture(b"fake_image_bytes", session_id=None)

        assert result["layer2_tags"] is None  # [] → stored as None (empty list)

    def test_enrich_capture_gemini_failure_is_best_effort(self) -> None:
        from services.enrich_service import enrich_capture

        with patch("services.enrich_service.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("services.enrich_service.get_layer1_tags_with_model", side_effect=RuntimeError("Gemini down")), \
             patch("services.enrich_service.classify", return_value={"Gorpcore": 0.91}), \
             patch("services.enrich_service.extract_palette", return_value=["#000000"]), \
             patch("services.enrich_service.get_reference_matches", return_value=[]), \
             patch("services.enrich_service.generate_reference_explanation", return_value=None):
            result = enrich_capture(b"fake_image_bytes", session_id="session-1")

        assert result["layer1_tags"] is None
        assert result["layer2_tags"] is None
        assert result["session_id"] == "session-1"

    def test_enrich_capture_persists_session_id(self) -> None:
        from services.enrich_service import enrich_capture

        with patch("services.enrich_service.get_image_embedding", return_value=[1.0, 0.0, 0.0]), \
             patch("services.enrich_service.get_layer1_tags_with_model", return_value=([], None)), \
             patch("services.enrich_service.get_layer2_tags_with_model", return_value=([], None)), \
             patch("services.enrich_service.classify", return_value={"Gorpcore": 0.91}), \
             patch("services.enrich_service.extract_palette", return_value=["#000000"]), \
             patch("services.enrich_service.get_reference_matches", return_value=[]), \
             patch("services.enrich_service.generate_reference_explanation", return_value=None):
            result = enrich_capture(b"fake_image_bytes", session_id="session-42")

        assert result["session_id"] == "session-42"
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd sakad-backend && python -m pytest tests/test_enrich_service.py -v
```

Expected: `ModuleNotFoundError: No module named 'services.enrich_service'`

- [ ] **Step 3: Create `services/enrich_service.py`**

```python
import logging
from typing import Any

from services.clip_service import classify, get_image_embedding
from services.color_service import extract_palette
from services.gemini_service import get_layer1_tags_with_model, get_layer2_tags_with_model
from services.retrieval_service import get_reference_matches

logger = logging.getLogger(__name__)


def generate_reference_explanation(
    taxonomy_matches: dict[str, float],
    reference_matches: list[dict[str, Any]],
    layer1_tags: list[str] | None = None,
    layer2_tags: list[str] | None = None,
) -> str | None:
    if not taxonomy_matches or not reference_matches:
        return None

    top_label = next(iter(taxonomy_matches))
    top_reference = reference_matches[0]
    reference_name = top_reference.get("title") or top_reference.get("designer") or "the top reference"
    cue_source = layer2_tags or layer1_tags or []
    cues = ", ".join(cue_source[:3])

    explanation = f"This image reads closest to {top_label} and aligns with {reference_name}."
    if cues:
        explanation += f" Key visual cues include {cues}."
    return explanation


def enrich_capture(image_bytes: bytes, session_id: str | None) -> dict[str, Any]:
    embedding = get_image_embedding(image_bytes)

    try:
        layer1, layer1_model = get_layer1_tags_with_model(image_bytes)
    except Exception as exc:
        logger.warning("[enrich] layer1 tags failed: %s", exc)
        layer1, layer1_model = [], None

    if layer1:
        try:
            layer2_raw, layer2_model = get_layer2_tags_with_model(image_bytes, layer1)
            layer2 = layer2_raw or []
        except Exception as exc:
            logger.warning("[enrich] layer2 tags failed: %s", exc)
            layer2, layer2_model = [], None
    else:
        layer2, layer2_model = [], None

    try:
        taxonomy_matches = classify(embedding)
    except RuntimeError:
        raise  # propagate — caller wraps in HTTPException 503

    palette = extract_palette(image_bytes)
    reference_matches = get_reference_matches(embedding)

    try:
        reference_explanation = generate_reference_explanation(
            taxonomy_matches=taxonomy_matches,
            reference_matches=reference_matches,
            layer1_tags=layer1 or None,
            layer2_tags=layer2 or None,
        )
    except Exception as exc:
        logger.exception("[enrich] reference explanation failed: %s", exc)
        reference_explanation = None

    return {
        "embedding": embedding,
        "taxonomy_matches": taxonomy_matches,
        "layer1_tags": layer1 or None,
        "layer2_tags": layer2 or None,
        "tags": {"palette": palette},
        "reference_matches": reference_matches,
        "reference_explanation": reference_explanation,
        "session_id": session_id,
        "gemini_models": {
            "layer1": layer1_model,
            "layer2": layer2_model,
        },
    }
```

- [ ] **Step 4: Run enrich tests — must pass**

```bash
cd sakad-backend && python -m pytest tests/test_enrich_service.py -v
```

Expected: 5 tests PASS

- [ ] **Step 5: Run full test suite — must stay green**

```bash
cd sakad-backend && python -m pytest tests/ -x -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add sakad-backend/services/enrich_service.py \
        sakad-backend/tests/test_enrich_service.py
git commit -m "refactor: add enrich_service as capture orchestrator; apply FIX 2 (L2 None guard)"
```

---

## Task 4: Thin `routes/capture.py`

**Files:**

- Modify: `sakad-backend/routes/capture.py`

Replace the ~340-line handler with a ~50-line thin route. The route:

1. Reads bytes and uploads to Supabase Storage
2. Calls `enrich_capture` in an executor
3. Inserts into `captures` table
4. Returns the record + injects `gemini_models`

- [ ] **Step 1: Replace `routes/capture.py`**

```python
import asyncio
import logging
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from services.enrich_service import enrich_capture
from services.supabase_client import supabase

router = APIRouter()
logger = logging.getLogger(__name__)

STORAGE_BUCKET = "captures"


@router.post("/api/capture")
async def capture(
    file: UploadFile = File(...),
    session_id: str | None = Form(default=None),
) -> dict:
    try:
        image_bytes = await file.read()

        ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"

        storage_response = supabase.storage.from_(STORAGE_BUCKET).upload(
            path=filename,
            file=image_bytes,
            file_options={"content-type": file.content_type or "image/jpeg"},
        )
        if hasattr(storage_response, "error") and storage_response.error:
            raise HTTPException(
                status_code=500,
                detail=f"Storage upload failed: {storage_response.error}",
            )

        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)

        loop = asyncio.get_running_loop()
        try:
            enriched = await loop.run_in_executor(None, enrich_capture, image_bytes, session_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        insert_response = supabase.table("captures").insert(
            {**enriched, "image_url": public_url}
        ).execute()

        if not insert_response.data:
            raise HTTPException(status_code=500, detail="Failed to insert capture record")

        capture_record = insert_response.data[0]
        capture_record["gemini_models"] = enriched["gemini_models"]

        logger.info(
            "[capture] success: id=%s taxonomy_labels=%d reference_matches=%d",
            capture_record.get("id"),
            len(enriched.get("taxonomy_matches", {})),
            len(enriched.get("reference_matches", [])),
        )
        return capture_record

    except HTTPException:
        raise
    except Exception:
        logger.exception("[capture] unhandled failure")
        raise
```

- [ ] **Step 2: Run full test suite — must stay green**

```bash
cd sakad-backend && python -m pytest tests/ -x -q
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add sakad-backend/routes/capture.py
git commit -m "refactor: thin routes/capture.py to ~50-line handler; delegate to enrich_service"
```

---

## Task 5: Update smoke scripts for new `taxonomy_matches` shape

**Files:**

- Modify: `sakad-backend/scripts/smoke_capture.sh`
- Modify: `sakad-backend/scripts/verify_capture_eval.sh`

- [ ] **Step 1: Update `smoke_capture.sh`**

Find and replace the taxonomy_matches validation block (around line 64–86 of the embedded Python heredoc):

Old:

```python
taxonomy_matches = payload.get("taxonomy_matches")
if not isinstance(taxonomy_matches, list):
    raise SystemExit(f"{image_name}: taxonomy_matches missing or invalid")
```

New:

```python
taxonomy_matches = payload.get("taxonomy_matches")
if not isinstance(taxonomy_matches, dict):
    raise SystemExit(f"{image_name}: taxonomy_matches missing or invalid")
```

Also replace the `top_matches` construction (around line 82–86):

Old:

```python
top_matches = [
    f"{match.get('label')} ({match.get('score')})"
    for match in taxonomy_matches[:3]
    if isinstance(match, dict)
]
```

New:

```python
top_matches = [
    f"{label} ({score})"
    for label, score in list(taxonomy_matches.items())[:3]
]
```

- [ ] **Step 2: Update `verify_capture_eval.sh`**

Find the Python heredoc that reads `predictions` from the response and prints `top`. The current code (around line 53–54):

```python
top = [f"{match.get('label')} ({match.get('score')})" for match in predictions[:5]]
```

Replace with:

```python
top = [f"{label} ({score})" for label, score in list(predictions.items())[:5]]
```

- [ ] **Step 3: Commit**

```bash
git add sakad-backend/scripts/smoke_capture.sh \
        sakad-backend/scripts/verify_capture_eval.sh
git commit -m "fix: update smoke scripts for dict-shaped taxonomy_matches"
```

---

## Task 6: Markdown reorganisation + README + API_CONTRACT

**Files:**

- Move: root `agent_brief_*.md` → `docs/agents/`
- Move: root `current_plan_overall.md`, `next_week_backend_plan.md`, `mvp_plan.md` → `docs/planning/`
- Create: `README.md`
- Create: `API_CONTRACT.md`

- [ ] **Step 1: Create destination directories and move files**

```bash
mkdir -p docs/agents docs/planning
git mv agent_brief_api_contract_and_read_surfaces.md docs/agents/
git mv agent_brief_clustering_endpoints.md docs/agents/
git mv agent_brief_demo_dataset_and_quality.md docs/agents/
git mv agent_brief_deployment_health_and_reliability.md docs/agents/
git mv agent_brief_generation_and_reflection.md docs/agents/
git mv current_plan_overall.md docs/planning/
git mv next_week_backend_plan.md docs/planning/
```

For `mvp_plan.md` — only move if it exists at root:

```bash
[ -f mvp_plan.md ] && git mv mvp_plan.md docs/planning/ || true
```

- [ ] **Step 2: Create `README.md`**

Create at repo root `README.md`:

````markdown
# Sakkad Backend

FastAPI backend for the Sakkad fashion design research tool. Runs on Snap Spectacles paired with a partner web app.

## What It Does

- Accepts image uploads from Spectacles via `POST /api/capture`
- Computes SigLIP embeddings (Marqo/marqo-fashionSigLIP)
- Classifies against a ~100-label fashion taxonomy (domain-aware, cosine similarity)
- Extracts dominant palette colors
- Retrieves visually similar reference corpus items
- Persists everything to Supabase

## Prerequisites

- Python 3.12+
- Supabase project with `captures`, `sessions`, `taxonomy`, `reference_corpus` tables
- SigLIP model weights downloaded locally (HF_HUB_OFFLINE=1)
- Gemini API key

## Environment Variables

| Variable                   | Description                                                 |
| -------------------------- | ----------------------------------------------------------- |
| `SUPABASE_URL`             | Supabase project URL                                        |
| `SUPABASE_KEY`             | Supabase service role key                                   |
| `GEMINI_API_KEY`           | Google Gemini API key                                       |
| `CLIP_MODEL_NAME`          | HuggingFace model ID (default: `Marqo/marqo-fashionSigLIP`) |
| `TAXONOMY_EMBEDDING_MODEL` | Must match model used to seed taxonomy                      |
| `DEV_USER_ID`              | Hardcoded user ID for MVP (no auth yet)                     |

## Running Locally

```bash
cd sakad-backend
uvicorn main:app --reload
```
````

## Running Tests

```bash
cd sakad-backend
python -m pytest tests/ -x -q
```

## Seeding Data

```bash
cd sakad-backend
python scripts/seed_taxonomy.py
python scripts/seed_reference_corpus.py
```

## API

See `API_CONTRACT.md` for full endpoint documentation.

````

- [ ] **Step 3: Create `API_CONTRACT.md`**

Create at repo root `API_CONTRACT.md`:

```markdown
# API Contract

Base URL: `http://localhost:8000` (local) / Railway URL (deployed)

All endpoints return JSON. No authentication required (DEV_USER_ID hardcoded for MVP).

---

## POST /api/capture

Upload an image captured by Spectacles. Runs the full enrichment pipeline.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | yes | Image file (JPEG/PNG) |
| `session_id` | string | no | Associate with an active session |

**Response 200:**

```json
{
  "id": "uuid",
  "image_url": "https://...",
  "embedding": [0.123, ...],
  "taxonomy_matches": {
    "Gorpcore": 0.9312,
    "Techwear": 0.8741,
    "Quiet Luxury": 0.6102
  },
  "layer1_tags": ["black", "technical", "matte"],
  "layer2_tags": ["outdoor-shell", "zip-closure"],
  "tags": {
    "palette": ["#1a1a1a", "#4d4d4d", "#ffffff", "#8b8682", "#2c3e50"]
  },
  "reference_matches": [
    {"id": "ref-uuid", "title": "Arc'teryx Atom SL", "score": 0.88}
  ],
  "reference_explanation": "This image reads closest to Gorpcore and aligns with Arc'teryx Atom SL. Key visual cues include outdoor-shell, zip-closure.",
  "session_id": "session-uuid-or-null",
  "gemini_models": {
    "layer1": "gemini-2.5-flash",
    "layer2": "gemini-2.5-flash"
  },
  "created_at": "2026-04-21T10:00:00Z"
}
````

**Response 503:** Taxonomy not seeded (run `seed_taxonomy.py`)

---

## GET /api/gallery

Returns all captures for the dev user.

**Response 200:**

```json
[
  {
    "id": "uuid",
    "image_url": "https://...",
    "taxonomy_matches": { "Gorpcore": 0.93 },
    "tags": { "palette": ["#1a1a1a"] },
    "created_at": "2026-04-21T10:00:00Z"
  }
]
```

---

## GET /api/sessions

Returns all sessions for the dev user.

**Response 200:**

```json
[
  {
    "id": "session-uuid",
    "started_at": "2026-04-21T09:00:00Z",
    "ended_at": null,
    "capture_count": 5
  }
]
```

---

## POST /api/sessions

Start a new session.

**Request:** `application/json` (empty body `{}` accepted)

**Response 201:**

```json
{
  "id": "session-uuid",
  "started_at": "2026-04-21T09:00:00Z",
  "ended_at": null
}
```

---

## PATCH /api/sessions/{session_id}/end

End an active session.

**Response 200:**

```json
{
  "id": "session-uuid",
  "started_at": "2026-04-21T09:00:00Z",
  "ended_at": "2026-04-21T10:00:00Z"
}
```

---

## GET /api/sessions/{session_id}

Get session detail with all associated captures.

**Response 200:**

```json
{
  "session": {
    "id": "session-uuid",
    "started_at": "2026-04-21T09:00:00Z",
    "ended_at": null
  },
  "captures": [
    {
      "id": "capture-uuid",
      "image_url": "https://...",
      "taxonomy_matches": { "Gorpcore": 0.93 },
      "tags": { "palette": ["#1a1a1a"] },
      "layer1_tags": ["black"],
      "layer2_tags": ["outdoor-shell"],
      "reference_matches": [
        { "id": "ref-uuid", "title": "Arc'teryx", "score": 0.88 }
      ],
      "reference_explanation": "...",
      "created_at": "2026-04-21T09:05:00Z"
    }
  ]
}
```

**Response 404:** Session not found

---

## GET /api/health

Basic health/status check.

**Response 200:**

```json
{
  "status": "ok"
}
```

````

- [ ] **Step 4: Commit**

```bash
git add docs/agents/ docs/planning/ README.md API_CONTRACT.md
git commit -m "docs: reorganise agent briefs/planning to docs/; add README and API_CONTRACT"
````

---

## Final Verification

- [ ] **Run the full test suite one last time**

```bash
cd sakad-backend && python -m pytest tests/ -v
```

Expected: all tests pass, no warnings about missing modules.

- [ ] **Verify file count and structure**

```bash
ls sakad-backend/services/
# Should contain: clip_service.py, color_service.py, enrich_service.py,
#                 gemini_service.py, retrieval_service.py, supabase_client.py

wc -l sakad-backend/routes/capture.py
# Should be ~55 lines
```

- [ ] **Run ruff and mypy**

```bash
cd sakad-backend && ruff check . && mypy --strict .
```

Fix any issues before pushing.

- [ ] **Final commit if any lint fixes**

```bash
git add -u
git commit -m "fix: ruff/mypy cleanup after refactor"
```
