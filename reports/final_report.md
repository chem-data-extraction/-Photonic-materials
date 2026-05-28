# Final report

> Summarize the completed project for instructors and future users. Update when you submit.

## Project summary

Template: Aptamer–protein binding dataset. Replace with your title, authors, and version.

## Dataset goal

What scientific question does the dataset support? Who is the intended audience?

## Source summary

Count of sources by group; key papers and databases; license overview.

The source map includes primary journal articles, supplementary materials, bibliographic aggregators, and external databases. After inspecting the final dataset fields, the three most relevant databases for validation and enrichment are:

| Database | Why it is relevant | Matching fields |
|----------|--------------------|-----------------|
| MOF-based SERS substrates dataset (Zenodo, DOI: `10.5281/zenodo.10580928`) | Closest external performance dataset for MOF/plasmonic sensing systems. It contains material/substrate descriptors, target analytes, measurement conditions, LOD, linear range, recovery, and source DOI. | `material_name`, `material_class`, `sensor_architecture`, `sensing_target`, `measurement_type`, `measurement_value`, `measurement_unit`, `doi` |
| OpticalMaterials.org refractive-index and dielectric-constant databases | Useful for checking optical-property plausibility of photonic and refractive-index sensing records. It provides downloadable refractive-index and dielectric-constant data with compound/material and DOI provenance. | `material_name`, `sensing_target`, `measurement_type`, `measurement_value`, `measurement_unit`, `doi` |
| RefractiveIndex.INFO optical constants database | Useful reference for optical constants of photonic layers, plasmonic metals, and sensing media. It supports checks of `n`, `k`, wavelength range, and source references. | `material_name`, `measurement_type`, `measurement_value`, `measurement_unit`, `source_url`, `notes` |

These databases should be treated as validation and comparison layers. Primary experimental papers remain the authoritative source for the final sensor-performance values in `data/processed/dataset.csv`.

## Extraction summary

PDF: methods, record count, main issues. Web: pages scraped, record count. Link to practice reports 3–4.

## Cleaning and normalization summary

Pipeline steps applied; deduplication outcome; unit normalization examples.

## Validation summary

Result of `scripts/validate_project.py` and `pytest`. Outstanding warnings.

## Limitations

Coverage gaps, uncertain extractions, license restrictions, conflicting values.

## Final artifacts

| Artifact | Path |
|----------|------|
| Processed dataset | `data/processed/dataset.csv` |
| Schema | `specs/dataset_schema.json` |
| Source map | `specs/source_map.json` |
| Dataset card | `dataset_card.md` |
| Citation | `CITATION.cff` |
| License | `LICENSE` |
