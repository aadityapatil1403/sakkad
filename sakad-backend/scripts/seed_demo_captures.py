"""Seed the demo capture corpus through the existing FastAPI pipeline."""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
MANIFEST_PATH = BACKEND_DIR / "eval" / "demo_dataset_manifest.json"
IMAGES_DIR = BACKEND_DIR / "test-images"
OUTPUT_PATH = BACKEND_DIR / "eval" / "demo_dataset_last_run.json"
DOC_PATH = REPO_ROOT / "docs" / "eval_demo_dataset.md"
SPECS_BUCKET = "specs-bucket"
REFERENCE_SCORE_WARNING_THRESHOLD = 0.1
SESSION_ALIASES = ("session_fashion", "session_abstract", "session_mixed")

load_dotenv(BACKEND_DIR / ".env")
sys.path.insert(0, str(BACKEND_DIR))


def load_manifest(path: Path = MANIFEST_PATH) -> list[dict[str, Any]]:
    entries = json.loads(path.read_text())
    if not isinstance(entries, list) or not entries:
        raise ValueError("demo dataset manifest must be a non-empty JSON array")

    required_fields = {"filename", "bucket", "session_alias", "expected_taxonomy"}
    for index, entry in enumerate(entries, start=1):
        missing = sorted(required_fields - set(entry))
        if missing:
            raise ValueError(f"manifest entry {index} missing required fields: {', '.join(missing)}")
        if entry["session_alias"] not in SESSION_ALIASES:
            raise ValueError(
                f"manifest entry {index} has unsupported session alias: {entry['session_alias']}"
            )
        if not isinstance(entry["expected_taxonomy"], list) or not entry["expected_taxonomy"]:
            raise ValueError(f"manifest entry {index} must include non-empty expected_taxonomy")
    return entries


def resolve_dataset_entries(
    manifest: list[dict[str, Any]],
    images_dir: Path = IMAGES_DIR,
) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for entry in manifest:
        local_path = images_dir / entry["filename"]
        asset_status = "available" if local_path.exists() else "missing"
        resolved.append({
            **entry,
            "asset_status": asset_status,
            "local_path": str(local_path),
        })
    return resolved


def ensure_demo_sessions(client: Any, aliases: list[str] | tuple[str, ...]) -> dict[str, str]:
    session_map: dict[str, str] = {}
    for alias in aliases:
        response = client.post("/api/sessions/start")
        if response.status_code != 200:
            raise RuntimeError(f"failed to start demo session {alias}: {response.text}")
        payload = response.json()
        session_id = payload.get("id")
        if not isinstance(session_id, str) or not session_id:
            raise RuntimeError(f"session start for {alias} returned invalid payload: {payload}")
        session_map[alias] = session_id
    return session_map


def ensure_runtime_environment() -> None:
    required_env_vars = ("SUPABASE_URL", "SUPABASE_SERVICE_KEY")
    missing = [name for name in required_env_vars if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing required environment variables for demo seeding: "
            + ", ".join(missing)
        )


def extract_top_taxonomy(payload: dict[str, Any]) -> tuple[str | None, float | None]:
    taxonomy_matches = payload.get("taxonomy_matches") or {}
    if not isinstance(taxonomy_matches, dict) or not taxonomy_matches:
        return None, None
    label, score = next(iter(taxonomy_matches.items()))
    try:
        return str(label), float(score)
    except (TypeError, ValueError):
        return str(label), None


def extract_top_reference(payload: dict[str, Any]) -> dict[str, Any] | None:
    reference_matches = payload.get("reference_matches") or []
    if not isinstance(reference_matches, list) or not reference_matches:
        return None
    top_reference = reference_matches[0]
    return top_reference if isinstance(top_reference, dict) else None


def evaluate_capture_result(
    entry: dict[str, Any],
    payload: dict[str, Any],
    *,
    reference_warning_threshold: float = REFERENCE_SCORE_WARNING_THRESHOLD,
) -> dict[str, Any]:
    expected = [str(label) for label in entry.get("expected_taxonomy", [])]
    acceptable = [str(label) for label in entry.get("acceptable_taxonomy", [])]
    top_label, top_score = extract_top_taxonomy(payload)
    top_reference = extract_top_reference(payload)

    notes: list[str] = []
    passed = top_label in set(expected + acceptable)
    if not passed:
        notes.append(
            "Taxonomy mismatch: "
            f"expected one of {expected + acceptable}, got {top_label or 'None'}."
        )

    reference_title = "None"
    reference_score: float | None = None
    if top_reference is None:
        notes.append("Reference missing: no reference_matches returned.")
    else:
        title = top_reference.get("title") or top_reference.get("designer") or top_reference.get("id")
        reference_title = str(title)
        raw_score = top_reference.get("score")
        try:
            reference_score = float(raw_score)
        except (TypeError, ValueError):
            reference_score = None
        if reference_score is None:
            notes.append("Reference score missing or invalid.")
        elif reference_score <= reference_warning_threshold:
            notes.append(
                f"Reference score low: {reference_score:.4f} <= {reference_warning_threshold:.2f}."
            )

    return {
        "image": entry["filename"],
        "bucket": entry.get("bucket", "unknown"),
        "session_alias": entry["session_alias"],
        "expected": ", ".join(expected),
        "actual_top_match": top_label or "None",
        "actual_top_score": top_score,
        "top_reference": (
            f"{reference_title} ({reference_score:.4f})"
            if reference_score is not None
            else reference_title
        ),
        "pass": passed,
        "notes": notes,
        "source_asset_status": entry["asset_status"],
    }


def choose_recommended_images(results: list[dict[str, Any]], limit: int = 5) -> list[str]:
    scored = [
        result
        for result in results
        if result["pass"]
        and not result["notes"]
        and isinstance(result.get("actual_top_score"), float)
    ]
    scored.sort(key=lambda result: result["actual_top_score"], reverse=True)
    return [result["image"] for result in scored[:limit]]


def build_report_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    seeded_by_image = {
        result["image"]: result
        for result in summary.get("results", [])
    }
    rows: list[dict[str, Any]] = []
    for entry in summary.get("manifest_entries", []):
        seeded = seeded_by_image.get(entry["filename"])
        if seeded is not None:
            rows.append(seeded)
            continue
        rows.append({
            "image": entry["filename"],
            "bucket": entry.get("bucket", "unknown"),
            "expected": ", ".join(entry.get("expected_taxonomy", [])),
            "actual_top_match": "Missing local asset",
            "actual_top_score": None,
            "top_reference": "None",
            "pass": False,
            "notes": [entry.get("notes", "Manual add required.")],
            "source_asset_status": entry.get("asset_status", "missing"),
        })
    return rows


def render_report_markdown(summary: dict[str, Any]) -> str:
    report_rows = build_report_rows(summary)
    lines = [
        "# Demo Dataset Evaluation",
        "",
        "## Evaluation Table",
        "",
        "| image | expected taxonomy | actual top match | pass/fail |",
        "| --- | --- | --- | --- |",
    ]
    for result in report_rows:
        status = "PASS" if result["pass"] else "FAIL"
        lines.append(
            f"| {result['image']} | {result['expected']} | {result['actual_top_match']} | {status} |"
        )

    lines.extend(["", "## Weak Cases", ""])
    weak_cases = [result for result in report_rows if not result["pass"] or result["notes"]]
    if not weak_cases:
        lines.append("- None from the latest run.")
    else:
        for result in weak_cases:
            note_text = " ".join(result["notes"]) if result["notes"] else "Review manually."
            lines.append(
                f"- `{result['image']}`: {result['actual_top_match']} | {result['top_reference']} | {note_text}"
            )

    lines.extend(["", "## Missing / Manual Assets", ""])
    missing_assets = summary.get("missing_assets", [])
    if not missing_assets:
        lines.append("- None.")
    else:
        for entry in missing_assets:
            lines.append(
                f"- `{entry['filename']}` ({entry['bucket']}): {entry['notes']}"
            )

    lines.extend(["", "## Safest Live Demo Images", ""])
    recommended_images = summary.get("recommended_images", [])
    if not recommended_images:
        lines.append("- Pending a successful seeded run in a configured environment.")
    else:
        for image in recommended_images:
            lines.append(f"- `{image}`")

    return "\n".join(lines) + "\n"


def upload_source_asset(
    supabase: Any,
    *,
    filename: str,
    image_bytes: bytes,
    content_type: str,
) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    storage_path = f"demo-dataset/{timestamp}-{uuid.uuid4().hex[:8]}-{filename}"
    response = supabase.storage.from_(SPECS_BUCKET).upload(
        path=storage_path,
        file=image_bytes,
        file_options={"content-type": content_type},
    )
    error = getattr(response, "error", None)
    if error:
        raise RuntimeError(f"specs-bucket upload failed for {filename}: {error}")
    return str(supabase.storage.from_(SPECS_BUCKET).get_public_url(storage_path))


def try_upload_source_asset(
    supabase: Any,
    *,
    filename: str,
    image_bytes: bytes,
    content_type: str,
) -> tuple[str | None, list[str]]:
    try:
        source_url = upload_source_asset(
            supabase,
            filename=filename,
            image_bytes=image_bytes,
            content_type=content_type,
        )
    except RuntimeError as exc:
        return None, [f"specs-bucket upload skipped: {exc}"]
    return source_url, []


def seed_available_entries() -> dict[str, Any]:
    ensure_runtime_environment()

    from fastapi.testclient import TestClient

    from main import app
    from services.supabase_client import supabase

    manifest = load_manifest()
    entries = resolve_dataset_entries(manifest)
    available_entries = [entry for entry in entries if entry["asset_status"] == "available"]
    missing_assets = [
        {
            "filename": entry["filename"],
            "bucket": entry["bucket"],
            "notes": entry.get("notes", "Manual add required."),
        }
        for entry in entries
        if entry["asset_status"] != "available"
    ]

    if not available_entries:
        raise RuntimeError("no available demo dataset images found in test-images/")

    results: list[dict[str, Any]] = []
    with TestClient(app) as client:
        session_map = ensure_demo_sessions(client, SESSION_ALIASES)
        print("Demo sessions:", json.dumps(session_map, indent=2), flush=True)

        for index, entry in enumerate(available_entries, start=1):
            local_path = Path(entry["local_path"])
            image_bytes = local_path.read_bytes()
            content_type = "image/jpeg"
            source_url, upload_notes = try_upload_source_asset(
                supabase,
                filename=entry["filename"],
                image_bytes=image_bytes,
                content_type=content_type,
            )

            response = client.post(
                "/api/capture",
                files={
                    "file": (entry["filename"], image_bytes, content_type),
                    "session_id": (None, session_map[entry["session_alias"]]),
                },
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"capture failed for {entry['filename']}: "
                    f"{response.status_code} {response.text}"
                )
            payload = response.json()
            result = evaluate_capture_result(entry, payload)
            result["source_url"] = source_url
            result["notes"].extend(upload_notes)
            results.append(result)

            print(
                f"[{index}/{len(available_entries)}] {entry['filename']}"
                f" | session={entry['session_alias']}"
                f" | top_taxonomy={result['actual_top_match']} ({result['actual_top_score']})"
                f" | top_reference={result['top_reference']}"
                f" | pass={result['pass']}",
                flush=True,
            )
            for note in result["notes"]:
                print(f"  FLAG: {note}", flush=True)

    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "manifest_entries_count": len(entries),
        "manifest_entries": entries,
        "seeded_entries": len(results),
        "missing_assets": missing_assets,
        "results": results,
        "recommended_images": choose_recommended_images(results),
    }
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    try:
        summary = seed_available_entries()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", flush=True)
        raise SystemExit(1) from exc

    markdown = render_report_markdown(summary)
    print("\n--- Markdown Summary ---\n", flush=True)
    print(markdown, flush=True)
    DOC_PATH.write_text(markdown)
    print(f"Updated run summary at {OUTPUT_PATH}", flush=True)
    print(f"Refreshed evaluation doc at {DOC_PATH}", flush=True)


if __name__ == "__main__":
    main()
