#!/usr/bin/env python3
"""Automatically extract photonic-sensor records from local PDF text."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

try:
    import fitz
except ImportError:  # pragma: no cover - tested through environment setup
    fitz = None

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "specs/pdf_extraction_manifest.json"
SOURCE_MAP = ROOT / "specs/source_map.json"
SCHEMA_PATH = ROOT / "specs/dataset_schema.json"
LOG_PATH = ROOT / "data/extracted/extraction_log.jsonl"


@dataclass(frozen=True)
class PdfSource:
    source_id: str
    source_type: str
    name: str
    pdf_path: Path
    source_url: str
    doi: str


@dataclass(frozen=True)
class ExtractedValue:
    value: float
    page: int
    evidence: str


RecordExtractor = Callable[[PdfSource, list[str]], list[dict]]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def schema_columns() -> list[str]:
    schema = load_json(SCHEMA_PATH)
    return [field["name"] for field in schema["fields"]]


def source_entries(source_map: dict) -> list[dict]:
    entries: list[dict] = []
    for group_sources in source_map.get("source_groups", {}).values():
        if isinstance(group_sources, list):
            entries.extend(entry for entry in group_sources if isinstance(entry, dict))
    return entries


def discover_pdf_sources(root: Path = ROOT) -> list[PdfSource]:
    source_map = load_json(SOURCE_MAP)
    sources: list[PdfSource] = []

    for entry in source_entries(source_map):
        raw_file = str(entry.get("raw_file", "")).strip()
        if not raw_file.lower().endswith(".pdf"):
            continue
        pdf_path = root / raw_file
        if not pdf_path.is_file():
            continue
        sources.append(
            PdfSource(
                source_id=str(entry.get("source_id", "")),
                source_type=str(entry.get("source_type", "")),
                name=str(entry.get("name", "")),
                pdf_path=pdf_path,
                source_url=str(entry.get("url", "")),
                doi=str(entry.get("doi", "")),
            )
        )

    raw_pdf_dir = root / "data/raw/pdf"
    known_paths = {source.pdf_path.resolve() for source in sources}
    for pdf_path in sorted(raw_pdf_dir.glob("*.pdf")):
        if pdf_path.resolve() in known_paths:
            continue
        sources.append(
            PdfSource(
                source_id=f"unmapped_{pdf_path.stem}",
                source_type="unmapped_pdf",
                name=pdf_path.stem,
                pdf_path=pdf_path,
                source_url="",
                doi="",
            )
        )

    return sorted(sources, key=lambda source: source.pdf_path.name)


def normalize_text(text: str) -> str:
    replacements = {
        "\ufb00": "ff",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
        "\u2212": "-",
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u00d7": "x",
        "\u00b5": "u",
        "\u223c": "~",
        "\u2217": "*",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def read_pdf_pages(pdf_path: Path) -> list[str]:
    if fitz is None:
        raise RuntimeError("PyMuPDF is required for automatic PDF extraction")

    with fitz.open(pdf_path) as doc:
        return [normalize_text(page.get_text("text")) for page in doc]


def parse_number(text: str) -> float:
    clean = text.replace(",", "").strip()
    clean = re.sub(r"\s+", "", clean)
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)E-?([0-9]+)", clean, flags=re.I)
    if match:
        return float(match.group(1)) * 10 ** (-int(match.group(2)))
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)x10-?([0-9]+)", clean, flags=re.I)
    if match:
        return float(match.group(1)) * 10 ** (-int(match.group(2)))
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)x10\+?([0-9]+)", clean, flags=re.I)
    if match:
        return float(match.group(1)) * 10 ** int(match.group(2))
    return float(clean)


def match_value(
    pages: list[str],
    pattern: str,
    *,
    page_numbers: list[int] | None = None,
    flags: int = re.I,
    transform: Callable[[re.Match[str]], float] | None = None,
) -> ExtractedValue:
    selected_pages = page_numbers or list(range(1, len(pages) + 1))
    for page_number in selected_pages:
        text = pages[page_number - 1]
        match = re.search(pattern, text, flags)
        if not match:
            continue
        value = transform(match) if transform else parse_number(match.group(1))
        evidence = match.group(0)
        return ExtractedValue(value=value, page=page_number, evidence=evidence)
    raise ValueError(f"No match for pattern: {pattern}")


def make_record(
    source: PdfSource,
    *,
    record_id: str,
    material_name: str,
    material_class: str,
    sensor_architecture: str,
    sensing_target: str,
    measurement_type: str,
    measurement_value: float,
    measurement_unit: str,
    extraction_confidence: str,
    notes: str,
) -> dict:
    return {
        "record_id": record_id,
        "material_name": material_name,
        "material_class": material_class,
        "sensor_architecture": sensor_architecture,
        "sensing_target": sensing_target,
        "measurement_type": measurement_type,
        "measurement_value": measurement_value,
        "measurement_unit": measurement_unit,
        "source_id": source.source_id,
        "source_url": source.source_url,
        "doi": source.doi,
        "raw_file": str(source.pdf_path.relative_to(ROOT)).replace("\\", "/"),
        "extraction_confidence": extraction_confidence,
        "notes": notes,
    }


def extract_wang_uio66(source: PdfSource, pages: list[str]) -> list[dict]:
    material = "UiO-66 3D photonic crystal"
    material_class = "MOF-based photonic crystal"
    architecture = "3D photonic crystal vapor sensor"
    target = "chlorobenzene vapor"

    sensitivity = match_value(
        pages,
        r"concentration sensitivity .*? was ([0-9.]+) nm ppm",
        page_numbers=[6],
    )
    lod = match_value(
        pages,
        r"LOD .*? toward C6H5Cl was ([0-9.]+) ppm",
        page_numbers=[6],
    )
    q_factor = match_value(
        pages,
        r"quality factor .*? respectively calculated to be ([0-9.]+) and",
        page_numbers=[6],
    )
    response = match_value(
        pages,
        r"response time and recovery time of ([0-9.]+) s and ([0-9.]+) s",
        page_numbers=[6],
    )
    recovery = match_value(
        pages,
        r"response time and recovery time of ([0-9.]+) s and ([0-9.]+) s",
        page_numbers=[6],
        transform=lambda match: parse_number(match.group(2)),
    )
    shift = match_value(
        pages,
        r"500 ppm.*?wavelength .*? were by about .*? and ([0-9.]+) nm",
        page_numbers=[6],
    )

    return [
        make_record(
            source,
            record_id="rec_wang_2022_uio66_sensitivity_001",
            material_name=material,
            material_class=material_class,
            sensor_architecture=architecture,
            sensing_target=target,
            measurement_type="sensitivity",
            measurement_value=sensitivity.value,
            measurement_unit="nm/ppm",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {sensitivity.page}; fitted slope evidence: {sensitivity.evidence}",
        ),
        make_record(
            source,
            record_id="rec_wang_2022_uio66_lod_001",
            material_name=material,
            material_class=material_class,
            sensor_architecture=architecture,
            sensing_target=target,
            measurement_type="limit_of_detection",
            measurement_value=lod.value,
            measurement_unit="ppm",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {lod.page}; evidence: {lod.evidence}",
        ),
        make_record(
            source,
            record_id="rec_wang_2022_uio66_q_factor_001",
            material_name=material,
            material_class=material_class,
            sensor_architecture=architecture,
            sensing_target=target,
            measurement_type="quality_factor",
            measurement_value=q_factor.value,
            measurement_unit="dimensionless",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {q_factor.page}; evidence: {q_factor.evidence}",
        ),
        make_record(
            source,
            record_id="rec_wang_2022_uio66_response_time_001",
            material_name=material,
            material_class=material_class,
            sensor_architecture=architecture,
            sensing_target=target,
            measurement_type="response_time",
            measurement_value=response.value,
            measurement_unit="s",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {response.page}; measured at 500 ppm chlorobenzene vapor.",
        ),
        make_record(
            source,
            record_id="rec_wang_2022_uio66_recovery_time_001",
            material_name=material,
            material_class=material_class,
            sensor_architecture=architecture,
            sensing_target=target,
            measurement_type="recovery_time",
            measurement_value=recovery.value,
            measurement_unit="s",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {recovery.page}; measured at 500 ppm chlorobenzene vapor.",
        ),
        make_record(
            source,
            record_id="rec_wang_2022_uio66_wavelength_shift_001",
            material_name=material,
            material_class=material_class,
            sensor_architecture=architecture,
            sensing_target=target,
            measurement_type="wavelength_shift",
            measurement_value=shift.value,
            measurement_unit="nm",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {shift.page}; shift at 500 ppm chlorobenzene vapor.",
        ),
    ]


def extract_nazeri_hcpcf(source: PdfSource, pages: list[str]) -> list[dict]:
    material = "hollow-core photonic crystal fiber"
    material_class = "photonic crystal fiber"

    sensitivity = match_value(
        pages,
        r"highest sensitivity was achieved by sensor C: ([0-9]+) \(nm/RIU\)",
        page_numbers=[9],
    )
    resolution = match_value(
        pages,
        r"sensor C .*? has a RI resolution of ([0-9.]+)\s*E-([0-9]+)",
        page_numbers=[10],
        transform=lambda match: float(match.group(1)) * 10 ** (-int(match.group(2))),
    )
    methane_times = match_value(
        pages,
        r"Methane: response \(s\)/recovery \(s\) ([0-9]+)/([0-9]+)",
        page_numbers=[11],
    )
    methane_recovery = match_value(
        pages,
        r"Methane: response \(s\)/recovery \(s\) ([0-9]+)/([0-9]+)",
        page_numbers=[11],
        transform=lambda match: float(match.group(2)),
    )

    return [
        make_record(
            source,
            record_id="rec_nazeri_2020_hcpcf_sensor_c_sensitivity_001",
            material_name=material,
            material_class=material_class,
            sensor_architecture="HC-PCF Mach-Zehnder interferometer sensor C, 3.30 mm HC-PCF length",
            sensing_target="gas refractive index",
            measurement_type="sensitivity",
            measurement_value=sensitivity.value,
            measurement_unit="nm/RIU",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {sensitivity.page}; RI range 1.0000347-1.000436.",
        ),
        make_record(
            source,
            record_id="rec_nazeri_2020_hcpcf_sensor_c_resolution_001",
            material_name=material,
            material_class=material_class,
            sensor_architecture="HC-PCF Mach-Zehnder interferometer sensor C, 3.30 mm HC-PCF length",
            sensing_target="gas refractive index",
            measurement_type="resolution",
            measurement_value=resolution.value,
            measurement_unit="RIU",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {resolution.page}; evidence: {resolution.evidence}",
        ),
        make_record(
            source,
            record_id="rec_nazeri_2020_hcpcf_sensor_a_methane_response_001",
            material_name=material,
            material_class=material_class,
            sensor_architecture="HC-PCF Mach-Zehnder interferometer sensor A, 4.97 mm HC-PCF length",
            sensing_target="methane gas",
            measurement_type="response_time",
            measurement_value=methane_times.value,
            measurement_unit="s",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {methane_times.page}; first methane pair in Table 3 is sensor A.",
        ),
        make_record(
            source,
            record_id="rec_nazeri_2020_hcpcf_sensor_a_methane_recovery_001",
            material_name=material,
            material_class=material_class,
            sensor_architecture="HC-PCF Mach-Zehnder interferometer sensor A, 4.97 mm HC-PCF length",
            sensing_target="methane gas",
            measurement_type="recovery_time",
            measurement_value=methane_recovery.value,
            measurement_unit="s",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {methane_recovery.page}; first methane pair in Table 3 is sensor A.",
        ),
    ]


def extract_dolci_fiber_tip(source: PdfSource, pages: list[str]) -> list[dict]:
    sensitivity = match_value(
        pages,
        r"sensitivities of ([0-9]+)\D+[0-9]+ nm/RIU and [0-9]+",
        page_numbers=[5],
    )
    lod = match_value(
        pages,
        r"LoD .*? = ([0-9]+) pM",
        page_numbers=[6],
    )

    return [
        make_record(
            source,
            record_id="rec_dolci_2025_fiber_tip_bulk_sensitivity_001",
            material_name="fiber-tip photonic crystal",
            material_class="nanophotonic resonator",
            sensor_architecture="dual-channel fiber-tip photonic crystal biosensor",
            sensing_target="bulk refractive index",
            measurement_type="sensitivity",
            measurement_value=sensitivity.value,
            measurement_unit="nm/RIU",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {sensitivity.page}; sensor channel reported before reference channel.",
        ),
        make_record(
            source,
            record_id="rec_dolci_2025_fiber_tip_anti_igg_lod_001",
            material_name="fiber-tip photonic crystal",
            material_class="nanophotonic resonator",
            sensor_architecture="dual-channel fiber-tip photonic crystal biosensor in continuous flow",
            sensing_target="anti-IgG in undiluted serum",
            measurement_type="limit_of_detection",
            measurement_value=lod.value,
            measurement_unit="pM",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {lod.page}; equivalent mass concentration reported as 9 ng/mL.",
        ),
    ]


def extract_shaban_au_1dpc(source: PdfSource, pages: list[str]) -> list[dict]:
    avg_ri = match_value(
        pages,
        r"average sensitivity is ([0-9.]+) nm/RIU",
        page_numbers=[6],
    )
    right_edge = match_value(
        pages,
        r"at .*? are [0-9.]+, [0-9.]+ and ([0-9.]+) nm/RIU",
        page_numbers=[6],
    )
    glucose_avg = match_value(
        pages,
        r"average sensitivity is about ([0-9.]+) nm/g/dl",
        page_numbers=[8],
    )
    glucose_max = match_value(
        pages,
        r"max-?\s*imum sensitivity is ([0-9.]+) nm/g/dl",
        page_numbers=[8],
    )
    pbg_slope = match_value(
        pages,
        r"slope of this curve .*? ([0-9.]+) nm/\(g/dl\)",
        page_numbers=[8],
    )

    base = {
        "material_name": "Au/1D photonic crystal",
        "material_class": "plasmonic/photonic hybrid",
    }

    return [
        make_record(
            source,
            record_id="rec_shaban_2017_au_1dpc_ri_sensitivity_avg_001",
            **base,
            sensor_architecture="gold-coated one-dimensional photonic crystal microfluidic sensor",
            sensing_target="environmental refractive index",
            measurement_type="sensitivity",
            measurement_value=avg_ri.value,
            measurement_unit="nm/RIU",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {avg_ri.page}; average RI sensitivity.",
        ),
        make_record(
            source,
            record_id="rec_shaban_2017_au_1dpc_right_edge_sensitivity_001",
            **base,
            sensor_architecture="gold-coated one-dimensional photonic crystal microfluidic sensor",
            sensing_target="environmental refractive index",
            measurement_type="sensitivity",
            measurement_value=right_edge.value,
            measurement_unit="nm/RIU",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {right_edge.page}; right PBG edge sensitivity.",
        ),
        make_record(
            source,
            record_id="rec_shaban_2017_au_1dpc_glucose_sensitivity_avg_001",
            **base,
            sensor_architecture="gold-coated one-dimensional photonic crystal glucose sensor",
            sensing_target="glucose concentration in aqueous solution",
            measurement_type="sensitivity",
            measurement_value=glucose_avg.value,
            measurement_unit="nm/(g/dL)",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {glucose_avg.page}; average SPR sensitivity.",
        ),
        make_record(
            source,
            record_id="rec_shaban_2017_au_1dpc_glucose_sensitivity_max_001",
            **base,
            sensor_architecture="gold-coated one-dimensional photonic crystal glucose sensor",
            sensing_target="glucose concentration in aqueous solution",
            measurement_type="sensitivity",
            measurement_value=glucose_max.value,
            measurement_unit="nm/(g/dL)",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {glucose_max.page}; maximum sensitivity at 0.031 g/dL.",
        ),
        make_record(
            source,
            record_id="rec_shaban_2017_au_1dpc_pbg_width_slope_001",
            **base,
            sensor_architecture="gold-coated one-dimensional photonic crystal glucose sensor",
            sensing_target="glucose concentration in aqueous solution",
            measurement_type="sensitivity",
            measurement_value=pbg_slope.value,
            measurement_unit="nm/(g/dL)",
            extraction_confidence="medium",
            notes=f"Automatically extracted from page {pbg_slope.page}; slope of PBG-width decrease.",
        ),
    ]


def power_from_match(match: re.Match[str]) -> float:
    base = float(match.group(1))
    exponent = int(match.group(2))
    sign = -1 if "-" in match.group(0).replace(" ", "") else 1
    return base * 10 ** (sign * exponent)


def extract_zaky_tamm(source: PdfSource, pages: list[str]) -> list[dict]:
    sensitivity = match_value(
        pages,
        r"S\s*=\s*([0-9.]+)\s*x\s*10\s*5 nm/RIU",
        page_numbers=[8, 1],
        transform=lambda match: float(match.group(1)) * 10**5,
    )
    lod = match_value(
        pages,
        r"DL\s*=\s*([0-9.]+)\s*x\s*10\s*-\s*([0-9]+) RIU",
        page_numbers=[1, 8],
        transform=lambda match: float(match.group(1)) * 10 ** (-int(match.group(2))),
    )
    q_factor = match_value(
        pages,
        r"QF\s*=\s*([0-9.]+)\s*x\s*10\s*3",
        page_numbers=[8],
        transform=lambda match: float(match.group(1)) * 10**3,
    )

    return [
        make_record(
            source,
            record_id="rec_zaky_2020_tamm_sensitivity_001",
            material_name="Tamm-state 1D photonic crystal",
            material_class="1D photonic crystal",
            sensor_architecture="prism-coupled Tamm-state one-dimensional photonic crystal gas sensor",
            sensing_target="gas refractive index",
            measurement_type="sensitivity",
            measurement_value=sensitivity.value,
            measurement_unit="nm/RIU",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {sensitivity.page}; theoretical optimized sensor.",
        ),
        make_record(
            source,
            record_id="rec_zaky_2020_tamm_lod_001",
            material_name="Tamm-state 1D photonic crystal",
            material_class="1D photonic crystal",
            sensor_architecture="prism-coupled Tamm-state one-dimensional photonic crystal gas sensor",
            sensing_target="gas refractive index",
            measurement_type="limit_of_detection",
            measurement_value=lod.value,
            measurement_unit="RIU",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {lod.page}; theoretical optimized sensor.",
        ),
        make_record(
            source,
            record_id="rec_zaky_2020_tamm_q_factor_001",
            material_name="Tamm-state 1D photonic crystal",
            material_class="1D photonic crystal",
            sensor_architecture="prism-coupled Tamm-state one-dimensional photonic crystal gas sensor",
            sensing_target="gas refractive index",
            measurement_type="quality_factor",
            measurement_value=q_factor.value,
            measurement_unit="dimensionless",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {q_factor.page}; FWHM reported as 0.52 nm.",
        ),
    ]


def extract_lin_seira(source: PdfSource, pages: list[str]) -> list[dict]:
    lod = match_value(
        pages,
        r"detection limit .*? is ([0-9]+), [0-9]+, and [0-9]+ ppm for the integrated device",
        page_numbers=[7],
    )
    q_factor = match_value(
        pages,
        r"low Q-factor \(~([0-9.]+)\)",
        page_numbers=[7],
    )

    return [
        make_record(
            source,
            record_id="rec_lin_2018_seira_co2_lod_001",
            material_name="Au nanopatch array with ZIF-8 MOF film",
            material_class="plasmonic/photonic hybrid",
            sensor_architecture="suspended Si3N4 nanomembrane on-chip SEIRA gas sensor",
            sensing_target="CO2 gas",
            measurement_type="limit_of_detection",
            measurement_value=lod.value,
            measurement_unit="ppm",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {lod.page}; extrapolated for a 4 mm absorption path.",
        ),
        make_record(
            source,
            record_id="rec_lin_2018_seira_q_factor_001",
            material_name="Au nanopatch array with ZIF-8 MOF film",
            material_class="plasmonic/photonic hybrid",
            sensor_architecture="suspended Si3N4 nanomembrane on-chip SEIRA gas sensor",
            sensing_target="CO2 gas",
            measurement_type="quality_factor",
            measurement_value=q_factor.value,
            measurement_unit="dimensionless",
            extraction_confidence="high",
            notes=f"Automatically extracted from page {q_factor.page}; measured experimental spectrum.",
        ),
    ]


EXTRACTORS: dict[str, RecordExtractor] = {
    "paper_wang_2022_uio66_pc": extract_wang_uio66,
    "paper_nazeri_2020_hcpcf_mzi_gas": extract_nazeri_hcpcf,
    "paper_dolci_2025_fiber_tip_pc_biosensing": extract_dolci_fiber_tip,
    "paper_shaban_2017_plasmonic_1d_pc": extract_shaban_au_1dpc,
    "paper_zaky_2020_tamm_1d_pc_gas": extract_zaky_tamm,
    "paper_lin_2018_seira_on_chip_gas": extract_lin_seira,
}


def extract_source(source: PdfSource) -> tuple[list[dict], dict]:
    event = {
        "timestamp": utc_now(),
        "step": "pdf_extraction",
        "source_id": source.source_id,
        "pdf": str(source.pdf_path.relative_to(ROOT)).replace("\\", "/"),
        "tool": "extract_pdf.py",
        "output": "",
        "records": 0,
        "status": "skipped",
        "issue": "",
    }

    extractor = EXTRACTORS.get(source.source_id)
    if extractor is None:
        event["issue"] = "No automatic extraction rule for this PDF; review/unmapped sources are scanned but not converted to records."
        return [], event

    pages = read_pdf_pages(source.pdf_path)
    records = extractor(source, pages)
    event["records"] = len(records)
    event["status"] = "ok"
    return records, event


def extract_all_sources(sources: list[PdfSource] | None = None) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    events: list[dict] = []
    seen: set[str] = set()

    for source in sources or discover_pdf_sources():
        records, event = extract_source(source)
        for record in records:
            record_id = str(record.get("record_id", "")).strip()
            if not record_id:
                raise ValueError(f"Record without record_id for {source.source_id}")
            if record_id in seen:
                raise ValueError(f"Duplicate record_id: {record_id}")
            seen.add(record_id)
            rows.append(record)
        events.append(event)

    return rows, events


def write_records(rows: list[dict], columns: list[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def write_log(events: list[dict], output_file: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", encoding="utf-8") as f:
        for event in events:
            event = dict(event)
            event["output"] = output_file
            f.write(json.dumps(event, ensure_ascii=True) + "\n")


def main() -> None:
    manifest = load_json(MANIFEST)
    columns = schema_columns()
    output_file = manifest["output_records_file"]
    output_path = ROOT / output_file

    rows, events = extract_all_sources()
    write_records(rows, columns, output_path)
    write_log(events, output_file)

    scanned = len(events)
    extracted = sum(1 for event in events if event["status"] == "ok")
    skipped = scanned - extracted

    print(manifest.get("pdf_extraction_process", "PDF extraction"))
    print(f"PDFs scanned: {scanned}")
    print(f"PDFs with records: {extracted}")
    print(f"PDFs skipped: {skipped}")
    print(f"Records: {len(rows)}")
    print(f"Output: {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
