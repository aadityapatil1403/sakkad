# API Contract

## Audit

- `GET /api/gallery`: now returns the full normalized capture shape.
- `GET /api/sessions/{id}`: now returns normalized captures under `captures`.
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
