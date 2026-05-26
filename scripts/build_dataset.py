#!/usr/bin/env python3
"""Merge schema-aligned extracted CSVs and write interim/processed datasets."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

EXTRACTED_CSVS = [
    ROOT / "data/extracted/pdf_extracted_records.csv",
    ROOT / "data/extracted/web_extracted_records.csv",
]
SCHEMA_PATH = ROOT / "specs/dataset_schema.json"
MERGED_PATH = ROOT / "data/interim/merged_records.csv"
DATASET_PATH = ROOT / "data/processed/dataset.csv"


def load_schema_columns() -> list[str]:
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    return [field["name"] for field in schema["fields"]]


def load_schema_aligned_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame(columns=columns)

    df = pd.read_csv(path)
    missing = [column for column in columns if column not in df.columns]
    if missing:
        print(f"Skipping {path.relative_to(ROOT)}: missing schema columns {missing}")
        return pd.DataFrame(columns=columns)

    return df[columns]


def build() -> pd.DataFrame:
    columns = load_schema_columns()
    frames = [load_schema_aligned_csv(path, columns) for path in EXTRACTED_CSVS]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return pd.DataFrame(columns=columns)

    merged = pd.concat(frames, ignore_index=True)
    return merged.drop_duplicates(subset=["record_id"], keep="first")


def main() -> None:
    MERGED_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = build()
    df.to_csv(MERGED_PATH, index=False)
    df.to_csv(DATASET_PATH, index=False)

    print(f"Wrote {len(df)} rows to {MERGED_PATH.relative_to(ROOT)}")
    print(f"Wrote {len(df)} rows to {DATASET_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
