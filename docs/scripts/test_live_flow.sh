#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8000}"
IMAGE_PATH="${1:-}"

if [[ -z "${IMAGE_PATH}" ]]; then
  echo "Usage: ./test_live_flow.sh /absolute/or/relative/path/to/image.jpg" >&2
  echo "Optional: set API_BASE=http://127.0.0.1:8000" >&2
  exit 1
fi

if [[ ! -f "${IMAGE_PATH}" ]]; then
  echo "Image not found: ${IMAGE_PATH}" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d /tmp/sakkad-flow.XXXXXX)"
trap 'rm -rf "${TMP_DIR}"' EXIT

SESSION_JSON="${TMP_DIR}/session.json"
CAPTURE_JSON="${TMP_DIR}/capture.json"
DETAIL_JSON="${TMP_DIR}/detail.json"

echo "Starting session..."
curl -sf -X POST "${API_BASE}/api/sessions/start" > "${SESSION_JSON}"

SESSION_ID="$(
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "${SESSION_JSON}"
)"

echo "Session: ${SESSION_ID}"
echo "Uploading capture..."
curl -sf -X POST \
  -F "file=@${IMAGE_PATH}" \
  -F "session_id=${SESSION_ID}" \
  "${API_BASE}/api/capture" > "${CAPTURE_JSON}"

echo "Fetching session detail..."
curl -sf "${API_BASE}/api/sessions/${SESSION_ID}" > "${DETAIL_JSON}"

python3 - "${SESSION_JSON}" "${CAPTURE_JSON}" "${DETAIL_JSON}" <<'PY'
import json
import sys

session = json.load(open(sys.argv[1]))
capture = json.load(open(sys.argv[2]))
detail = json.load(open(sys.argv[3]))

taxonomy = capture.get("taxonomy_matches") or []
references = capture.get("reference_matches") or []
layer1_tags = capture.get("layer1_tags") or []
layer2_tags = capture.get("layer2_tags") or []
gemini_models = capture.get("gemini_models") or {}
reference_explanation = capture.get("reference_explanation")
top_taxonomy = taxonomy[0]["label"] if taxonomy else None
top_reference = references[0].get("title") or references[0].get("designer") if references else None

session_obj = detail.get("session") or {}
captures = detail.get("captures") or []

print("")
print("Flow OK")
print(f"session_id: {session.get('id')}")
print(f"capture_id: {capture.get('id')}")
print(f"top_taxonomy: {top_taxonomy}")
print(f"top_reference: {top_reference}")
print(f"reference_count: {len(references)}")
print(f"session_detail_id: {session_obj.get('id')}")
print(f"session_capture_count: {len(captures)}")
print(f"gemini_layer1_model: {gemini_models.get('layer1')}")
print(f"gemini_layer2_model: {gemini_models.get('layer2')}")
print(f"layer1_tags: {json.dumps(layer1_tags)}")
print(f"layer2_tags: {json.dumps(layer2_tags)}")
print("taxonomy_matches:")
for item in taxonomy:
    print(f"  - {item.get('label')} ({item.get('score')})")
print("reference_matches:")
for item in references:
    title = item.get("title") or item.get("designer")
    print(f"  - {title} ({item.get('score')})")
if reference_explanation:
    print(f"reference_explanation: {reference_explanation}")

if captures:
    first = captures[0]
    print(f"session_capture_image_url: {first.get('image_url')}")
    print(f"session_capture_taxonomy_count: {len(first.get('taxonomy_matches') or [])}")
    print(f"session_capture_reference_count: {len(first.get('reference_matches') or [])}")
PY
