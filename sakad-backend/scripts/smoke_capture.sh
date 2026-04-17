#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGES_DIR="${BACKEND_DIR}/test-images"

IMAGES=(
  "furcoat.jpg"
  "japanjersey.jpg"
  "western.jpg"
  "workwear.jpg"
  "leather_jacket.jpg"
)

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd curl
require_cmd python3

for image in "${IMAGES[@]}"; do
  image_path="${IMAGES_DIR}/${image}"
  if [[ ! -f "${image_path}" ]]; then
    echo "Missing test image: ${image_path}" >&2
    exit 1
  fi

  response_file="$(mktemp)"
  trap 'rm -f "${response_file}"' EXIT

  curl -fsS -X POST "${BASE_URL}/api/capture" \
    -F "file=@${image_path}" \
    -o "${response_file}"

  python3 - "${image}" "${response_file}" <<'PY'
import json
import sys
from pathlib import Path

image_name = sys.argv[1]
response_path = Path(sys.argv[2])

try:
    payload = json.loads(response_path.read_text())
except json.JSONDecodeError as exc:
    raise SystemExit(f"{image_name}: invalid JSON response: {exc}") from exc

required_keys = ("layer1_tags", "layer2_tags", "taxonomy_matches", "tags")
missing = [key for key in required_keys if key not in payload]
if missing:
    raise SystemExit(f"{image_name}: missing response keys: {', '.join(missing)}")

palette = payload.get("tags", {}).get("palette")
if not isinstance(palette, list):
    raise SystemExit(f"{image_name}: tags.palette missing or invalid")

taxonomy_matches = payload.get("taxonomy_matches")
if not isinstance(taxonomy_matches, list):
    raise SystemExit(f"{image_name}: taxonomy_matches missing or invalid")

layer1 = payload.get("layer1_tags")
layer2 = payload.get("layer2_tags")
if layer1 is not None and not isinstance(layer1, list):
    raise SystemExit(f"{image_name}: layer1_tags must be a list or null")
if layer2 is not None and not isinstance(layer2, list):
    raise SystemExit(f"{image_name}: layer2_tags must be a list or null")

top_matches = [
    f"{match.get('label')} ({match.get('score')})"
    for match in taxonomy_matches[:3]
    if isinstance(match, dict)
]

print(f"=== {image_name} ===")
print("layer1:", layer1)
print("layer2:", layer2)
print("top taxonomy:", top_matches)
print("palette:", palette)
print()
PY

  rm -f "${response_file}"
  trap - EXIT
done
