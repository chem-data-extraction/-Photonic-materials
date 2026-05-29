# Processed data

This folder holds the **publication-ready** dataset: one row per record, columns aligned with `specs/dataset_schema.json`.

## Main file

- `dataset.csv` — final 42-row article-extraction dataset produced by `scripts/build_dataset.py` and `scripts/clean_dataset.py`, validated with `scripts/validate_project.py`

## Guidelines

- Regenerate this file from scripts; avoid hand-editing except for small metadata fixes during setup.
- The current processed dataset is version 0.1.0 and is summarized in `reports/final_report.md` and `dataset_card.md`.
