#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
IMAGE_NAME="${2:-western.jpg}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGE_PATH="${BACKEND_DIR}/test-images/${IMAGE_NAME}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd curl
require_cmd python3

if [[ ! -f "${IMAGE_PATH}" ]]; then
  echo "Missing test image: ${IMAGE_PATH}" >&2
  exit 1
fi

health_file="$(mktemp)"
session_file="$(mktemp)"
capture_file="$(mktemp)"
session_detail_file="$(mktemp)"
sessions_list_file="$(mktemp)"
capture_read_file="$(mktemp)"
trap 'rm -f "${health_file}" "${session_file}" "${capture_file}" "${session_detail_file}" "${sessions_list_file}" "${capture_read_file}"' EXIT

health_status="$(curl -sS -o "${health_file}" -w "%{http_code}" "${BASE_URL}/api/health")"
python3 - "${health_status}" "${health_file}" <<'PY'
import json
import sys
from pathlib import Path

status_code = int(sys.argv[1])
payload = json.loads(Path(sys.argv[2]).read_text())

if status_code not in (200, 503):
    raise SystemExit(f"/api/health returned unexpected HTTP {status_code}")

status = payload.get("status")
if status == "error":
    raise SystemExit(f"/api/health reports error: {payload.get('errors')}")

checks = payload.get("checks") or {}
print("health:", status)
for name, check in checks.items():
    print(f"  {name}: ok={check.get('ok')} detail={check.get('detail')}")
PY

curl -fsS -X POST "${BASE_URL}/api/sessions/start" -o "${session_file}"
session_id="$(python3 - "${session_file}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text())
session_id = payload.get("id")
if not isinstance(session_id, str) or not session_id:
    raise SystemExit(f"Invalid session payload: {payload}")
print(session_id)
PY
)"
echo "session_id: ${session_id}"

curl -fsS -X POST "${BASE_URL}/api/capture" \
  -F "file=@${IMAGE_PATH}" \
  -F "session_id=${session_id}" \
  -o "${capture_file}"

capture_id="$(python3 - "${capture_file}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text())
capture_id = payload.get("id")
taxonomy_matches = payload.get("taxonomy_matches")
if not isinstance(capture_id, str) or not capture_id:
    raise SystemExit(f"Invalid capture payload: {payload}")
if not isinstance(taxonomy_matches, dict) or not taxonomy_matches:
    raise SystemExit(f"taxonomy_matches missing or invalid: {payload}")
print(capture_id)
PY
)"
echo "capture_id: ${capture_id}"

curl -fsS "${BASE_URL}/api/sessions/${session_id}" -o "${session_detail_file}"
python3 - "${session_id}" "${capture_id}" "${session_detail_file}" <<'PY'
import json
import sys
from pathlib import Path

session_id = sys.argv[1]
capture_id = sys.argv[2]
payload = json.loads(Path(sys.argv[3]).read_text())

session = payload.get("session") or {}
captures = payload.get("captures") or []
if session.get("id") != session_id:
    raise SystemExit(f"Session detail returned wrong session: {payload}")
if not any(isinstance(item, dict) and item.get("id") == capture_id for item in captures):
    raise SystemExit(f"Session detail missing capture {capture_id}: {payload}")
print(f"session detail captures: {len(captures)}")
PY

curl -fsS "${BASE_URL}/api/sessions" -o "${sessions_list_file}"
python3 - "${session_id}" "${sessions_list_file}" <<'PY'
import json
import sys
from pathlib import Path

session_id = sys.argv[1]
payload = json.loads(Path(sys.argv[2]).read_text())
if not isinstance(payload, list):
    raise SystemExit(f"/api/sessions did not return a list: {payload}")
if not any(isinstance(item, dict) and item.get("id") == session_id for item in payload):
    raise SystemExit(f"Session {session_id} not found in /api/sessions")
print(f"sessions listed: {len(payload)}")
PY

curl -fsS "${BASE_URL}/api/captures/${capture_id}" -o "${capture_read_file}"
python3 - "${capture_id}" "${capture_read_file}" <<'PY'
import json
import sys
from pathlib import Path

capture_id = sys.argv[1]
payload = json.loads(Path(sys.argv[2]).read_text())
if payload.get("id") != capture_id:
    raise SystemExit(f"Capture read returned wrong id: {payload}")
if not isinstance(payload.get("taxonomy_matches"), dict):
    raise SystemExit(f"Capture read taxonomy_matches invalid: {payload}")
print("capture read ok")
PY

echo "Smoke flow passed for ${IMAGE_NAME} against ${BASE_URL}"
