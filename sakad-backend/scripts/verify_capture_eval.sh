#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
MANIFEST_PATH="${BACKEND_DIR}/eval/classifier_manifest.json"
IMAGES_DIR="${BACKEND_DIR}/test-images"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd curl
require_cmd python3

python3 - "${MANIFEST_PATH}" <<'PY' | while IFS=$'\t' read -r image expected acceptable; do
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
for entry in manifest:
    print(
        entry["image"],
        ", ".join(entry["expected_primary_labels"]),
        ", ".join(entry.get("acceptable_secondary_labels", [])),
        sep="\t",
    )
PY
  image_path="${IMAGES_DIR}/${image}"
  response_file="$(mktemp)"
  trap 'rm -f "${response_file}"' EXIT

  curl -fsS -X POST "${BASE_URL}/api/capture" \
    -F "file=@${image_path}" \
    -o "${response_file}"

  python3 - "${image}" "${expected}" "${acceptable}" "${response_file}" <<'PY'
import json
import sys
from pathlib import Path

image_name = sys.argv[1]
expected = sys.argv[2]
acceptable = sys.argv[3]
payload = json.loads(Path(sys.argv[4]).read_text())
predictions = payload.get("taxonomy_matches", {})
top = [f"{label} ({score})" for label, score in list(predictions.items())[:5]]

print(f"=== {image_name} ===")
print(f"expected primary: {expected}")
print(f"acceptable secondary: {acceptable}")
print("top taxonomy:", top)
print("layer1:", payload.get("layer1_tags"))
print("layer2:", payload.get("layer2_tags"))
print()
PY

  rm -f "${response_file}"
  trap - EXIT
done
