"""Tests for DeepSeek LLM candidate extraction helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from extract_llm_candidates import (  # noqa: E402
    build_messages,
    normalize_candidate,
    select_candidate_pages,
)
from extract_pdf import PdfSource  # noqa: E402


def make_source() -> PdfSource:
    return PdfSource(
        source_id="paper_example_photonic_sensor",
        source_type="primary_article",
        name="Example photonic sensor",
        pdf_path=ROOT / "data/raw/pdf/example.pdf",
        source_url="https://doi.org/10.0000/example",
        doi="10.0000/example",
    )


def test_select_candidate_pages_prefers_metric_text() -> None:
    pages = [
        "Introduction and fabrication details.",
        "The sensor sensitivity was 42 nm/RIU and the limit of detection was 2 ppm.",
        "References and acknowledgements.",
    ]

    selected = select_candidate_pages(pages, max_pages=1, max_chars_per_page=1000)

    assert [page["page"] for page in selected] == [2]
    assert "42 nm/RIU" in selected[0]["text"]


def test_build_messages_requests_json_candidates() -> None:
    source = make_source()
    messages = build_messages(
        source=source,
        pages=[{"page": 2, "score": 2, "text": "LOD was 2 ppm."}],
        columns=["record_id", "measurement_type", "measurement_value"],
        allowed_types={"limit_of_detection"},
    )

    joined = "\n".join(message["content"] for message in messages)
    assert "strict JSON" in joined
    assert "limit_of_detection" in joined
    assert source.source_id in joined


def test_normalize_candidate_marks_record_for_review() -> None:
    source = make_source()
    item = {
        "record": {
            "material_name": "Example photonic crystal",
            "material_class": "3D photonic crystal",
            "sensor_architecture": "example sensor",
            "sensing_target": "test vapor",
            "measurement_type": "limit_of_detection",
            "measurement_value": 2,
            "measurement_unit": "ppm",
            "notes": "Reported in the abstract.",
        },
        "evidence_page": 2,
        "evidence_text": "The limit of detection was 2 ppm.",
        "llm_confidence": "medium",
    }

    candidate = normalize_candidate(
        item,
        source=source,
        columns=[
            "record_id",
            "material_name",
            "material_class",
            "sensor_architecture",
            "sensing_target",
            "measurement_type",
            "measurement_value",
            "measurement_unit",
            "source_id",
            "source_url",
            "doi",
            "raw_file",
            "extraction_confidence",
            "notes",
        ],
        allowed_types={"limit_of_detection"},
        index=1,
        model="deepseek-v4-pro",
    )

    assert candidate is not None
    assert candidate["needs_review"] is True
    assert candidate["schema_record"]["source_id"] == source.source_id
    assert candidate["schema_record"]["measurement_value"] == 2.0
    assert candidate["schema_record"]["record_id"].startswith("llm_candidate_")
