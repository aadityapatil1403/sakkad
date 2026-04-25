# PRD: Backend Showcase UI

**Version:** 1.0
**Status:** Draft
**Author:** Codex + User
**Created:** 2026-04-24
**Last Updated:** 2026-04-24

---

## 1. Overview

Build a polished browser UI that demonstrates the Sakkad backend as a fashion intelligence system. The page should let users upload inspiration images, call the FastAPI classification pipeline, and render SigLIP taxonomy, Gemini layer tags, designer reference matches, and narrative explanation in a high-quality editorial interface.

The UI should mirror the important partner-app flow from the recording: capture canvas, selected image group, Explore Relationships panel, Tags & Taxonomy column, suggested relationship statements, and a sketch-generation stage. It should not copy the partner repo or depend on its code.

## 2. Goals & Success Metrics

### Goals

- Make the backend capability understandable to a non-engineer in one screen.
- Provide a real upload-to-classification demo using `POST /api/capture`.
- Make the enriched capture contract obvious to partner frontend engineers.
- Show that the backend supports both garment imagery and abstract/environmental inspiration such as bark, concrete, rust, flowers, leaves, signage, and texture.
- Avoid exposing Gemini or Supabase service secrets in the browser.

### Success Metrics

| Metric | Target | How Measured |
| ------ | ------ | ------------ |
| Demo comprehension | Presenter can explain pipeline from upload to references in under 3 minutes | Manual demo rehearsal |
| Functional upload | One valid image upload renders classification results | Frontend test plus manual smoke against local backend |
| Result completeness | UI displays taxonomy, layer1 tags, layer2 tags, reference matches, and explanation when present | Component tests with fixture payloads |
| Resilience | Empty gallery, failed upload, and backend unavailable states are visible and actionable | Component/API tests |
| Secret safety | No Gemini or Supabase service key appears in frontend env docs/code | Code review |

### Non-Goals

- No direct Lens Studio integration.
- No direct Supabase read/write integration for this showcase.
- No client-side Gemini calls.
- No clustering UI until backend clustering endpoints exist.
- No auth, account management, or multi-user permissions.
- No production deployment work in the first planning pass.
- No browser-side Gemini image generation; sketch generation requires a future backend-proxied image endpoint.

## 3. User Personas

### Demo Presenter

- **Role:** Founder/student/team member showing the live backend.
- **Permissions:** Can open the demo UI and upload local images.
- **Goals:** Prove the pipeline produces fashion-aware outputs, not generic computer vision labels.

### Fashion Student or Designer

- **Role:** User collecting inspiration from garments, textures, and environments.
- **Permissions:** Can upload images and inspect returned analysis.
- **Goals:** Understand visual instincts, references, and styling directions.

### Partner Frontend Engineer

- **Role:** Developer building or connecting the production web app.
- **Permissions:** Read-only viewer of API behavior in the showcase.
- **Goals:** See the capture contract and response shape clearly.

## 4. User Stories

### US-001: Upload And Classify Image

**As a** demo presenter
**I want** to upload an image and send it to `POST /api/capture`
**So that** I can show the backend classifying fashion inspiration live

**Scenario:**

```gherkin
Given the backend is reachable
When I choose a valid image file and submit it
Then the UI shows an analysis loading state
And the completed capture appears with taxonomy, tags, references, and explanation
```

**Acceptance Criteria:**

- [ ] File input accepts image files and has an accessible label.
- [ ] Submit sends `multipart/form-data` with `file`.
- [ ] The response renders without requiring a page refresh.
- [ ] Upload failure renders a useful error message.

**Edge Cases:**

| Condition | Expected Behavior |
| --------- | ----------------- |
| Backend unavailable | Show connection error and keep selected file available for retry |
| Non-image file | Block submission with validation copy |
| Slow first SigLIP load | Show progress/status copy that explains warmup can take longer |

**Priority:** Must Have

### US-002: Inspect Classification Results

**As a** fashion student/designer
**I want** the analysis to show ranked taxonomy, layer tags, and designer references
**So that** I can understand why the backend sees the image a certain way

**Scenario:**

```gherkin
Given a capture has enriched fields
When I open its analysis panel
Then I see the top taxonomy scores
And layer 1 and layer 2 tags
And top reference matches with scores and descriptions
And the reference explanation when present
```

**Acceptance Criteria:**

- [ ] Taxonomy labels are sorted by score descending.
- [ ] Scores are shown both numerically and visually.
- [ ] Missing optional fields render as restrained empty states, not broken blanks.
- [ ] Reference scores below meaningful threshold are visually de-emphasized.

**Edge Cases:**

| Condition | Expected Behavior |
| --------- | ----------------- |
| `reference_matches` is `null` | Show "No strong reference match returned" |
| `layer1_tags` or `layer2_tags` is `null` | Show "Tags unavailable" in the relevant section |
| `taxonomy_matches` is empty | Show "No taxonomy scores returned" and keep the image visible |

**Priority:** Must Have

### US-003: Browse Existing Gallery

**As a** demo presenter
**I want** existing enriched captures to load from `GET /api/gallery`
**So that** the demo is still useful if live upload is slow or credentials are unavailable

**Scenario:**

```gherkin
Given captures exist in Supabase
When I open the showcase UI
Then the UI loads and displays recent captures
And selecting a capture opens the same analysis layout as an upload result
```

**Acceptance Criteria:**

- [ ] Gallery fetches from `GET /api/gallery` using the configured backend URL.
- [ ] Recent captures are displayed as visual cards.
- [ ] Empty gallery has helpful copy and points the user to upload.
- [ ] Gallery failure does not block the upload workflow.

**Priority:** Should Have

### US-004: Generate Narrative Copy From Captures

**As a** presenter
**I want** to select one or more classified captures and call `POST /api/generate`
**So that** I can demonstrate backend-proxied creative copy without exposing Gemini keys

**Scenario:**

```gherkin
Given I have one or more captures selected
When I request a creative summary
Then the UI displays the returned text
And indicates whether fallback text was used
```

**Acceptance Criteria:**

- [ ] User can select capture cards.
- [ ] Request body uses `capture_ids`, not raw image data.
- [ ] `fallback_used` is visible when true.
- [ ] Errors from invalid selection or backend failure are readable.

**Priority:** Nice to Have for MVP, but valuable for demo.

### US-005: Explore Relationships And Sketch Prompt

**As a** demo presenter
**I want** to select a group of captures and see relationship statements beside grouped images and tags
**So that** the backend demo follows the same product story as the partner app

**Scenario:**

```gherkin
Given I have at least two enriched captures
When I select them and open Explore Relationships
Then I see Suggested Relationships
And I see Grouped Images
And I see Tags & Taxonomy aggregated from the selected captures
And selecting a statement fills the sketch prompt stage
```

**Acceptance Criteria:**

- [ ] Relationship panel uses three columns on desktop and stacked sections on mobile.
- [ ] Suggested relationships use existing `POST /api/generate` kinds rather than client-side Gemini.
- [ ] Tags & Taxonomy preserves both fashion labels and abstract/environmental labels.
- [ ] Sketch generation action is visibly gated until a secure backend image endpoint exists.

**Priority:** Must Have

## 5. Technical Constraints

### Known Limitations

- This repository currently has no frontend app.
- First capture after backend start can be slow because SigLIP loads lazily.
- Existing backend routes are `/api/...`, not `/api/v1/...`; the UI must use current routes.
- Existing `GET /api/gallery` returns all captures; client-side filtering/pagination may be needed later.
- Current checked-in taxonomy has 81 labels across `fashion_streetwear` and `abstract_visual`; older planning docs may mention a 100-label target.
- `POST /api/generate` returns one text result per request, so multiple suggested relationships require multiple calls using the existing `kind` values.

### Dependencies

- **Requires:** FastAPI backend running locally or via demo URL.
- **Requires:** Supabase credentials configured for backend, not frontend.
- **Blocked by:** None for a local mock-data UI; live upload depends on backend environment.

### Integration Points

- `POST /api/capture`: image upload and enrichment.
- `GET /api/gallery`: recent enriched captures.
- `GET /api/captures/{id}`: optional refresh/detail fetch.
- `POST /api/generate`: optional selected-capture copy.
- `GET /api/health`: optional status indicator.

## 6. Data Requirements

### New Data Models

- No backend data model changes.
- Frontend TypeScript should define `BackendCapture`, `ReferenceMatch`, `CaptureTags`, and `GenerateResponse` from `sakad-backend/API_CONTRACT.md`.

### Data Validation Rules

- `image_url`: must be rendered only when it is a non-empty string.
- `taxonomy_matches`: object of labels to numeric scores; sort by score descending.
- `layer1_tags` and `layer2_tags`: nullable arrays.
- `reference_matches`: nullable array; each item may have nullable brand/title/score/description.

### Data Migration

- None.

## 7. Security Considerations

- **Authentication:** None in MVP; backend uses hardcoded `DEV_USER_ID`.
- **Authorization:** None in MVP; do not imply production privacy boundaries.
- **Data Protection:** Browser receives public capture URLs and classification metadata only.
- **Secrets:** Frontend may use `VITE_BACKEND_URL`; it must not use Gemini keys, Supabase service keys, or any private token. Vite exposes `VITE_*` variables to client bundles, so keep them non-sensitive.
- **Logging:** Do not log file contents, API keys, or full backend error traces in the browser UI.

## 8. Open Questions

- [ ] Confirm app path: recommended `web/sakkad-showcase/`.
- [ ] Confirm whether batch upload is MVP or after single upload is complete.
- [ ] Confirm whether to use Tailwind v4 or custom CSS for faster local delivery.
- [ ] Confirm whether the UI should be deployable independently or only used locally for demo.

## 9. References

- **Discussion Log:** `docs/prds/backend-showcase-ui-discussion.md`
- **Backend Contract:** `sakad-backend/API_CONTRACT.md`
- **Prior Design:** `docs/superpowers/specs/2026-04-21-api-contract-design.md`
- **Prior Design:** `docs/superpowers/specs/2026-04-21-generation-and-reflection-design.md`
- **Apple HIG:** https://developer.apple.com/design/human-interface-guidelines/
- **React form/input docs:** https://react.dev/reference/react-dom/components/input
- **Vite env docs:** https://vite.dev/guide/env-and-mode
- **Tailwind with Vite docs:** https://tailwindcss.com/docs/installation/using-vite

---

## Appendix A: Revision History

| Version | Date | Author | Changes |
| ------- | ---- | ------ | ------- |
| 1.0 | 2026-04-24 | Codex + User | Initial PRD |

## Appendix B: Approval

- [ ] Product Owner approval
- [ ] Technical Lead approval
- [ ] Ready for technical design
