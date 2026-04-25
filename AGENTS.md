# AGENTS.md — Sakkad Harness Guide for Codex

> **This file is your system prompt.** It is loaded automatically before every task.
> Follow every rule here exactly. These are not suggestions.

---

## What This Project Is

Sakkad is a fashion design research tool for Snap Spectacles. FastAPI backend + SigLIP vision model + Supabase. Students capture fashion inspiration with AR glasses; the backend classifies images against a 100-label taxonomy and clusters them for a partner web app.

**Key facts:**

- Backend: `sakad-backend/` — FastAPI, Python, SigLIP, Gemini, Supabase
- Tests: `cd sakad-backend && python -m pytest`
- Lint: `cd sakad-backend && ruff check .`
- Dev server: `cd sakad-backend && uvicorn main:app --reload`
- Auth: `DEV_USER_ID` hardcoded (MVP — no Supabase Auth yet)
- Never expose Gemini API keys to clients — backend-proxied only

**Always read `CONTINUITY.md` before starting any task.** It contains the current goal, what's done, what's in progress, and open questions.

---

## How This Harness Works

This project uses a structured workflow harness. The harness consists of:

| Component         | Location                             | Purpose                                                        |
| ----------------- | ------------------------------------ | -------------------------------------------------------------- |
| Workflow commands | `.claude/commands/*.md`              | Step-by-step playbooks for features, bugs, quick fixes         |
| Coding rules      | `.claude/rules/*.md`                 | Python style, testing, API design, security, database patterns |
| Hooks             | `.claude/hooks/*.sh`                 | Automated enforcement (Claude-side — context below)            |
| State files       | `CONTINUITY.md`, `docs/CHANGELOG.md` | Session continuity and history                                 |
| Skills            | Superpowers plugin (Claude-only)     | Brainstorming, TDD, plan-writing scaffolds                     |

**You (Codex) do not have access to Claude's Skill tool.** Where this guide references a skill, you execute the equivalent behavior manually — described in each section below.

---

## Workflow Decision Matrix

**Before doing anything, pick the right workflow:**

| Scenario                                              | Workflow              | Worktree? | Command file                             |
| ----------------------------------------------------- | --------------------- | --------- | ---------------------------------------- |
| New feature touching 4+ files or multiple sessions    | Full feature workflow | **Yes**   | `.claude/commands/new-feature.md`        |
| New feature touching 1–3 files, self-contained        | Full feature workflow | No        | `.claude/commands/new-feature.md`        |
| Complex bug fix (multi-file, unclear root cause)      | Bug fix workflow      | **Yes**   | `.claude/commands/fix-bug.md`            |
| Simple bug fix (1–3 files, obvious cause)             | Bug fix workflow      | No        | `.claude/commands/fix-bug.md`            |
| Trivial change (1 file, no logic change, obvious fix) | Quick fix             | No        | `.claude/commands/quick-fix.md`          |
| Code review / second opinion                          | Codex review mode     | No        | `.claude/commands/codex.md`              |
| PR review comments to address                         | PR comments workflow  | No        | `.claude/commands/review-pr-comments.md` |
| Merging and cleaning up after PR approval             | Finish branch         | No        | `.claude/commands/finish-branch.md`      |

**When in doubt about worktree: if the task touches 1–3 files and fits in one session, skip the worktree. Never use quick-fix for anything touching business logic, tests, or APIs.**

---

## How to Execute a Workflow

When a workflow is triggered:

1. **Read the command file** — open the relevant `.claude/commands/*.md` file and follow it phase by phase
2. **Read CONTINUITY.md** — understand current state before acting
3. **Initialize the Workflow section in CONTINUITY.md** — write the Command, Phase, and Checklist as shown in the command file
4. **Execute phases in order** — do not skip phases, do not reorder
5. **Update CONTINUITY.md after each phase** — update Phase, Next step, and check off completed items
6. **Never commit or push until quality gates are complete** — see Quality Gates section below

The command files are the authoritative source. This file tells you _when_ and _why_; the command files tell you _how_.

---

## Partner Frontend Context

The partner web app lives at `/Users/aaditya/Desktop/Sakkad/Project-Sakkad-main/web/sakkad-app/`.

**Read these two files before doing any frontend or integration work:**

- `BACKEND_CONTEXT.md` (this repo, root) — what the backend produces, all endpoints, data shapes, what the frontend can consume
- `/Users/aaditya/Desktop/Sakkad/Project-Sakkad-main/PARTNER_CONTEXT.md` — the partner's complete data contract: Capture/Session shapes, all Supabase calls, realtime subscriptions, field name requirements, and what's mock vs real

**Partner stack:** React 19 + Vite + Tailwind v4 + Framer Motion + Supabase Realtime. No backend API calls today — reads directly from Supabase. Aesthetic: Teenage Engineering / Braun, orange `#FF5A00` accent.

**Integration points your code must respect:**

- `taxonomy_matches` must always be `Record<string, number>` — never an array
- Storage bucket is `captures` (backend) / `specs-bucket` (Lens) — do not assume one canonical name without checking
- Supabase Realtime channels are `captures-realtime` and `sessions-realtime` — do not create conflicting channel names
- `session_id` can be null on captures from the unsorted Lens path

---

## UI Design → What You Do Instead

Claude uses a `frontend-design` skill for UI work. You replicate it manually:

### Before writing any UI code

**Commit to a clear aesthetic direction first.** Do not start generic. Answer these questions in a design note before coding:

1. **Tone** — pick one extreme and own it. Options: brutally minimal, editorial/archive, organic/material, industrial/utilitarian, maximalist, luxury/refined. Sakkad's backend is fashion-archive + material philosophy — the UI should feel like a designer's research tool, not a consumer app.
2. **Typography** — choose fonts that are distinctive and characterful. Never use Inter, Roboto, Arial, or Space Grotesk. Pick a display font that feels editorial or archival (e.g. a condensed grotesque, a serif with character, a mono with texture). Pair it with a refined body font.
3. **Color** — commit to a dominant palette with sharp accents. The backend's aesthetic is dark, material, fashion-archive. Consider: near-black backgrounds, raw paper tones, mineral greys, one strong accent (the partner uses `#FF5A00` orange — either align or deliberately contrast).
4. **One unforgettable thing** — decide what someone will remember about this UI. A specific animation, a texture, a layout pattern, a typographic moment. Name it before you build it.

Write a 4–6 line design note to `docs/superpowers/specs/YYYY-MM-DD-<ui-feature>-design.md` before writing any component code.

### Implementation rules

- **Motion:** Use Framer Motion (already in the partner's stack). Prioritize one well-orchestrated moment (page load stagger, capture-reveal animation) over scattered micro-interactions.
- **Typography:** Set font via CSS custom properties or Tailwind config. Import from Google Fonts or use system fonts only if they are genuinely distinctive.
- **Color:** Use CSS variables or Tailwind theme tokens — never hardcode hex values inline across multiple components.
- **Backgrounds:** Create atmosphere. Grain overlay, noise texture, gradient mesh, or raw paper texture beats a solid color every time.
- **Layout:** Use asymmetry, overlap, and generous negative space. Grid-breaking elements are intentional. Avoid centered-everything layouts.
- **No generic AI aesthetics:** No purple gradients on white. No rounded-everything card grids. No glassmorphism without purpose. No "clean and modern" as a goal — that's not a direction, it's the absence of one.

### Component quality bar

Every component must:

- Work correctly (no placeholder data, no TODO comments left in)
- Be typed (TypeScript interfaces for all props)
- Handle loading and empty states explicitly
- Use the shared design tokens (colors, fonts, spacing) — no one-off inline styles

### Checking your work

After building a UI component or page:

1. Read every file you wrote
2. Check: does it look like it was designed for a fashion archive research tool, or does it look like a generic dashboard?
3. Check: is the typography choice distinctive and intentional?
4. Check: is there at least one motion or layout moment that is memorable?
5. Fix anything that would make a designer cringe

---

## Pattern Check Before Responding

Before writing any code or answering any non-trivial question, pause and ask:

> "Does this task match a known workflow pattern?"

| If the task is...                     | Use this pattern                          |
| ------------------------------------- | ----------------------------------------- |
| New feature or non-trivial addition   | Design → Plan → TDD Execution             |
| Bug or unexpected behavior            | Systematic Debugging                      |
| UI or frontend work                   | UI Design rules                           |
| Code to ship                          | Quality Gates (all 3)                     |
| Something done before in this project | Check `docs/solutions/` first             |
| Unclear or ambiguous                  | Ask one clarifying question, then proceed |

You do not need to name the pattern out loud. Just apply it. The goal is to avoid jumping straight to implementation when a more structured approach would produce better results.

---

## Skills → What You Do Instead

Claude uses a `Skill` tool to invoke structured workflows. You replicate the same behavior manually:

### `superpowers:brainstorming` → Design Before Code

Before implementing anything non-trivial:

1. Read the relevant files in the codebase (existing patterns, related modules)
2. Propose 2–3 approaches with trade-offs
3. State your recommendation and why
4. Write a design spec to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
5. **Do not write implementation code until the design is clear and written down**

The Iron Law: design before code. If you skip this and go straight to implementation, you will waste time on the wrong approach.

### `superpowers:writing-plans` → Implementation Plan

After design is approved:

1. Write a step-by-step implementation plan to `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`
2. Each step must be: specific, testable, and small enough to verify independently
3. Include E2E use cases if the feature is user-facing (API changes, UI changes, new endpoints)
4. Review the plan against the actual code — check every file you plan to modify exists and looks as expected

### `superpowers:executing-plans` → TDD Execution

When executing an implementation plan, follow strict Red-Green-Refactor TDD:

**The Iron Law: NO production code without a failing test first.**

1. **RED** — Write one failing test for the next behavior. Run it. Confirm it fails for the right reason (missing feature, not a syntax error).
2. **GREEN** — Write the minimal code to make it pass. No extras, no cleanup yet.
3. **REFACTOR** — Clean up while keeping tests green.
4. Repeat for each behavior.

If you write code before the test: delete it. Start over. No exceptions.

### `superpowers:systematic-debugging` → Root Cause Analysis

Never guess at fixes. When debugging:

1. **Reproduce** — confirm the bug exists with a minimal reproduction
2. **Isolate** — add logging/tracing to narrow down where it breaks
3. **Identify** — find the actual root cause, not just the symptom
4. **Verify** — confirm your understanding before writing any fix
5. Write a failing test that reproduces the bug, then fix it (TDD applies to bugs too)

### `verify-app` subagent → Run Verification Directly

Claude uses a subagent to keep test output out of its context window. You run verification directly:

```bash
cd sakad-backend
python -m pytest && ruff check . && mypy --strict .
```

Report the pass/fail result. Fix any failures before proceeding.

### `pr-review-toolkit:review-pr` → Manual Code Review

Run a thorough self-review of your changes before shipping:

1. Read every file you modified
2. Check for correctness, security issues, error handling gaps, missing tests
3. Tag findings with severity: P0 (broken), P1 (wrong), P2 (poor quality), P3 (nit)
4. Fix all P0/P1/P2 before proceeding — P3s are optional

Also run Codex's own review mode via `.claude/commands/codex.md` for a second pass.

---

## Quality Gates (ALL REQUIRED before commit/push/PR)

These three gates are non-negotiable. The hooks enforce them for Claude automatically. You enforce them yourself:

### Gate 1: Code Review Loop

Run a full self-review (and Codex review if applicable). Iterate until no P0/P1/P2 findings remain on the same pass. Track iteration count in CONTINUITY.md checklist: `Code review loop (N iterations) — PASS`.

**Exit criteria:** All reviewers report clean (P3 only or nothing) on the same pass.

### Gate 2: Simplify

After review, simplify the implementation:

- Remove duplication
- Eliminate dead code
- Rename unclear identifiers
- Extract helpers where logic repeats 3+ times
- Do NOT add features or change behavior

### Gate 3: Verify

Run the full test + lint + type-check suite:

```bash
cd sakad-backend
python -m pytest && ruff check . && mypy --strict .
```

All must pass. Fix failures before proceeding.

**Do not commit until all 3 gates are green.**

---

## Severity Rubric (P0–P3)

Use this rubric when reviewing code or plans:

| Level | Meaning                                                                | Action                     |
| ----- | ---------------------------------------------------------------------- | -------------------------- |
| P0    | Broken — will crash, lose data, or create a security vulnerability     | Must fix before proceeding |
| P1    | Wrong — incorrect behavior, logic error, missing edge case             | Must fix before proceeding |
| P2    | Poor — code smell, maintainability issue, unclear intent, missing test | Must fix before proceeding |
| P3    | Nit — style, naming, minor suggestion                                  | May fix, does not block    |

---

## State File Rules

You are responsible for keeping these files current. Claude's Stop hook enforces this automatically; you self-enforce.

### CONTINUITY.md — Update Every Session

**After completing work:**

1. Add to **Done** (keep only 2–3 recent items)
2. Update **Now** — mark completed items, move top of Next into Now if appropriate
3. Update **Next** — remove anything now in Now
4. Update the **Workflow** section — current Phase and Next step

**Workflow section format** (initialized at workflow start, cleared at finish):

```markdown
## Workflow

| Field     | Value               |
| --------- | ------------------- |
| Command   | /new-feature <name> |
| Phase     | 4 — Execute         |
| Next step | TDD implementation  |

### Checklist

- [x] Worktree created
- [x] Project state read
- [x] Brainstorming complete
- [x] Plan written
- [ ] TDD execution complete
- [ ] Code review loop (0 iterations)
- [ ] Simplified
- [ ] Verified (tests/lint/types)
- [ ] State files updated
- [ ] Committed and pushed
- [ ] PR created
```

Set `Command: none` when the workflow is complete.

### docs/CHANGELOG.md — Update When Significant

Add a changelog entry when 3+ files change on a branch. Format:

```markdown
## [YYYY-MM-DD] — <feature or fix name>

- What changed and why
- Breaking changes (if any)
```

---

## Branch and Worktree Rules

**Never work directly on `main`.** Always on a feature or fix branch. Check before starting:

```bash
git branch --show-current   # must NOT be "main"
```

### When to create a worktree (isolated branch + separate directory)

Create a worktree when:

- The task touches **4+ files** or spans multiple modules
- The task will take **multiple sessions** to complete
- The work must stay isolated from other in-progress changes (e.g. two features being built in parallel)
- The task involves **schema migrations**, **new routes**, or **new services**

```bash
git worktree add .worktrees/<name> -b feat/<name>   # feature
git worktree add .worktrees/<name> -b fix/<name>    # complex bug fix
```

### When to use a branch only (no worktree)

Create a branch but work in the main repo directory when:

- The task touches **1–3 files** and is self-contained
- The fix is clearly scoped (one function, one endpoint, one config value)
- No parallel work is in progress on another branch

```bash
git checkout -b feat/<name>   # or fix/<name>
```

### When quick-fix applies (main repo, no branch, direct commit)

Only for changes that are:

- **Trivially obvious** — a typo, a constant value, a comment, a log message
- **1 file only**
- **Zero logic change** — no conditionals, no new imports, no schema changes

If you are uncertain whether something qualifies as a quick-fix, it does not. Use a branch.

### Worktree mechanics

- **When inside a worktree:** all paths are relative to the worktree root — `sakad-backend/` not `.worktrees/<name>/sakad-backend/`
- Symlink `.env` files into worktrees — never copy them: `ln -s ../../.env .env`
- Do not manually delete worktrees mid-workflow — cleanup happens in the finish-branch step
- After merging, remove the worktree: `git worktree remove .worktrees/<name>` then `git branch -d feat/<name>`

---

## Critical Rules (Non-Negotiable)

These rules are enforced by hooks for Claude. You enforce them yourself:

1. **Never work on `main`** — check `git branch --show-current` before doing anything
2. **TDD mandatory** — write the failing test first, always. No exceptions.
3. **No bugs left behind** — if a review, test, or tool flags an issue, fix it in the same branch before moving on. No "follow-up PRs" for known problems.
4. **Research before implementing** — search `docs/solutions/` for prior solutions, use WebSearch for current library docs. Never implement from memory alone.
5. **Design before code** — write the plan/spec before implementation. No skipping brainstorming for non-trivial work.
6. **Update state files** — CONTINUITY.md must reflect the current state before you stop working. The hook blocks Claude if this is missing; you self-enforce.
7. **Never skip tests** — failing tests mean stop and fix, never bypass.
8. **Never expose secrets** — no API keys in code, no secrets in git. Read from env vars only.
9. **Never commit sensitive files** — `.env`, credentials, API keys stay out of git always.
10. **Ask before creating PRs or merging** — confirm with the user before `gh pr create` or `gh pr merge`.

---

## Hook Awareness (What's Automated for Claude vs. What You Self-Enforce)

Understanding what the hooks do helps you know what's already being enforced vs. what you own:

| Hook                      | Trigger                               | What it does                                                  | Your equivalent                                                        |
| ------------------------- | ------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `session-start.sh`        | Session start                         | Injects current git branch into Claude's context              | Run `git branch --show-current` at session start                       |
| `check-state-updated.sh`  | Claude stops responding               | Blocks if CONTINUITY.md not updated after uncommitted changes | Self-enforce: update CONTINUITY.md before finishing                    |
| `check-workflow-gates.sh` | Before `git commit/push/gh pr create` | Blocks if Code review, Simplified, Verified not checked off   | Self-enforce: verify all 3 gates before shipping                       |
| `check-bash-safety.sh`    | Before any Bash command               | Blocks dangerous patterns (curl\|sh, rm -rf /, sudo, etc.)    | Never run these patterns — they are blocked for good reason            |
| `check-config-change.sh`  | Settings changes                      | Logs config modifications                                     | Be aware: all config changes are logged                                |
| `post-tool-format.sh`     | After Edit/Write                      | Auto-formats changed files                                    | Run `ruff check --fix` after edits to Python files                     |
| `pre-compact-memory.sh`   | Before context compaction             | Reminds Claude to save learnings                              | Save key learnings to `docs/solutions/` when you finish a complex task |

---

## Coding Standards

Full rules are in `.claude/rules/`. Key rules by file:

### Python (`rules/python-style.md`)

- Always type all function parameters and return values
- Use `str | None` not `Optional[str]`, `list[int]` not `List[int]`
- Early returns over nested conditionals
- Never use mutable default arguments (`def f(x=[])`)
- Never use bare `except:` or broad `except Exception:` — catch specific exceptions
- Never block the async event loop with sync calls — use `await asyncio.sleep()` not `time.sleep()`
- Run `ruff check .` and `mypy --strict .` before every commit

### Testing (`rules/testing.md`)

- Follow Arrange-Act-Assert in every test
- File naming: `test_{module}.py`, function naming: `test_{action}_{scenario}_{expected}`
- Mock external APIs (Gemini, Supabase HTTP); never mock your own code
- E2E tests are user use cases: Intent → Steps → Verification → Persistence
- E2E required for any user-facing change; skip only with written justification

### API Design (`rules/api-design.md`)

- Always version: `/api/v1/` (existing routes use `/api/` — apply versioning to new routes only, don't break existing ones)
- Use correct status codes: 201+Location for POST, 204 for DELETE, 422 for validation errors
- Consistent error format: `{"error": {"code": ..., "message": ..., "request_id": ...}}`
- Separate schemas for Create, Update, and Response — never expose internal fields

### Security (`rules/security.md`)

- Never commit secrets — use environment variables
- Never log tokens, passwords, or API keys
- Always validate external input with Pydantic
- Gemini and Supabase keys load from config.py env vars only

### Database (`rules/database.md`)

- Always add `created_at` and `updated_at`
- Always index foreign key columns
- Use eager loading to prevent N+1 queries
- Never build SQL with string concatenation

---

## Prior Solutions

Before implementing anything, check if it was solved before:

```bash
ls docs/solutions/
grep -r "<symptom or keyword>" docs/solutions/
```

After fixing a bug or discovering a pattern, add a solution doc:

```
docs/solutions/<category>/<descriptive-name>.md

# Problem: <symptom>
# Root Cause: <what actually caused it>
# Solution: <how to fix>
# Prevention: <how to avoid in future>
```

---

## Session Start Checklist

At the start of every session:

- [ ] Read `CONTINUITY.md` — understand current state, active workflow, open questions
- [ ] Check `git branch --show-current` — confirm you are NOT on `main`
- [ ] Check `## Workflow` in CONTINUITY.md — if Command != `none`, pick up from the current Phase and Next step
- [ ] If no active workflow: use the Decision Matrix to pick the right workflow for the task

---

## Session End Checklist

Before stopping:

- [ ] CONTINUITY.md updated (Done/Now/Next + Workflow phase)
- [ ] CHANGELOG.md updated if 3+ files changed
- [ ] All tests passing
- [ ] No uncommitted changes left in an unknown state (either committed or explicitly noted in CONTINUITY.md)
- [ ] Key learnings saved to `docs/solutions/` if you fixed a bug or discovered a non-obvious pattern
