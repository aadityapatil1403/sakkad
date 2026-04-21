# Sakkad

Sakkad is a FastAPI backend for Snap Spectacles fashion-capture research. It accepts image uploads, enriches them with SigLIP-based taxonomy classification plus Gemini-generated descriptive tags, stores the capture in Supabase, and exposes session/gallery reads for the partner web app.

## Repo Layout

- `sakad-backend/`: FastAPI app, services, tests, scripts
- `docs/`: planning, agent notes, changelog, workflow artifacts
- `data/`: local datasets and supporting artifacts

## Backend Setup

From `sakad-backend/`:

```bash
python -m venv ../venv
source ../venv/bin/activate
pip install -e .
```

Required environment variables live in `.env` and are loaded by `config.py`. Keep Gemini and Supabase secrets server-side only.

## Run

```bash
cd sakad-backend
uvicorn main:app --reload
```

The app mounts these main routes:

- `POST /api/capture`
- `GET /api/gallery`
- `GET /api/health`
- `GET /api/health/supabase`
- `POST /api/sessions/start`
- `POST /api/sessions/{session_id}/end`
- `GET /api/sessions`
- `GET /api/sessions/{session_id}`

## Quality Gates

```bash
cd sakad-backend
python -m pytest
ruff check .
mypy --strict .
```

Helpful smoke scripts:

```bash
cd sakad-backend
scripts/smoke_capture.sh
scripts/verify_capture_eval.sh
python scripts/evaluate_classifier.py
```
