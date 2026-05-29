# Dataset Card - Photonic Materials For Optical Sensing

## Dataset Title

Photonic materials for optical sensing

## Dataset Summary

This dataset contains article-derived quantitative performance measurements for optical sensors based on photonic materials, including photonic crystals, hollow-core photonic crystal fibers, MOF-based photonic crystals, plasmonic/photonic hybrids, and nanophotonic resonators.

## Scientific Task

Support comparison of reported sensor-performance metrics such as sensitivity, limit of detection, wavelength shift, response time, recovery time, quality factor, and resolution across photonic-material sensing platforms.

## Record Unit

One row = one reported quantitative sensor-performance measurement for one material/device architecture, one sensing target, and one source.

## Data Sources

Primary records come from journal articles documented in `specs/source_map.json`. External database snapshots from Zenodo, OpticalMaterials.org, RefractiveIndex.INFO, PubChem, and PMC are stored in `data/raw/external/` and inventoried in `specs/database_download_manifest.json`; they support validation, comparison, and metadata normalization rather than replacing primary article values.

## Data Extraction Procedure

1. PDF extraction: `scripts/extract_pdf.py` guided by `specs/pdf_extraction_manifest.json`
2. Web extraction: `scripts/extract_web.py` guided by `specs/web_extraction_manifest.json`
3. Database downloads: raw snapshots documented by `specs/database_download_manifest.json`
4. Logs: `data/extracted/extraction_log.jsonl`

## Data Cleaning And Normalization

`scripts/build_dataset.py` merges extracted article records into `data/interim/merged_records.csv`; `scripts/clean_dataset.py` aligns columns, normalizes missing values and confidence labels, deduplicates by `record_id`, and writes `data/processed/dataset.csv`.

## Dataset Schema

Field definitions and examples are in `specs/dataset_schema.json`. The final CSV contains 42 rows and uses these columns exactly.

## Validation

Validation rules are in `specs/validation_rules.json`. On `2026-05-28`, `python scripts/validate_project.py` passed and `pytest -q` passed with 14 tests.

## Known Limitations

- Units are preserved as reported and are not converted across different metric types.
- Some records are theoretical simulations and are marked in `notes`.
- External databases are downloaded as raw references; their values are not automatically mixed into the processed article-extraction dataset.
- License terms differ by upstream source and should be checked before redistribution.

## Recommended Use

Teaching structured scientific data extraction; comparing reported photonic-sensor metrics; prototyping cleaning and validation workflows for materials-informatics datasets.

## Not Recommended Use

Clinical or safety-critical decision-making; direct meta-analysis without rechecking primary articles and source licenses.

## License

Processed records and project-authored materials are released under CC-BY-4.0.
Raw third-party source files and database snapshots retain their upstream
licenses and terms; see `specs/source_map.json` and
`specs/database_download_manifest.json`.

## Citation

Use the metadata in `CITATION.cff`: Roma (2026), *Photonic materials for optical
sensing*, version 0.1.0.
