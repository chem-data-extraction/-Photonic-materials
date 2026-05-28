"""Tests for automatic PDF extraction rules."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from extract_pdf import discover_pdf_sources, extract_all_sources, schema_columns  # noqa: E402


def test_discovers_every_local_pdf() -> None:
    raw_pdfs = sorted((ROOT / "data/raw/pdf").glob("*.pdf"))
    sources = discover_pdf_sources(ROOT)

    assert len(sources) == len(raw_pdfs)
    assert {source.pdf_path.name for source in sources} == {path.name for path in raw_pdfs}


def test_automatic_extraction_scans_all_pdfs() -> None:
    rows, events = extract_all_sources(discover_pdf_sources(ROOT))

    assert len(events) == len(list((ROOT / "data/raw/pdf").glob("*.pdf")))
    assert len(rows) == 22
    assert sum(event["status"] == "ok" for event in events) == 6
    assert sum(event["status"] == "skipped" for event in events) == 4


def test_automatic_extraction_source_counts() -> None:
    rows, _events = extract_all_sources(discover_pdf_sources(ROOT))
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["source_id"]] = counts.get(row["source_id"], 0) + 1

    assert counts == {
        "paper_dolci_2025_fiber_tip_pc_biosensing": 2,
        "paper_lin_2018_seira_on_chip_gas": 2,
        "paper_nazeri_2020_hcpcf_mzi_gas": 4,
        "paper_shaban_2017_plasmonic_1d_pc": 5,
        "paper_wang_2022_uio66_pc": 6,
        "paper_zaky_2020_tamm_1d_pc_gas": 3,
    }


def test_key_values_are_extracted_from_pdf_text() -> None:
    rows, _events = extract_all_sources(discover_pdf_sources(ROOT))
    by_id = {row["record_id"]: row for row in rows}

    assert by_id["rec_wang_2022_uio66_lod_001"]["measurement_value"] == pytest.approx(1.64)
    assert by_id["rec_nazeri_2020_hcpcf_sensor_c_sensitivity_001"]["measurement_value"] == pytest.approx(4629)
    assert by_id["rec_dolci_2025_fiber_tip_anti_igg_lod_001"]["measurement_value"] == pytest.approx(60)
    assert by_id["rec_shaban_2017_au_1dpc_glucose_sensitivity_max_001"]["measurement_value"] == pytest.approx(407.42)
    assert by_id["rec_zaky_2020_tamm_sensitivity_001"]["measurement_value"] == pytest.approx(190000)
    assert by_id["rec_lin_2018_seira_co2_lod_001"]["measurement_value"] == pytest.approx(52)


def test_extracted_rows_match_dataset_schema_columns() -> None:
    rows, _events = extract_all_sources(discover_pdf_sources(ROOT))
    expected = set(schema_columns())

    assert rows
    assert all(set(row) == expected for row in rows)
    assert len({row["record_id"] for row in rows}) == len(rows)
