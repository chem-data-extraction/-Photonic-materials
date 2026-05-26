#!/usr/bin/env python3
"""Write manually verified web extraction records from publisher HTML pages."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib import request

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "specs/web_extraction_manifest.json"
SCHEMA_PATH = ROOT / "specs/dataset_schema.json"
LOG_PATH = ROOT / "data/extracted/extraction_log.jsonl"

USER_AGENT = (
    "Mozilla/5.0 (compatible; photonic-materials-course-extractor/0.2; "
    "+https://example.invalid/course-project)"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def schema_columns() -> list[str]:
    schema = load_json(SCHEMA_PATH)
    return [field["name"] for field in schema["fields"]]


def append_log(entry: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=True) + "\n")


def download_snapshot(page: dict) -> tuple[Path, str, list[str], str]:
    """Download a publisher HTML snapshot, falling back to an existing cache."""

    snap_path = ROOT / page["raw_snapshot_path"]
    snap_path.parent.mkdir(parents=True, exist_ok=True)

    status = "downloaded"
    issue = ""
    html = ""

    try:
        req = request.Request(
            page["url"],
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with request.urlopen(req, timeout=45) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            html = response.read().decode(charset, errors="replace")
        snap_path.write_text(html, encoding="utf-8")
    except Exception as exc:  # pragma: no cover - depends on live publisher access.
        issue = f"{type(exc).__name__}: {exc}"
        if snap_path.is_file():
            status = "cached_after_download_error"
            html = snap_path.read_text(encoding="utf-8", errors="replace")
        else:
            status = "download_failed"
            html = (
                "<!-- download failed; curated records remain in the manifest -->\n"
                f"<!-- url: {page['url']} -->\n"
                f"<!-- error: {issue} -->\n"
            )
            snap_path.write_text(html, encoding="utf-8")

    missing_terms = [
        term for term in page.get("validation_terms", []) if term not in html
    ]
    if missing_terms and status == "downloaded":
        status = "downloaded_with_missing_terms"

    return snap_path, status, missing_terms, issue


def collect_records(manifest: dict, columns: list[str]) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()

    for page in manifest.get("input_pages", []):
        snap_path, snapshot_status, missing_terms, issue = download_snapshot(page)
        source_records = page.get("records", [])

        for record in source_records:
            record_id = str(record.get("record_id", "")).strip()
            if not record_id:
                raise ValueError(f"Record without record_id in {page['page_id']}")
            if record_id in seen:
                raise ValueError(f"Duplicate record_id in manifest: {record_id}")
            seen.add(record_id)

            row = {column: record.get(column, "") for column in columns}
            row["source_id"] = row["source_id"] or page.get("source_id", "")
            row["source_url"] = row["source_url"] or page.get("url", "")
            row["doi"] = row["doi"] or page.get("doi", "")
            row["raw_file"] = row["raw_file"] or page.get("raw_snapshot_path", "")
            rows.append(row)

        append_log(
            {
                "timestamp": utc_now(),
                "step": "web_extraction",
                "source_id": page.get("source_id", ""),
                "page_id": page.get("page_id", ""),
                "status": "ok" if source_records else "skipped",
                "snapshot_status": snapshot_status,
                "tool": "extract_web.py",
                "output": manifest.get("output_records_file", ""),
                "raw_snapshot": str(snap_path.relative_to(ROOT)),
                "records": len(source_records),
                "missing_validation_terms": missing_terms,
                "issue": issue,
            }
        )

    return rows


def write_records(rows: list[dict], columns: list[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    manifest = load_json(MANIFEST)
    columns = schema_columns()
    rows = collect_records(manifest, columns)

    output_path = ROOT / manifest["output_records_file"]
    write_records(rows, columns, output_path)

    print(manifest.get("web_extraction_process", "Web extraction"))
    print(f"Pages: {len(manifest.get('input_pages', []))}")
    print(f"Records: {len(rows)}")
    print(f"Output: {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
