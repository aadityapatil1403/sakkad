# API Contract

This document reflects the current backend contract in `feat/backend-refactor`.

## Capture Shape

```ts
type Capture = {
  id: string
  session_id?: string | null
  image_url: string
  created_at?: string
  embedding?: number[]
  taxonomy_matches: Record<string, number>
  layer1_tags?: string[] | null
  layer2_tags?: string[] | null
  tags: {
    palette: string[]
  }
  reference_matches?: Array<{
    id?: string
    title?: string
    designer?: string
    brand?: string
    score: number
  }>
  reference_explanation?: string | null
}
```

`taxonomy_matches` is a score map keyed by taxonomy label. The ordering of the JSON object is descending by score as produced by the backend classifier.

## Endpoints

### `POST /api/capture`

Multipart form fields:

- `file`: required image upload
- `session_id`: optional string

Behavior:

- uploads the image to the `captures` Supabase storage bucket
- computes a SigLIP image embedding
- classifies against taxonomy labels
- generates Gemini `layer1_tags` and `layer2_tags` on a best-effort basis
- extracts `tags.palette`
- retrieves reference matches and an optional explanation
- inserts the enriched record into `captures`

Success response: `200 OK`

Response body:

```json
{
  "id": "capture-id",
  "image_url": "https://example.com/image.jpg",
  "taxonomy_matches": {
    "Cowboy Core": 0.9673,
    "Western Americana": 0.9121
  },
  "layer1_tags": ["black", "leather"],
  "layer2_tags": ["wide-leg", "western-boot"],
  "tags": {
    "palette": ["#1a2b3c", "#4d5e6f"]
  },
  "reference_matches": [],
  "reference_explanation": null,
  "gemini_models": {
    "layer1": "gemini-2.5-flash",
    "layer2": "gemini-2.5-flash"
  }
}
```

Failure responses:

- `500` for storage/insert failures
- `503` when taxonomy loading/classification cannot run

### `GET /api/gallery`

Returns all rows from `captures`, newest first.

Success response: `200 OK`

```json
[
  {
    "id": "capture-id",
    "taxonomy_matches": {
      "Gorpcore": 0.91
    }
  }
]
```

### `GET /api/health`

Lightweight process health.

Success response:

```json
{"status": "ok"}
```

### `GET /api/health/supabase`

Checks the `captures` table and `captures` storage bucket.

Success response:

```json
{
  "status": "ok",
  "checks": {
    "database": {"ok": true, "table": "captures"},
    "storage": {"ok": true, "bucket": "captures"}
  }
}
```

Failure response: `503` with `detail.status = "error"` plus per-check errors.

### `POST /api/sessions/start`

Creates a new session row using the hardcoded MVP `DEV_USER_ID`.

Success response: inserted session row.

### `POST /api/sessions/{session_id}/end`

Marks `ended_at` on an existing session.

Success response: updated session row.

Failure response: `404` if the session does not exist.

### `GET /api/sessions`

Returns all sessions ordered by `started_at desc`.

Success response: array of session rows.

### `GET /api/sessions/{session_id}`

Returns a session plus normalized captures for that session.

Success response:

```json
{
  "session": {
    "id": "session-1"
  },
  "captures": [
    {
      "id": "capture-1",
      "taxonomy_matches": {
        "Gorpcore": 0.91
      },
      "tags": {
        "palette": ["#111111", "#eeeeee"]
      },
      "layer1_tags": ["technical"],
      "layer2_tags": ["outdoor-shell"],
      "reference_matches": [],
      "reference_explanation": null
    }
  ]
}
```

Failure response: `404` if the session does not exist.

## Notes

- New routes should use `/api/v1/`, but existing routes above remain unversioned for compatibility.
- Gemini failures are best-effort and do not block capture ingestion.
- `taxonomy_matches` is intentionally a map, not a ranked array of objects.
