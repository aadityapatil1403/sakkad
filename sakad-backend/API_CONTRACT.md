# API Contract

## Audit

- `GET /api/gallery`: now returns the full normalized capture shape.
- `POST /api/generate`: returns short render-ready text from existing capture/session data, with deterministic fallback when Gemini is unavailable.
- `GET /api/sessions/{id}`: now returns normalized captures under `captures`.
- `GET /api/sessions/{id}/reflection`: returns a short session recap, with deterministic fallback when Gemini is unavailable.
- `GET /api/sessions`: remains a session-list endpoint, so the capture shape does not apply to its top-level items.

## Shared Capture Shape

Used by `GET /api/gallery`, `GET /api/captures/{id}`, and `GET /api/sessions/{id}.captures[*]`.

```json
{
  "id": "string",
  "session_id": "string | null",
  "image_url": "string",
  "created_at": "string",
  "taxonomy_matches": {
    "label": 0.91
  },
  "tags": {
    "palette": ["#111111"],
    "attributes": ["structured"],
    "mood": "technical",
    "layer2": ["outdoor-shell"]
  },
  "layer1_tags": ["structured"],
  "layer2_tags": ["outdoor-shell"],
  "reference_matches": [
    {
      "brand": "Arc'teryx",
      "title": "Beta Shell",
      "score": 0.88,
      "description": "Technical shell with muted palette."
    }
  ],
  "reference_explanation": "Technical outerwear cues align with the reference."
}
```

Nullable:
- `session_id`
- `tags.palette`
- `tags.attributes`
- `tags.mood`
- `tags.layer2`
- `layer1_tags`
- `layer2_tags`
- `reference_matches`
- `reference_explanation`

Notes:
- `taxonomy_matches` is always an object keyed by label, never an array.
- Missing optional fields are returned as `null`, not omitted.

## Endpoints

### `POST /api/capture`

Request: `multipart/form-data`
- `file`: required image upload
- `session_id`: nullable string

Response `200`: inserted capture row plus `gemini_models`

### `GET /api/captures/{id}`

Request: path param `id: string`

Response `200`: shared capture shape

Response `404`:

```json
{"detail": "Capture not found"}
```

### `GET /api/gallery`

Request: none

Response `200`: array of shared capture shape

### `POST /api/generate`

Request body:

```json
{
  "kind": "inspiration_prompt | styling_direction | creative_summary",
  "session_id": "string | null",
  "capture_ids": ["string"]
}
```

Rules:
- provide exactly one of `session_id` or `capture_ids`
- `capture_ids` must be non-empty when used

Response `200`:

```json
{
  "kind": "creative_summary",
  "text": "Short render-ready copy.",
  "fallback_used": false,
  "source": {
    "session_id": "session-1",
    "capture_ids": ["capture-1", "capture-2"]
  }
}
```

Response `404`:

```json
{"detail": "Session not found"}
```

or

```json
{"detail": "Session has no captures to summarize"}
```

Response `422`:

```json
{"detail": "Provide exactly one of session_id or capture_ids"}
```

### `POST /api/sessions/start`

Request: none

Response `200`:

```json
{
  "id": "string",
  "user_id": "string",
  "started_at": "string | null",
  "ended_at": "string | null"
}
```

### `POST /api/sessions/{session_id}/end`

Request: path param `session_id: string`

Response `200`: updated session row

Response `404`:

```json
{"detail": "Session not found"}
```

### `GET /api/sessions`

Request: none

Response `200`:

```json
[
  {
    "id": "string",
    "user_id": "string",
    "started_at": "string | null",
    "ended_at": "string | null"
  }
]
```

### `GET /api/sessions/{id}`

Request: path param `id: string`

Response `200`:

```json
{
  "session": {
    "id": "string",
    "user_id": "string | null",
    "started_at": "string | null",
    "ended_at": "string | null"
  },
  "captures": ["shared_capture_shape"]
}
```

Response `404`:

```json
{"detail": "Session not found"}
```

### `GET /api/sessions/{id}/reflection`

Request: path param `id: string`

Response `200`:

```json
{
  "session_id": "session-1",
  "reflection": "Two to three concise sentences.",
  "fallback_used": false,
  "capture_count": 2
}
```

Response `404`:

```json
{"detail": "Session not found"}
```

or

```json
{"detail": "Session has no captures to summarize"}
```

Response `503`:

```json
{"detail": "Session reflection is unavailable until captures.session_id is migrated"}
```

Returned when the `captures.session_id` column has not yet been migrated. The session detail endpoint (`GET /api/sessions/{id}`) degrades gracefully in this case, but the reflection endpoint requires the column to compute a meaningful summary.

### `GET /api/health`

Request: none

Response `200`:

```json
{"status": "ok"}
```

### `GET /api/health/supabase`

Request: none

Response `200`:

```json
{
  "status": "ok",
  "checks": {
    "database": {"ok": true, "table": "captures"},
    "storage": {"ok": true, "bucket": "captures"}
  }
}
```
