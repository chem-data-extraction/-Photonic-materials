# Practice 5 — Cleaning, normalization and publication

> Follow `specs/cleaning_pipeline.json`. Run `scripts/clean_dataset.py` and `scripts/validate_project.py`.

## Input files

- `data/extracted/pdf_extracted_records.csv`
- `data/extracted/web_extracted_records.csv`
- `data/raw/external/*` database snapshots documented in `specs/database_download_manifest.json` for validation and metadata support
- (optional) `data/interim/merged_records.csv`
- (optional, review-only) `data/extracted/llm_candidate_records.jsonl`

## Cleaning steps

Walk through each step in `specs/cleaning_pipeline.json`: merge, unit preservation, text cleanup, missing values, deduplication, validation, export.

## Normalization rules

The final schema preserves article-reported units (`nm`, `pm`, `nm/RIU`, `ppm`, `pM`, `s`, `RIU`, and `dimensionless`) rather than converting across incompatible sensor-performance metrics. Missing-value tokens are normalized by `scripts/clean_dataset.py`; no sequence fields are present in the photonic-materials schema.

## Deduplication strategy

Rows are deduplicated by stable `record_id`. The merge step keeps the first occurrence when the same record appears in multiple extraction outputs.

LLM candidate records are excluded from the automatic merge. `scripts/build_dataset.py` reads only the PDF and web CSV files, so `data/extracted/llm_candidate_records.jsonl` cannot change `data/processed/dataset.csv` unless reviewed candidates are intentionally copied into a schema-aligned extraction CSV.

## Validation results

`python scripts/validate_project.py` passed on `2026-05-29`. The original publication test suite passed with 14 tests. After adding the DeepSeek helper, `tests/test_llm_candidate_extraction.py` adds 4 offline tests for prompt construction and candidate normalization without calling the API.

## Final dataset description

The final dataset contains 42 article-derived sensor-performance records and is stored at `data/processed/dataset.csv`.

The project publication metadata was also completed: `project.json` now marks the project as `practice_05_completed`, `LICENSE` selects CC-BY-4.0 for project-authored materials, `CITATION.cff` describes the photonic-materials dataset, and the final report and dataset card summarize source coverage, limitations, license boundaries, and citation information.

## Publication readiness checklist

- [x] `dataset.csv` matches `specs/dataset_schema.json`
- [x] All `source_id` values documented in source map
- [x] Optional DeepSeek candidates are documented as review-only and excluded from automatic publication
- [x] LICENSE finalized
- [x] `CITATION.cff` completed
- [x] `dataset_card.md` updated
- [x] `reports/final_report.md` complete
