# Classification Layer 1 & 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Gemini Flash-powered layer1 (10 single-word) and layer2 (10 hyphenated two-word) fashion tags to the POST /api/capture pipeline, then blend a text embedding from those tags with the image embedding for richer taxonomy classification.

**Architecture:** A new `services/gemini_service.py` module calls Gemini Flash with the image bytes to generate tags. The tags are joined into a sentence and embedded via the existing `get_text_embedding()` in `clip_service.py`. `_classify()` in `capture.py` accepts an optional second embedding and blends it 60/40 (image/text) before scoring. Both tag arrays are stored in the Supabase captures row.

**Tech Stack:** FastAPI, `google-generativeai` SDK (gemini-2.0-flash), `google/generativeai.types.content_types` inline image, existing marqo-fashionSigLIP (`get_text_embedding`), numpy, pydantic-settings.

---

## File Map

| Action | Path                                           | Responsibility                       |
| ------ | ---------------------------------------------- | ------------------------------------ |
| Modify | `sakad-backend/config.py`                      | Add `GEMINI_API_KEY` field           |
| Modify | `sakad-backend/.env.example`                   | Document `GEMINI_API_KEY`            |
| Create | `sakad-backend/services/gemini_service.py`     | `get_layer1_tags`, `get_layer2_tags` |
| Modify | `sakad-backend/routes/capture.py`              | Updated pipeline + `_classify` blend |
| Modify | `sakad-backend/requirements.txt`               | Add `google-generativeai`            |
| Create | `sakad-backend/tests/test_gemini_service.py`   | Unit tests for gemini_service        |
| Create | `sakad-backend/tests/test_capture_classify.py` | Unit tests for blended `_classify`   |

---

## Task 1: Config + requirements

**Files:**

- Modify: `sakad-backend/config.py`
- Modify: `sakad-backend/.env.example`
- Modify: `sakad-backend/requirements.txt`

- [ ] **Step 1: Add GEMINI_API_KEY to config.py**

Replace the Settings class body:

```python
# sakad-backend/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    CLIP_MODEL_NAME: str = "Marqo/marqo-fashionSigLIP"
    GEMINI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
```

- [ ] **Step 2: Update .env.example**

If `.env.example` doesn't exist, create it. Add the line:

```
GEMINI_API_KEY=your_key_here
```

If it already exists, append after the existing entries.

- [ ] **Step 3: Add google-generativeai to requirements.txt**

Append to `sakad-backend/requirements.txt`:

```
google-generativeai
```

- [ ] **Step 4: Commit**

```bash
cd sakad-backend
git add config.py .env.example requirements.txt
git commit -m "chore: add GEMINI_API_KEY config and google-generativeai dependency"
```

---

## Task 2: Write failing tests for gemini_service

**Files:**

- Create: `sakad-backend/tests/test_gemini_service.py`

The tests mock `google.generativeai.GenerativeModel.generate_content` so no real API call is made.

- [ ] **Step 1: Create tests directory if missing**

```bash
mkdir -p sakad-backend/tests
touch sakad-backend/tests/__init__.py
```

- [ ] **Step 2: Write the test file**

```python
# sakad-backend/tests/test_gemini_service.py
import json
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(text: str) -> MagicMock:
    """Build a fake GenerateContentResponse with .text == text."""
    resp = MagicMock()
    resp.text = text
    return resp


# ---------------------------------------------------------------------------
# get_layer1_tags
# ---------------------------------------------------------------------------

class TestGetLayer1Tags:
    def test_returns_10_strings_on_valid_response(self) -> None:
        tags = ["black", "leather", "oversized", "shiny", "structured",
                "indigo", "denim", "wide", "burgundy", "matte"]
        payload = json.dumps(tags)

        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = _mock_response(payload)
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == tags

    def test_returns_empty_list_when_json_invalid(self) -> None:
        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = _mock_response("not json")
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []

    def test_returns_empty_list_when_list_not_10(self) -> None:
        payload = json.dumps(["black", "leather"])  # only 2 items

        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = _mock_response(payload)
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []

    def test_returns_empty_list_on_api_exception(self) -> None:
        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = RuntimeError("API down")
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer1_tags(b"fake-image-bytes")

        assert result == []


# ---------------------------------------------------------------------------
# get_layer2_tags
# ---------------------------------------------------------------------------

class TestGetLayer2Tags:
    _layer1 = ["black", "leather", "oversized", "shiny", "structured",
                "indigo", "denim", "wide", "burgundy", "matte"]

    def test_returns_10_hyphenated_strings_on_valid_response(self) -> None:
        tags = ["wide-leg", "moto-collar", "leather-jacket", "oversized-denim",
                "burgundy-loafer", "white-sock", "cropped-torso",
                "zip-closure", "ribbed-knit", "straight-hem"]
        payload = json.dumps(tags)

        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = _mock_response(payload)
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == tags

    def test_filters_out_items_without_exactly_one_hyphen(self) -> None:
        tags = ["wide-leg", "no-hyphen-here", "valid-tag",
                "another-good", "bad", "ok-word",
                "fine-item", "extra--dash", "good-one", "last-tag"]
        # Items with 0 hyphens ("bad") or 2+ hyphens ("no-hyphen-here" has 2, "extra--dash")
        # should be dropped, causing the list to fail validation → return []
        payload = json.dumps(tags)

        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = _mock_response(payload)
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == []

    def test_returns_empty_list_on_api_exception(self) -> None:
        with patch("services.gemini_service._get_model") as mock_model_factory:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = RuntimeError("API down")
            mock_model_factory.return_value = mock_model

            import importlib
            import services.gemini_service as gs
            importlib.reload(gs)

            result = gs.get_layer2_tags(b"fake-image-bytes", self._layer1)

        assert result == []
```

- [ ] **Step 3: Run tests — expect ImportError (module doesn't exist yet)**

```bash
cd sakad-backend
python -m pytest tests/test_gemini_service.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'services.gemini_service'`

---

## Task 3: Implement gemini_service.py

**Files:**

- Create: `sakad-backend/services/gemini_service.py`

- [ ] **Step 1: Create the service module**

```python
# sakad-backend/services/gemini_service.py
import json

import google.generativeai as genai

from config import settings

_LAYER1_PROMPT = """\
You are analyzing a fashion photograph.
Return exactly 10 single-word visual descriptors of what you literally see.
Focus on: colors, materials, textures, shapes, silhouettes.
Rules:
- Single words only, no hyphens
- Lowercase
- Be specific (burgundy not red, leather not fabric)
- No abstract concepts, only visual facts
Return ONLY a valid JSON array of exactly 10 strings. No other text.
Example: ["black", "leather", "oversized", "shiny", "structured",
          "indigo", "denim", "wide", "burgundy", "matte"]
"""

_LAYER2_PROMPT_TEMPLATE = """\
You are analyzing a fashion photograph.
Basic visual descriptors already identified: {layer1_joined}

Return exactly 10 two-word fashion descriptors that describe this image
in more specific detail. Build on the basic descriptors above.
Focus on: garment constructions, style combinations, material qualities,
silhouette details, styling choices.
Rules:
- Exactly two words per descriptor, hyphenated
- Lowercase
- Be specific and fashion-literate
- Describe what you see, not abstract aesthetics
Return ONLY a valid JSON array of exactly 10 strings. No other text.
Example: ["wide-leg", "moto-collar", "leather-jacket", "oversized-denim",
          "burgundy-loafer", "white-sock", "cropped-torso",
          "zip-closure", "ribbed-knit", "straight-hem"]
"""


def _get_model() -> genai.GenerativeModel:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-2.0-flash")


def get_layer1_tags(image_bytes: bytes) -> list[str]:
    """Return 10 single-word visual descriptors for the image, or [] on failure."""
    try:
        model = _get_model()
        image_part = {"mime_type": "image/jpeg", "data": image_bytes}
        response = model.generate_content([_LAYER1_PROMPT, image_part])
        tags: list[str] = json.loads(response.text)
        if not isinstance(tags, list) or len(tags) != 10:
            print(f"[gemini_service] layer1: unexpected response length {len(tags) if isinstance(tags, list) else 'non-list'}")
            return []
        return tags
    except Exception as exc:
        print(f"[gemini_service] layer1 error: {exc}")
        return []


def get_layer2_tags(image_bytes: bytes, layer1: list[str]) -> list[str]:
    """Return 10 hyphenated two-word descriptors for the image, or [] on failure."""
    try:
        layer1_joined = ", ".join(layer1)
        prompt = _LAYER2_PROMPT_TEMPLATE.format(layer1_joined=layer1_joined)
        model = _get_model()
        image_part = {"mime_type": "image/jpeg", "data": image_bytes}
        response = model.generate_content([prompt, image_part])
        tags: list[str] = json.loads(response.text)
        if not isinstance(tags, list) or len(tags) != 10:
            print(f"[gemini_service] layer2: unexpected response length")
            return []
        # Validate exactly one hyphen per item (two words)
        if not all(t.count("-") == 1 for t in tags):
            print(f"[gemini_service] layer2: items failed hyphen validation: {tags}")
            return []
        return tags
    except Exception as exc:
        print(f"[gemini_service] layer2 error: {exc}")
        return []
```

- [ ] **Step 2: Run tests — expect PASS**

```bash
cd sakad-backend
python -m pytest tests/test_gemini_service.py -v
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add services/gemini_service.py tests/test_gemini_service.py tests/__init__.py
git commit -m "feat: add gemini_service with get_layer1_tags and get_layer2_tags"
```

---

## Task 4: Write failing tests for blended \_classify

**Files:**

- Create: `sakad-backend/tests/test_capture_classify.py`

- [ ] **Step 1: Write the test file**

```python
# sakad-backend/tests/test_capture_classify.py
"""
Tests for _classify() in routes/capture.py.

Strategy: mock _load_taxonomy() so we can use a deterministic 3-label taxonomy
and verify that:
  1. Without text_embedding the image vector is used as-is.
  2. With text_embedding the blended vector shifts the top result.
"""
import numpy as np
import pytest
from unittest.mock import patch


# Build a fake taxonomy: 3 unit vectors pointing along axes
_FAKE_TAXONOMY = [
    {
        "id": 1,
        "label": "label-A",
        "domain": "streetwear",
        "embedding": np.array([1.0, 0.0, 0.0], dtype=np.float32),
    },
    {
        "id": 2,
        "label": "label-B",
        "domain": "streetwear",
        "embedding": np.array([0.0, 1.0, 0.0], dtype=np.float32),
    },
    {
        "id": 3,
        "label": "label-C",
        "domain": "streetwear",
        "embedding": np.array([0.0, 0.0, 1.0], dtype=np.float32),
    },
]


class TestClassify:
    def _run(
        self,
        image_embedding: list[float],
        text_embedding: list[float] | None,
    ) -> list[dict]:
        from routes.capture import _classify
        with patch("routes.capture._load_taxonomy", return_value=_FAKE_TAXONOMY):
            return _classify(image_embedding, text_embedding)

    def test_no_text_embedding_returns_top_label_matching_image_vector(self) -> None:
        # Image strongly aligned with label-A
        result = self._run([1.0, 0.0, 0.0], text_embedding=None)
        assert result[0]["label"] == "label-A"

    def test_text_embedding_shifts_top_result(self) -> None:
        # Image aligned with label-A, text aligned with label-B
        # Blend: 0.6*[1,0,0] + 0.4*[0,1,0] = [0.6, 0.4, 0] → label-A still top
        result_no_text = self._run([1.0, 0.0, 0.0], text_embedding=None)
        result_with_text = self._run([1.0, 0.0, 0.0], text_embedding=[0.0, 1.0, 0.0])
        # Top label stays label-A but the second should now be label-B
        assert result_no_text[0]["label"] == "label-A"
        assert result_with_text[0]["label"] == "label-A"
        assert result_with_text[1]["label"] == "label-B"

    def test_returns_all_labels_when_taxonomy_has_3(self) -> None:
        result = self._run([1.0, 0.0, 0.0], text_embedding=None)
        assert len(result) == 3  # min(5, len(taxonomy))

    def test_result_has_required_keys(self) -> None:
        result = self._run([1.0, 0.0, 0.0], text_embedding=None)
        for item in result:
            assert "id" in item
            assert "label" in item
            assert "domain" in item
            assert "score" in item

    def test_scores_sum_to_1(self) -> None:
        result = self._run([1.0, 0.0, 0.0], text_embedding=None)
        total = sum(r["score"] for r in result)
        assert abs(total - 1.0) < 1e-3  # top-5 subset, may not be exactly 1 for 3-label
```

- [ ] **Step 2: Run tests — expect FAIL (signature mismatch)**

```bash
cd sakad-backend
python -m pytest tests/test_capture_classify.py -v 2>&1 | head -30
```

Expected: `TypeError: _classify() takes 1 positional argument but 2 were given`

---

## Task 5: Update capture.py — \_classify signature + blending + pipeline

**Files:**

- Modify: `sakad-backend/routes/capture.py`

- [ ] **Step 1: Replace \_classify with blended version**

Change the `_classify` function (lines 42–59) to:

```python
def _classify(
    image_embedding: list[float],
    text_embedding: list[float] | None,
) -> list[dict]:
    taxonomy = _load_taxonomy()
    img_vec = np.array(image_embedding, dtype=np.float32)  # (768,) already normalized

    if text_embedding is not None:
        txt_vec = np.array(text_embedding, dtype=np.float32)
        blended = 0.6 * img_vec + 0.4 * txt_vec
        norm = np.linalg.norm(blended)
        blended = blended / norm if norm > 0 else img_vec
    else:
        blended = img_vec

    text_matrix = np.stack([r["embedding"] for r in taxonomy])  # (N, 768)
    logits = 100.0 * (text_matrix @ blended)
    exp = np.exp(logits - logits.max())
    probs = exp / exp.sum()
    k = min(5, len(taxonomy))
    top_idx = np.argsort(probs)[::-1][:k]
    return [
        {
            "id": taxonomy[i]["id"],
            "label": taxonomy[i]["label"],
            "domain": taxonomy[i]["domain"],
            "score": round(float(probs[i]), 4),
        }
        for i in top_idx
    ]
```

- [ ] **Step 2: Update the capture endpoint imports and pipeline**

At the top of `capture.py`, change the imports to add:

```python
from services.clip_service import get_image_embedding, get_text_embedding
from services.gemini_service import get_layer1_tags, get_layer2_tags
```

Replace the `capture` endpoint function with:

```python
@router.post("/api/capture")
async def capture(file: UploadFile = File(...)) -> dict:
    image_bytes = await file.read()

    filename = f"{uuid.uuid4()}.{file.filename.rsplit('.', 1)[-1] if '.' in file.filename else 'jpg'}"

    storage_response = supabase.storage.from_(STORAGE_BUCKET).upload(
        path=filename,
        file=image_bytes,
        file_options={"content-type": file.content_type or "image/jpeg"},
    )
    if hasattr(storage_response, "error") and storage_response.error:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {storage_response.error}")

    public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)

    image_embedding = get_image_embedding(image_bytes)

    layer1 = await asyncio.get_event_loop().run_in_executor(None, get_layer1_tags, image_bytes)
    layer2 = await asyncio.get_event_loop().run_in_executor(None, get_layer2_tags, image_bytes, layer1)

    if layer1 or layer2:
        enriched_text = " ".join(layer1 + layer2)
        text_embedding: list[float] | None = get_text_embedding(enriched_text)
    else:
        text_embedding = None

    taxonomy_matches = _classify(image_embedding, text_embedding)
    palette = _extract_palette(image_bytes)

    insert_response = supabase.table("captures").insert({
        "image_url": public_url,
        "embedding": image_embedding,
        "taxonomy_matches": taxonomy_matches,
        "layer1_tags": layer1 or None,
        "layer2_tags": layer2 or None,
        "tags": {"palette": palette},
    }).execute()

    if not insert_response.data:
        raise HTTPException(status_code=500, detail="Failed to insert capture record")

    return insert_response.data[0]
```

Also add `import asyncio` at the top of the file.

The full updated `capture.py`:

```python
import ast
import asyncio
import io
import uuid

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from services.clip_service import get_image_embedding, get_text_embedding
from services.gemini_service import get_layer1_tags, get_layer2_tags
from services.supabase_client import supabase

router = APIRouter()

STORAGE_BUCKET = "captures"

# Module-level taxonomy cache: populated on first request
_taxonomy_cache: list[dict] | None = None


def _load_taxonomy() -> list[dict]:
    global _taxonomy_cache
    if _taxonomy_cache is not None:
        return _taxonomy_cache
    response = supabase.table("taxonomy").select("id, label, domain, embedding").execute()
    rows = response.data or []
    parsed = []
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
    _taxonomy_cache = parsed
    return _taxonomy_cache


def _classify(
    image_embedding: list[float],
    text_embedding: list[float] | None,
) -> list[dict]:
    taxonomy = _load_taxonomy()
    img_vec = np.array(image_embedding, dtype=np.float32)  # (768,) already normalized

    if text_embedding is not None:
        txt_vec = np.array(text_embedding, dtype=np.float32)
        blended = 0.6 * img_vec + 0.4 * txt_vec
        norm = np.linalg.norm(blended)
        blended = blended / norm if norm > 0 else img_vec
    else:
        blended = img_vec

    text_matrix = np.stack([r["embedding"] for r in taxonomy])  # (N, 768)
    logits = 100.0 * (text_matrix @ blended)
    exp = np.exp(logits - logits.max())
    probs = exp / exp.sum()
    k = min(5, len(taxonomy))
    top_idx = np.argsort(probs)[::-1][:k]
    return [
        {
            "id": taxonomy[i]["id"],
            "label": taxonomy[i]["label"],
            "domain": taxonomy[i]["domain"],
            "score": round(float(probs[i]), 4),
        }
        for i in top_idx
    ]


def _kmeans_numpy(pixels: np.ndarray, k: int = 5, max_iter: int = 20) -> np.ndarray:
    """Minimal k-means using numpy — avoids sklearn dependency."""
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


def _extract_palette(image_bytes: bytes) -> list[str]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((150, 150))
    pixels = np.array(image).reshape(-1, 3).astype(np.float32)
    centroids = _kmeans_numpy(pixels)
    return [f"#{int(round(r)):02x}{int(round(g)):02x}{int(round(b)):02x}" for r, g, b in centroids]


@router.post("/api/capture")
async def capture(file: UploadFile = File(...)) -> dict:
    image_bytes = await file.read()

    filename = f"{uuid.uuid4()}.{file.filename.rsplit('.', 1)[-1] if '.' in file.filename else 'jpg'}"

    storage_response = supabase.storage.from_(STORAGE_BUCKET).upload(
        path=filename,
        file=image_bytes,
        file_options={"content-type": file.content_type or "image/jpeg"},
    )
    if hasattr(storage_response, "error") and storage_response.error:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {storage_response.error}")

    public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)

    image_embedding = get_image_embedding(image_bytes)

    layer1 = await asyncio.get_event_loop().run_in_executor(None, get_layer1_tags, image_bytes)
    layer2 = await asyncio.get_event_loop().run_in_executor(None, get_layer2_tags, image_bytes, layer1)

    if layer1 or layer2:
        enriched_text = " ".join(layer1 + layer2)
        text_embedding: list[float] | None = get_text_embedding(enriched_text)
    else:
        text_embedding = None

    taxonomy_matches = _classify(image_embedding, text_embedding)
    palette = _extract_palette(image_bytes)

    insert_response = supabase.table("captures").insert({
        "image_url": public_url,
        "embedding": image_embedding,
        "taxonomy_matches": taxonomy_matches,
        "layer1_tags": layer1 or None,
        "layer2_tags": layer2 or None,
        "tags": {"palette": palette},
    }).execute()

    if not insert_response.data:
        raise HTTPException(status_code=500, detail="Failed to insert capture record")

    return insert_response.data[0]
```

- [ ] **Step 3: Run \_classify tests — expect PASS**

```bash
cd sakad-backend
python -m pytest tests/test_capture_classify.py -v
```

Expected: all tests pass.

- [ ] **Step 4: Run all tests**

```bash
cd sakad-backend
python -m pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 5: Lint**

```bash
cd sakad-backend
ruff check .
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add routes/capture.py tests/test_capture_classify.py
git commit -m "feat: add layer1/layer2 tags and blended classification to capture pipeline"
```

---

## Task 6: Smoke test against live server

**Note:** This task requires `GEMINI_API_KEY` set in `.env` and the server running.

- [ ] **Step 1: Start server**

```bash
cd sakad-backend
uvicorn main:app --reload
```

- [ ] **Step 2: Send a test capture**

```bash
curl -X POST http://localhost:8000/api/capture \
  -F "file=@test-images/furcoat.jpg" | python3 -m json.tool
```

Expected shape:

```json
{
  "id": "...",
  "image_url": "...",
  "layer1_tags": ["<word>", "...", "..."],
  "layer2_tags": ["<word>-<word>", "...", "..."],
  "taxonomy_matches": [
    {"label": "...", "score": 0.XXXX, "domain": "...", "id": "..."}
  ],
  "tags": {"palette": ["#xxxxxx", "..."]}
}
```

- [ ] **Step 3: Verify layer1_tags has 10 items and layer2_tags has 10 items**

If either is `null` or `[]`:

1. Check the server logs for `[gemini_service]` error lines
2. Confirm `GEMINI_API_KEY` is present in `.env`
3. Confirm the image is being read as bytes (not a path string)

---

## Notes

- `get_layer1_tags` and `get_layer2_tags` are synchronous (google-generativeai SDK is sync). They're dispatched via `run_in_executor` in the async route to avoid blocking the event loop.
- `_classify` remains synchronous — do not make it async.
- The Supabase schema already has `layer1_tags` and `layer2_tags` columns — no migration needed.
- If `GEMINI_API_KEY` is empty string (default), Gemini calls will fail gracefully and return `[]` — the capture still completes with `null` tags.
