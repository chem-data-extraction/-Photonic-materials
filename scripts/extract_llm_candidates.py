#!/usr/bin/env python3
"""Draft review-only extraction candidates with the DeepSeek chat API."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

from extract_pdf import PdfSource, discover_pdf_sources, read_pdf_pages

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "specs/llm_extraction_manifest.json"
SCHEMA_PATH = ROOT / "specs/dataset_schema.json"

DEFAULT_API_BASE = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_OUTPUT = ROOT / "data/extracted/llm_candidate_records.jsonl"
DEFAULT_MAX_CANDIDATES = 4

METRIC_KEYWORDS = (
    "sensitivity",
    "limit of detection",
    "lod",
    "wavelength shift",
    "response time",
    "recovery time",
    "quality factor",
    "q factor",
    "resolution",
    "detection range",
    "nm/riu",
    "ppm",
    "riu",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def schema_columns(schema_path: Path = SCHEMA_PATH) -> list[str]:
    schema = load_json(schema_path)
    return [field["name"] for field in schema["fields"]]


def allowed_measurement_types(schema_path: Path = SCHEMA_PATH) -> set[str]:
    schema = load_json(schema_path)
    for field in schema["fields"]:
        if field["name"] == "measurement_type":
            return set(field.get("allowed_values", []))
    return set()


def compact_text(text: str, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def metric_snippets(text: str, max_chars: int) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_chars:
        return compact

    lowered = compact.lower()
    positions = sorted(
        {
            match.start()
            for keyword in METRIC_KEYWORDS
            for match in re.finditer(re.escape(keyword), lowered)
        }
    )
    if not positions:
        return compact_text(compact, max_chars)

    window = max(220, min(520, max_chars // 3))
    snippets: list[str] = []
    used = 0
    last_end = -1
    for pos in positions:
        start = max(0, pos - window)
        end = min(len(compact), pos + window)
        if end - start > max_chars:
            half = max_chars // 2
            start = max(0, pos - half)
            end = min(len(compact), start + max_chars)
            start = max(0, end - max_chars)
        if start <= last_end:
            if snippets:
                extension = compact[last_end:end]
                if used + len(extension) > max_chars:
                    break
                snippets[-1] += extension
                used += len(extension)
                last_end = end
            continue

        snippet = compact[start:end].strip()
        separator = " ... " if snippets else ""
        if used + len(separator) + len(snippet) > max_chars:
            break
        snippets.append(separator + snippet)
        used += len(separator) + len(snippet)
        last_end = end

    return "".join(snippets) if snippets else compact_text(compact, max_chars)


def metric_score(text: str) -> int:
    lowered = text.lower()
    return sum(lowered.count(keyword) for keyword in METRIC_KEYWORDS)


def select_candidate_pages(
    pages: list[str],
    *,
    max_pages: int,
    max_chars_per_page: int,
) -> list[dict[str, Any]]:
    scored = [
        (metric_score(text), page_number, text)
        for page_number, text in enumerate(pages, start=1)
        if text.strip()
    ]
    selected = [item for item in scored if item[0] > 0]
    if not selected:
        selected = scored

    selected = sorted(selected, key=lambda item: (-item[0], item[1]))[:max_pages]
    selected = sorted(selected, key=lambda item: item[1])
    return [
        {
            "page": page_number,
            "score": score,
            "text": metric_snippets(text, max_chars_per_page),
        }
        for score, page_number, text in selected
    ]


def build_messages(
    *,
    source: PdfSource,
    pages: list[dict[str, Any]],
    columns: list[str],
    allowed_types: set[str],
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
) -> list[dict[str, str]]:
    system_prompt = (
        "You extract candidate structured records for a photonic-material optical-sensing "
        "dataset. Return strict JSON only. Do not invent values. Use only quantitative "
        "measurements explicitly supported by the supplied text. Every candidate must include "
        "short evidence_text copied from the supplied text and evidence_page. If there are no "
        "supported measurements, return {\"records\": []}."
    )
    user_payload = {
        "task": "Return JSON with a records array of review-only candidate records.",
        "max_records": max_candidates,
        "output_limits": {
            "records": f"at most {max_candidates}",
            "evidence_text": "at most 30 words",
            "notes": "at most 25 words",
            "review_reason": "at most 20 words",
        },
        "json_shape": {
            "records": [
                {
                    "record": {column: "" for column in columns},
                    "evidence_page": 0,
                    "evidence_text": "short source-supported evidence",
                    "llm_confidence": "high|medium|low",
                    "needs_review": True,
                    "review_reason": "why a human should confirm or how the value was mapped",
                }
            ]
        },
        "schema_columns": columns,
        "allowed_measurement_type_values": sorted(allowed_types),
        "source": {
            "source_id": source.source_id,
            "name": source.name,
            "source_url": source.source_url,
            "doi": source.doi,
            "raw_file": str(source.pdf_path.relative_to(ROOT)).replace("\\", "/"),
        },
        "rules": [
            "Set measurement_value to a JSON number, not a string.",
            "Use one record per scalar measurement.",
            "Keep units exactly as reported when possible.",
            "Use source_id, source_url, doi, and raw_file from the source object.",
            "Set needs_review to true for every record.",
            "Do not include review-article summary values unless the text gives a primary measurement.",
            f"Return no more than {max_candidates} highest-confidence records for this source.",
            "Prefer complete, schema-ready records over partial or ambiguous measurements.",
            "Keep evidence_text, notes, and review_reason short.",
            "Do not include markdown, explanations, citations outside evidence_text, or extra keys.",
        ],
        "pages": pages,
    }
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]


def call_deepseek(
    *,
    api_key: str,
    api_base: str,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    timeout: int,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    req = request.Request(
        api_base.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API returned HTTP {exc.code}: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"DeepSeek API request failed: {exc}") from exc

    data = json.loads(body)
    choice = data.get("choices", [{}])[0]
    if choice.get("finish_reason") == "length":
        raise RuntimeError("DeepSeek response was truncated; lower --max-pages-per-source or raise --max-tokens")
    content = choice.get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("DeepSeek returned an empty message content")
    return json.loads(content)


def slug(value: object, max_len: int = 48) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).lower()).strip("_")
    return (text or "unknown")[:max_len].strip("_") or "unknown"


def coerce_confidence(value: object) -> str:
    text = str(value or "").strip().lower()
    return text if text in {"high", "medium", "low"} else "low"


def normalize_candidate(
    item: dict[str, Any],
    *,
    source: PdfSource,
    columns: list[str],
    allowed_types: set[str],
    index: int,
    model: str,
) -> dict[str, Any] | None:
    record = item.get("record", item)
    if not isinstance(record, dict):
        return None

    measurement_type = str(record.get("measurement_type", "")).strip()
    if allowed_types and measurement_type not in allowed_types:
        return None

    try:
        measurement_value = float(record.get("measurement_value", ""))
    except (TypeError, ValueError):
        return None

    evidence_page = item.get("evidence_page") or record.get("evidence_page") or ""
    candidate_id = "llm_candidate_{source}_{metric}_{target}_{page}_{index:03d}".format(
        source=slug(source.source_id),
        metric=slug(measurement_type, 32),
        target=slug(record.get("sensing_target", ""), 32),
        page=slug(evidence_page, 12),
        index=index,
    )

    schema_record = {column: record.get(column, "") for column in columns}
    schema_record.update(
        {
            "record_id": candidate_id,
            "measurement_type": measurement_type,
            "measurement_value": measurement_value,
            "source_id": source.source_id,
            "source_url": source.source_url,
            "doi": source.doi,
            "raw_file": str(source.pdf_path.relative_to(ROOT)).replace("\\", "/"),
            "extraction_confidence": coerce_confidence(
                item.get("llm_confidence", schema_record.get("extraction_confidence"))
            ),
        }
    )

    notes = str(schema_record.get("notes", "") or "").strip()
    review_note = "LLM candidate generated by DeepSeek; review before adding to the final dataset."
    schema_record["notes"] = f"{notes} {review_note}".strip()

    return {
        "candidate_id": candidate_id,
        "generated_at": utc_now(),
        "generator": "DeepSeek chat completions",
        "model": model,
        "source_id": source.source_id,
        "source_name": source.name,
        "schema_record": schema_record,
        "evidence_page": evidence_page,
        "evidence_text": item.get("evidence_text", ""),
        "needs_review": True,
        "review_reason": item.get("review_reason", "LLM extraction candidate requires source verification."),
    }


def iter_sources(source_ids: list[str] | None, limit_sources: int | None) -> list[PdfSource]:
    sources = discover_pdf_sources(ROOT)
    if source_ids:
        wanted = set(source_ids)
        sources = [source for source in sources if source.source_id in wanted]
    if limit_sources is not None:
        sources = sources[:limit_sources]
    return sources


def write_candidates(path: Path, candidates: list[dict[str, Any]], *, append: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as f:
        for candidate in candidates:
            f.write(json.dumps(candidate, ensure_ascii=False) + "\n")


def project_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_args(argv: list[str]) -> argparse.Namespace:
    manifest = load_json(MANIFEST) if MANIFEST.is_file() else {}
    defaults = manifest.get("defaults", {})
    parser = argparse.ArgumentParser(
        description="Draft DeepSeek LLM candidate records from local PDF text. Candidates are not merged automatically."
    )
    parser.add_argument("--source-id", action="append", help="Restrict extraction to a source_id; repeatable.")
    parser.add_argument("--limit-sources", type=int, help="Process only the first N discovered PDF sources.")
    parser.add_argument("--output", type=Path, default=Path(defaults.get("output_file", DEFAULT_OUTPUT)))
    parser.add_argument("--append", action="store_true", help="Append to the output JSONL instead of replacing it.")
    parser.add_argument("--dry-run", action="store_true", help="Print selected pages and prompt sizes without calling DeepSeek.")
    parser.add_argument("--model", default=os.getenv("DEEPSEEK_MODEL", defaults.get("model", DEFAULT_MODEL)))
    parser.add_argument("--api-base", default=os.getenv("DEEPSEEK_API_BASE", defaults.get("api_base", DEFAULT_API_BASE)))
    parser.add_argument("--max-pages-per-source", type=int, default=int(defaults.get("max_pages_per_source", 4)))
    parser.add_argument("--max-chars-per-page", type=int, default=int(defaults.get("max_chars_per_page", 4500)))
    parser.add_argument("--max-candidates", type=int, default=int(defaults.get("max_candidates_per_source", DEFAULT_MAX_CANDIDATES)))
    parser.add_argument("--max-tokens", type=int, default=int(defaults.get("max_tokens", 3000)))
    parser.add_argument("--timeout", type=int, default=int(defaults.get("timeout_seconds", 90)))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    output_path = project_path(args.output)
    columns = schema_columns()
    allowed_types = allowed_measurement_types()
    sources = iter_sources(args.source_id, args.limit_sources)

    if not sources:
        print("No local PDF sources discovered. Check data/raw/pdf and specs/source_map.json.", file=sys.stderr)
        return 1

    if args.dry_run:
        for source in sources:
            pages = select_candidate_pages(
                read_pdf_pages(source.pdf_path),
                max_pages=args.max_pages_per_source,
                max_chars_per_page=args.max_chars_per_page,
            )
            messages = build_messages(
                source=source,
                pages=pages,
                columns=columns,
                allowed_types=allowed_types,
                max_candidates=args.max_candidates,
            )
            print(f"{source.source_id}: pages {[page['page'] for page in pages]}, prompt chars {sum(len(m['content']) for m in messages)}")
        return 0

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY is required for DeepSeek LLM extraction. See README.md.", file=sys.stderr)
        return 2

    all_candidates: list[dict[str, Any]] = []
    sequence = 1
    for source in sources:
        pages = select_candidate_pages(
            read_pdf_pages(source.pdf_path),
            max_pages=args.max_pages_per_source,
            max_chars_per_page=args.max_chars_per_page,
        )
        messages = build_messages(
            source=source,
            pages=pages,
            columns=columns,
            allowed_types=allowed_types,
            max_candidates=args.max_candidates,
        )
        response = call_deepseek(
            api_key=api_key,
            api_base=args.api_base,
            model=args.model,
            messages=messages,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
        )
        for item in response.get("records", []):
            candidate = normalize_candidate(
                item,
                source=source,
                columns=columns,
                allowed_types=allowed_types,
                index=sequence,
                model=args.model,
            )
            if candidate is None:
                continue
            all_candidates.append(candidate)
            sequence += 1

    write_candidates(output_path, all_candidates, append=args.append)
    print(f"Wrote {len(all_candidates)} DeepSeek candidate record(s) to {display_path(output_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
