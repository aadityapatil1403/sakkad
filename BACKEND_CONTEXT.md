# BACKEND_CONTEXT.md — Sakkad Backend for Partner Frontend Agents

> Read this if you are a coding agent working on the Sakkad web frontend.
> This describes what the backend produces, what endpoints exist, and what
> your frontend can consume that it may not yet be using.

---

## What the Backend Does

Sakkad backend is a FastAPI + SigLIP + Supabase service that enriches captures
beyond what the Lens app writes. When a capture image is submitted via
`POST /api/capture`, the backend:

1. Uploads the image to Supabase Storage (`captures` bucket)
2. Runs SigLIP (`google/siglip-base-patch16-224`) to produce a 768-dim embedding
3. Calls Gemini for `layer1_tags` (10 single-word visual descriptors) and
   `layer2_tags` (10 hyphenated two-word fashion descriptors)
4. Classifies the blended embedding against a 100-label fashion taxonomy
5. Matches against a 74-entry designer reference corpus (Margiela, Rick Owens,
   Iris van Herpen, Issey Miyake, Jil Sander, Craig Green, etc.)
6. Writes the enriched row back to `captures` in Supabase

The frontend can read this enriched data directly from Supabase OR via the
backend API endpoints below.

---

## Base URL

Local dev: `http://127.0.0.1:8000`
Demo/live: ngrok URL (see DEMO_CHECKLIST.md) — always add header:

```
ngrok-skip-browser-warning: true
```

---

## Enriched Capture Shape

Every capture read from the backend API returns this normalized shape:

```ts
interface BackendCapture {
  id: string;
  session_id: string | null;
  image_url: string;
  created_at: string;

  // Classification — always an object, never an array
  // Keys are taxonomy label strings, values are 0–1 scores
  taxonomy_matches: Record<string, number>;

  // Gemini vision tags
  layer1_tags: string[] | null; // ["rugged", "denim", "worn", ...]
  layer2_tags: string[] | null; // ["cowboy-hat", "denim-shirt", ...]

  // Color/mood tags
  tags: {
    palette: string[] | null; // ["#5c3d1e", "#c9a96e"]
    attributes: string[] | null;
    mood: string | null;
    layer2: string[] | null;
  };

  // Designer reference matching
  reference_matches: Array<{
    brand: string;
    title: string;
    score: number; // 0–1, cosine similarity
    description: string;
  }> | null;

  // Narrative explanation connecting capture to top reference
  reference_explanation: string | null;
}
```

**Key difference from Lens app writes:** The Lens app only writes
`image_url`, `created_at`, and `session_id`. The backend enriches
`taxonomy_matches`, `layer1_tags`, `layer2_tags`, `tags.palette`,
`reference_matches`, and `reference_explanation`.

---

## Endpoints Your Frontend Can Use

### Read all captures (enriched)

```
GET /api/gallery
```

Returns: `BackendCapture[]`

### Read one capture

```
GET /api/captures/{id}
```

Returns: `BackendCapture`

### Read session + its captures

```
GET /api/sessions/{id}
```

Returns:

```json
{
  "session": { "id": "...", "user_id": "...", "started_at": "...", "ended_at": "..." },
  "captures": [BackendCapture]
}
```

### List all sessions

```
GET /api/sessions
```

Returns: `Array<{ id, user_id, started_at, ended_at }>`

### Session reflection (designer-aware narrative)

```
GET /api/sessions/{id}/reflection
```

Returns:

```json
{
  "session_id": "...",
  "reflection": "Your eye is consistently drawn to surfaces mid-transformation...",
  "fallback_used": false,
  "capture_count": 4
}
```

The reflection is 3–4 sentences written by a Gemini creative director persona.
It names specific designers (Rick Owens, Margiela, Iris van Herpen, etc.),
identifies the visual thread across the session, and ends with a line about
the person's aesthetic instinct. If Gemini is unavailable, a deterministic
fallback is returned and `fallback_used: true`.

### Generate copy from captures

```
POST /api/generate
Content-Type: application/json

{
  "kind": "inspiration_prompt" | "styling_direction" | "creative_summary",
  "session_id": "string",      // provide one of these
  "capture_ids": ["string"]    // not both
}
```

Returns:

```json
{
  "kind": "inspiration_prompt",
  "text": "Short render-ready copy.",
  "fallback_used": false,
  "source": { "session_id": "...", "capture_ids": [...] }
}
```

### Health check

```
GET /api/health
```

Returns `{"status": "ok"}` when all dependencies (DB, storage, taxonomy, Gemini) are healthy.

---

## Taxonomy

100 labels across 3 domains:

- `fashion_streetwear` (~56 labels): Cowboy Core, Gorpcore, Quiet Luxury, Techwear, etc.
- `visual_context` (~19 labels): Concrete Brutalism, Botanical Organic, Oxidized Metal, etc.
- `abstract_visual` (~25 labels): Veined Leaf, Cellular Pattern, Raw Fiber, Layered Grain, etc.

`taxonomy_matches` returns the top-scoring labels. A value of `0.97` is very strong;
`0.3` is weak. You can use these scores to drive visual weight in the UI.

---

## Designer Reference Corpus

74 entries. Each capture is matched against this corpus and the top matches
returned in `reference_matches`. Designers covered include:

- Margiela, Rick Owens, Yohji Yamamoto, Jil Sander, Helmut Lang
- Iris van Herpen, Issey Miyake, Comme des Garçons, Alexander McQueen
- Craig Green, Ralph Lauren, Carhartt WIP, Arc'teryx, and others

Reference match scores above `0.15` are meaningful; below that the match
is weak and the `reference_explanation` omits the designer name.

---

## What the Backend Does NOT Do

- **No client-side clustering** — clustering is currently done client-side in the
  frontend with d3-force. Backend clustering (`POST /api/clusters/run`) is not yet built.
- **No Gemini image generation** — image generation is frontend-side via Gemini API key.
  The backend never calls Gemini image generation.
- **No auth** — `DEV_USER_ID` is hardcoded. No Supabase Auth integration yet.
- **No realtime push** — Supabase Realtime subscriptions are frontend-only.
  The backend writes enriched rows to Supabase; the frontend observes them via Realtime.

---

## Integration Pattern for Frontend

The simplest integration path:

1. **Continue using Supabase Realtime** for live updates — the backend writes to the
   same `captures` table the frontend already subscribes to.
2. **Read from backend API** instead of direct Supabase for enriched capture data —
   `GET /api/sessions/{id}` returns normalized captures with taxonomy, references, and tags.
3. **Call `/api/sessions/{id}/reflection`** after a session ends to get the designer-aware
   narrative for display in `SessionView`.
4. **Call `POST /api/generate`** with a session_id or capture_ids to get
   `inspiration_prompt`, `styling_direction`, or `creative_summary` copy.

---

## CORS / Network Notes

Backend runs on port `8000`. For demo, it's exposed via ngrok.
Always include `ngrok-skip-browser-warning: true` header when calling the ngrok URL.
For local dev with the frontend on a different port, CORS is configured to allow all origins.
