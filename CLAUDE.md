@CONTINUITY.md

# CLAUDE.md - Sakkad

## Project Overview

### What Is This?

Sakkad is a fashion design research tool for Snap Spectacles. Students capture fashion inspiration with AR glasses — images flow to a FastAPI backend that embeds them with SigLIP, classifies against a 100-label fashion taxonomy, and clusters them so a companion web app can surface aesthetic relationships in real time.

### Tech Stack

- **Backend:** FastAPI (Python) · SigLIP `google/siglip-base-patch16-224` (813MB, lazy-loaded) · Gemini (backend-proxied, never exposed to client)
- **Frontend:** Partner-owned — Lens Studio (Spectacles AR) + web app
- **Database:** Supabase — pgvector for embeddings, Storage for images, Realtime for live updates
- **Deploy:** Railway $5/mo (8GB RAM tier — required for SigLIP)
- **Auth:** DEV_USER_ID hardcoded for MVP (Supabase Auth post-demo only)

### File Structure

```
sakkad/
├── sakad-backend/        # FastAPI app (Aaditya owns)
│   ├── main.py           # App entry point, router registration
│   ├── config.py         # Env vars (Supabase URL/key, Gemini key)
│   ├── routes/           # One file per route group
│   │   ├── capture.py    # POST /api/capture ✅
│   │   ├── gallery.py    # GET /api/gallery ✅
│   │   ├── sessions.py   # Sessions endpoints (Week 2)
│   │   └── health.py     # GET /api/health
│   ├── services/
│   │   ├── clip_service.py      # SigLIP model wrapper (lazy-load)
│   │   └── supabase_client.py   # Supabase singleton
│   ├── test_clip.py      # Manual SigLIP smoke test
│   └── requirements.txt
├── docs/
│   ├── prds/             # Product requirements
│   ├── plans/            # Design documents
│   ├── solutions/        # Compounded learnings
│   └── CHANGELOG.md
└── .claude/
    ├── rules/            # Coding standards (auto-loaded)
    └── plans/            # Implementation plans
```

### Key Commands

```bash
# Dev server
cd sakad-backend && uvicorn main:app --reload

# Run tests
cd sakad-backend && python -m pytest

# Lint
cd sakad-backend && ruff check .

# Seed taxonomy (Week 2 task)
cd sakad-backend && python scripts/seed_taxonomy.py

# Manual SigLIP smoke test
cd sakad-backend && python test_clip.py
```

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
