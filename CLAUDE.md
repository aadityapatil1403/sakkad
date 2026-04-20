@CONTINUITY.md

# CLAUDE.md - Sakkad

## Project Overview

### What Is This?

Sakkad is a fashion design research tool built for Snap Spectacles and a companion web app. The live experience is designed as a dual-screen demo: one person wears Spectacles and captures inspiration in the physical world while a second screen shows the Sakkad web app updating as sessions and captures flow in.

The product is aimed at fashion design students. The Spectacles side handles onboarding, wrist-based session control, and pinch-to-crop capture. The backend stores images, computes SigLIP embeddings, classifies captures against a fashion-focused taxonomy, and prepares the data needed for the partner-built web app to show sessions, spatial canvases, clustering, and downstream generation workflows.

### Tech Stack

- **Backend:** FastAPI (Python) owned by Aaditya
- **Vision model:** SigLIP `google/siglip-base-patch16-224`, lazy-loaded locally for capture embeddings and taxonomy scoring
- **Generation/tagging:** Gemini, always backend-proxied
- **Frontend:** Partner-owned Lens Studio Spectacles experience + partner web app
- **Database:** Supabase for Postgres, pgvector, Storage, and planned Realtime updates
- **Deploy target:** Railway, 8GB RAM tier, because SigLIP is large
- **Auth:** `DEV_USER_ID` hardcoded for the MVP; full auth is intentionally deferred until after the demo if time allows

### Product Shape

- **Live demo setup:** Product overview video, live onboarding on Spectacles, a classmate taking live captures, session appearing in the web app, then a switch to a pre-seeded outdoor account for the richer spatial canvas and generation story
- **Spectacles experience:** Onboarding flow, wrist UI, persistent HUD, live session start/end, pinch-and-drag capture, capture count and environmental metadata
- **Web app experience:** Home collage with evolving clusters, sessions overlay, session canvas, relationship statements, generated images that can be chained back into the canvas

### Current Backend State

- `POST /api/capture` is live: upload to Supabase Storage, compute embedding, enrich metadata, and persist the capture
- `GET /api/gallery` is live
- SigLIP is working locally and is the intended deployed model
- Sessions table exists in Supabase
- Classification work is in progress and currently blends SigLIP with Gemini-produced descriptors
- Sessions API is the current Week 2 focus
- Planned next phases are clusters, generation, reflection, Realtime integration, and demo polish

### Ownership Split

- **Aaditya:** FastAPI backend, ML pipeline, taxonomy, classification, deployment, API contract
- **Partner:** Lens Studio onboarding/capture UX, on-device RSG Gemini object label, web app frontend, session canvas, frontend integration

### Fashion Taxonomy

The taxonomy is intentionally fashion-first rather than general-purpose vision tagging. It targets roughly 100 labels across three tiers:

- **Fashion / Streetwear:** aesthetics such as gorpcore, quiet luxury, techwear, workwear, archive fashion, tailoring, maximalism, monochrome, layering culture
- **Visual / Environmental context:** aesthetics such as brutalism, japandi, bauhaus, material study, golden hour, biophilic, urban industrial
- **Visual art / reference:** aesthetics such as editorial, documentary, swiss graphic, surrealism, vaporwave, risograph, collage

SigLIP is used here because labels should score independently; a single image can belong to multiple aesthetics at once.

### Architecture Principles

- Spectacles captures should land in a shared Supabase-backed system so the web app can observe the same data
- Gemini keys must never reach the client or Lens; all Gemini traffic goes through FastAPI
- The MVP optimizes for demo reliability over full product completeness
- Railway deployment should preserve local-model behavior rather than replacing SigLIP with a remote service

### Repo Structure

```
sakkad/
├── sakad-backend/
│   ├── main.py                 # FastAPI entrypoint
│   ├── config.py               # Environment-backed config
│   ├── routes/
│   │   ├── capture.py          # Capture ingest pipeline
│   │   ├── gallery.py          # Gallery reads
│   │   ├── sessions.py         # Session lifecycle APIs
│   │   └── health.py           # Health/status endpoint
│   ├── services/
│   │   ├── clip_service.py     # SigLIP load + embed helpers
│   │   ├── gemini_service.py   # Backend Gemini integration
│   │   ├── retrieval_service.py# Similarity / retrieval logic
│   │   └── supabase_client.py  # Supabase client factory
│   ├── scripts/
│   │   ├── seed_taxonomy.py
│   │   ├── seed_reference_corpus.py
│   │   └── evaluate_classifier.py
│   ├── migrations/             # Schema evolution for captures/taxonomy/reference data
│   ├── tests/                  # API, seeding, retrieval, and classifier tests
│   └── test-images/            # Manual eval fixtures
├── docs/
│   ├── prds/
│   ├── plans/
│   ├── superpowers/            # Design specs and implementation plans
│   └── CHANGELOG.md
└── .claude/
    ├── commands/                # Workflow playbooks
    ├── hooks/                   # Harness automation
    └── rules/                   # Coding standards
```

### Key Commands

```bash
# Dev server
cd sakad-backend && uvicorn main:app --reload

# Run tests
cd sakad-backend && python -m pytest

# Lint
cd sakad-backend && ruff check .

# Type check
cd sakad-backend && mypy --strict .

# Seed taxonomy and reference data
cd sakad-backend && python scripts/seed_taxonomy.py
cd sakad-backend && python scripts/seed_reference_corpus.py

# Evaluate capture/classification behavior
cd sakad-backend && python scripts/evaluate_classifier.py

# Manual SigLIP smoke test
cd sakad-backend && python test_clip.py
```

### Near-Term Milestones

- **Week 2:** Sessions API, taxonomy seeding, classification validation, capture enrichment
- **Week 3:** Session detail endpoints, clustering endpoints, generation endpoint, API contract, partner handoff
- **Week 4:** Railway deploy, Supabase Realtime, session reflection, live frontend integration
- **Week 5:** Demo account seeding, performance polish, backup walkthrough video, full health endpoint

---

## No Bugs Left Behind Policy

**NEVER defer known issues "for later."** When a review, test, or tool flags an issue — fix it in the same branch before moving on. This applies to:

- Code bugs found during review
- Deployment/infrastructure issues found during testing
- Configuration mismatches across environments (Docker, K8s, Helm)
- Security findings from any reviewer (Claude, Codex, PR toolkit)
- Test coverage gaps for new code

No "follow-up PRs" for known problems. No "v2" for things that should work in v1. If it's found, it's fixed — or the branch isn't ready.

## Detailed Rules

All coding standards, workflow rules, and policies are in `.claude/rules/`.
These files are auto-loaded by Claude Code with the same priority as this file.

**What's in `.claude/rules/`:**

- `principles.md` — Top-level principles and design philosophy
- `workflow.md` — Decision matrix for choosing the right command
- `worktree-policy.md` — Git worktree isolation rules
- `critical-rules.md` — Non-negotiable rules (branch safety, TDD, etc.)
- `memory.md` — How to use persistent memory and save learnings
- `security.md`, `testing.md`, `api-design.md` — Coding standards
- Language-specific: `python-style.md`, `typescript-style.md`, `database.md`, `frontend-design.md`
