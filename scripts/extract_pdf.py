#!/usr/bin/env python3
"""Write manually verified PDF extraction records from the manifest."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "specs/pdf_extraction_manifest.json"
SCHEMA_PATH = ROOT / "specs/dataset_schema.json"
LOG_PATH = ROOT / "data/extracted/extraction_log.jsonl"


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


def collect_records(manifest: dict, columns: list[str]) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()

    for source in manifest.get("input_sources", []):
        pdf_path = ROOT / source["pdf_path"]
        if not pdf_path.is_file():
            raise FileNotFoundError(f"Missing PDF: {source['pdf_path']}")

        source_records = source.get("records", [])
        if not source_records:
            append_log(
                {
                    "timestamp": utc_now(),
                    "step": "pdf_extraction",
                    "source_id": source.get("source_id", ""),
                    "status": "skipped",
                    "tool": "extract_pdf.py",
                    "output": manifest.get("output_records_file", ""),
                    "issue": "No curated records listed in manifest",
                }
            )
            continue

        for record in source_records:
            record_id = str(record.get("record_id", "")).strip()
            if not record_id:
                raise ValueError(f"Record without record_id in {source['source_id']}")
            if record_id in seen:
                raise ValueError(f"Duplicate record_id in manifest: {record_id}")
            seen.add(record_id)

            row = {column: record.get(column, "") for column in columns}
            rows.append(row)

        append_log(
            {
                "timestamp": utc_now(),
                "step": "pdf_extraction",
                "source_id": source.get("source_id", ""),
                "status": "ok",
                "tool": "extract_pdf.py",
                "output": manifest.get("output_records_file", ""),
                "records": len(source_records),
                "issue": "",
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

    print(manifest.get("pdf_extraction_process", "PDF extraction"))
    print(f"Sources: {len(manifest.get('input_sources', []))}")
    print(f"Records: {len(rows)}")
    print(f"Output: {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
