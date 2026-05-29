# Final report

## Project summary

Photonic materials for optical sensing. The repository now contains a schema-aligned CSV of article-derived sensor-performance records plus raw database snapshots for validation and metadata support.

Author: Базуев Роман Денисович.

## Dataset goal

The dataset supports comparison of quantitative optical-sensing performance across photonic crystals, photonic crystal fibers, MOF-based photonic crystals, plasmonic/photonic hybrids, and nanophotonic resonators. The intended audience is course participants and researchers practicing structured materials-data extraction.

## Source summary

The source map documents 21 source entries: 10 scientific articles, 3 supplementary/supporting-information entries, 5 external databases, and 3 bibliographic metadata aggregators. The processed dataset uses primary article records as authoritative values; reviews and databases support discovery, validation, comparison, and metadata normalization.

License overview: the processed dataset and project-authored files are released under CC-BY-4.0. Raw third-party article files, HTML snapshots, database exports, and metadata retain their upstream licenses and should be checked before redistribution.

After inspecting the final dataset fields, the three most relevant databases for validation and enrichment are:

| Database | Why it is relevant | Matching fields |
|----------|--------------------|-----------------|
| MOF-based SERS substrates dataset (Zenodo, DOI: `10.5281/zenodo.10580928`) | Closest external performance dataset for MOF/plasmonic sensing systems. It contains material/substrate descriptors, target analytes, measurement conditions, LOD, linear range, recovery, and source DOI. | `material_name`, `material_class`, `sensor_architecture`, `sensing_target`, `measurement_type`, `measurement_value`, `measurement_unit`, `doi` |
| OpticalMaterials.org refractive-index and dielectric-constant databases | Useful for checking optical-property plausibility of photonic and refractive-index sensing records. It provides downloadable refractive-index and dielectric-constant data with compound/material and DOI provenance. | `material_name`, `sensing_target`, `measurement_type`, `measurement_value`, `measurement_unit`, `doi` |
| RefractiveIndex.INFO optical constants database | Useful reference for optical constants of photonic layers, plasmonic metals, and sensing media. It supports checks of `n`, `k`, wavelength range, and source references. | `material_name`, `measurement_type`, `measurement_value`, `measurement_unit`, `source_url`, `notes` |

These databases have been downloaded to `data/raw/external/` and inventoried in `specs/database_download_manifest.json`. They should be treated as validation, comparison, and metadata-normalization layers. Primary experimental papers remain the authoritative source for the final sensor-performance values in `data/processed/dataset.csv`.

## Extraction summary

PDF extraction produced 22 records from 6 primary PDF articles. Web extraction produced 20 records from 4 article HTML/PMC pages, including 8 additional Nazeri et al. table values for HC-PCF sensor A/B spectral shifts and RI sensitivities. See Practice 3 and Practice 4 reports for extraction rules and mapping decisions.

An optional DeepSeek LLM helper was added as a candidate-discovery layer for PDF text. It uses `DEEPSEEK_API_KEY`, selects metric-heavy PDF snippets, requests schema-shaped JSON from DeepSeek, and writes review-only candidates to `data/extracted/llm_candidate_records.jsonl`. These candidates are not merged into the publication dataset automatically.

## Cleaning and normalization summary

`scripts/build_dataset.py` merged PDF and web records into 42 rows. `scripts/clean_dataset.py` aligned schema columns, normalized missing tokens and confidence labels, and deduplicated by `record_id`. Units are preserved as reported because the schema combines heterogeneous performance metrics.

The LLM candidate file is intentionally outside the merge list. This protects the final dataset from unreviewed model output while still allowing the project to use DeepSeek for discovery of values that may deserve later manual verification.

## Validation summary

`python scripts/validate_project.py` passed on `2026-05-29`. The original extraction and publication tests passed with 14 tests. The DeepSeek helper adds 4 offline tests for candidate-page selection, prompt construction, metric snippets, and record normalization; these tests do not require an API key.

## Limitations

Coverage is strongest for gas and refractive-index sensing. Biosensing coverage remains limited. Some values are theoretical and are marked in `notes`. External databases have heterogeneous licenses and should be checked before redistribution.

## Final artifacts

| Artifact | Path |
|----------|------|
| Processed dataset | `data/processed/dataset.csv` |
| Schema | `specs/dataset_schema.json` |
| Source map | `specs/source_map.json` |
| LLM extraction manifest | `specs/llm_extraction_manifest.json` |
| Dataset card | `dataset_card.md` |
| Citation | `CITATION.cff` |
| License | `LICENSE` |

The project status in `project.json` is `practice_05_completed`.
