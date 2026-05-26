#!/usr/bin/env python3
"""Clean extracted photonic-sensor records into the final dataset schema."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

MERGED_PATH = ROOT / "data/interim/merged_records.csv"
SCHEMA_PATH = ROOT / "specs/dataset_schema.json"
DATASET_PATH = ROOT / "data/processed/dataset.csv"

MISSING_TOKENS = {"", "na", "n/a", "none", "null", "-", "nan"}
CONFIDENCE_ALLOWED = {"high", "medium", "low", "unknown", ""}


def load_schema_columns() -> list[str]:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    return [field["name"] for field in schema["fields"]]


def normalize_missing(value: object):
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.lower() in MISSING_TOKENS:
        return None
    return text


def normalize_confidence(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    return text if text in CONFIDENCE_ALLOWED else "unknown"


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    columns = load_schema_columns()
    out = df.copy()

    for column in columns:
        if column not in out.columns:
            out[column] = None
    out = out[columns]

    for column in out.columns:
        if column == "measurement_value":
            out[column] = pd.to_numeric(out[column], errors="coerce")
        elif column == "extraction_confidence":
            out[column] = out[column].map(normalize_confidence)
        else:
            out[column] = out[column].map(normalize_missing)

    if "record_id" in out.columns:
        out = out.dropna(subset=["record_id"])
        out = out.drop_duplicates(subset=["record_id"], keep="first")

    return out


def load_input_frame() -> pd.DataFrame:
    if MERGED_PATH.is_file():
        return pd.read_csv(MERGED_PATH)

    import importlib.util

    build_path = ROOT / "scripts" / "build_dataset.py"
    spec = importlib.util.spec_from_file_location("build_dataset", build_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {build_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build()


def main() -> None:
    df = load_input_frame()
    cleaned = clean_dataframe(df)
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(DATASET_PATH, index=False)
    print(f"Wrote {len(cleaned)} cleaned rows to {DATASET_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
