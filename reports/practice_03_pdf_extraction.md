# Practice 3 - PDF extraction

This practice implements the PDF extraction step for the topic defined in Practice 1 and the source priorities defined in Practice 2: quantitative performance data for optical sensors based on photonic materials.

The machine-readable plan is stored in `specs/pdf_extraction_manifest.json`. The extracted records are written to `data/extracted/pdf_extracted_records.csv` and then merged into `data/processed/dataset.csv`.

## Selected PDF sources

| source_id | pdf_id | Source role | Pages used |
|-----------|--------|-------------|------------|
| `paper_wang_2022_uio66_pc` | `rsc_2022_uio66_3d_photonic_crystal_optical_sensor` | Primary MOF-based 3D photonic crystal chlorobenzene sensor | 1, 5, 6, 7, 8 |
| `paper_nazeri_2020_hcpcf_mzi_gas` | `nazeri_2020_hollow_core_pcf_mzi_gas_sensing` | Primary hollow-core photonic crystal fiber MZI gas sensor | 1, 9, 10, 11, 12 |
| `paper_dolci_2025_fiber_tip_pc_biosensing` | `fernandez_regules_2024_fiber_tip_photonic_crystal_biosensing` | Primary fiber-tip photonic crystal biosensor | 2, 3, 5, 6, 7 |
| `paper_shaban_2017_plasmonic_1d_pc` | `shaban_2017_plasmonic_1d_photonic_crystal` | Primary plasmonic/1D photonic crystal RI and glucose sensor | 1, 6, 7, 8 |
| `paper_zaky_2020_tamm_1d_pc_gas` | `zaky_2020_tamm_1d_photonic_crystal_gas_sensor` | Theoretical 1D photonic crystal Tamm-state gas sensor | 1, 6, 7, 8 |
| `paper_lin_2018_seira_on_chip_gas` | `lin_2018_surface_enhanced_infrared_on_chip_gas_sensing` | On-chip SEIRA plasmonic/MOF gas sensor | 6, 7 |

These PDFs were selected because they match the dataset scope, are already present in `data/raw/pdf/`, and contain directly reported scalar metrics that can be represented by the schema from Practice 1.

## Extraction method

PDF text layers were inspected with PyMuPDF text extraction to locate candidate pages and terms such as `sensitivity`, `limit of detection`, `response time`, `recovery time`, `quality factor`, `resolution`, `nm/RIU`, `ppm`, and `pM`.

The final numeric values were transcribed manually into `specs/pdf_extraction_manifest.json` because the target data are scalar values embedded in prose, figure captions, and compact tables. This is more reliable for this practice than automatic table extraction with Camelot or Tabula, especially for merged cells, wrapped table headings, and chemical notation.

The executable extraction step is:

```bash
python scripts/extract_pdf.py
```

The script reads curated records from the manifest, checks that each referenced PDF exists, validates unique `record_id` values, writes the schema-aligned CSV, and appends source-level events to `data/extracted/extraction_log.jsonl`.

## Extracted records

The PDF extraction produced 22 records:

| Source | Number of records | Main extracted metrics |
|--------|-------------------|------------------------|
| Wang et al. 2022 UiO-66 3D PC | 6 | sensitivity, LOD, Q factor, response time, recovery time, wavelength shift |
| Nazeri et al. 2020 HC-PCF MZI | 4 | RI sensitivity, resolution, methane response time, methane recovery time |
| Dolci et al. 2025 fiber-tip PC | 2 | bulk RI sensitivity, anti-IgG LOD in undiluted serum |
| Shaban et al. 2017 Au/1D PC | 5 | RI sensitivity, glucose sensitivity, PBG-width slope |
| Zaky et al. 2020 Tamm-state 1D PC | 3 | theoretical sensitivity, theoretical LOD, theoretical Q factor |
| Chong et al. 2018 SEIRA gas sensor | 2 | CO2 LOD, measured Q factor |

All output rows use the schema fields from `specs/dataset_schema.json`: `record_id`, material fields, sensor architecture, sensing target, controlled `measurement_type`, numeric `measurement_value`, unit, source provenance, extraction confidence, and notes.

## Mapping decisions

- Each row represents one quantitative performance metric for one sensor architecture, one target, and one source.
- Reported concentration or RI ranges are kept in `notes` rather than split into sparse columns.
- For Wang et al. 2022, the chlorobenzene slope is stored as `sensitivity = 0.06 nm/ppm`; the more precise fitted slope `0.06063` is preserved in notes.
- For Zaky et al. 2020, records are retained because the source is in the Practice 2 source map, but notes explicitly mark them as theoretical.
- For Shaban et al. 2017, the PBG-width glucose slope is stored as a `sensitivity` record because the project schema does not have a separate PBG-width-slope metric.
- For Lin/Chong et al. 2018, only scalar metrics visible in the local PDF are extracted; the source map warning about ACS publisher terms is preserved in notes.

## Extraction problems

- Some PDFs use ligatures and symbol encodings that appear imperfectly in raw text extraction, so final values were verified manually rather than parsed by regular expression alone.
- Several useful values are embedded in figure captions or prose instead of machine-readable tables.
- Units are not fully normalized in this practice. The reported units are kept as written, for example `nm/RIU`, `nm/ppm`, `pM`, `ppm`, and `dimensionless`.
- Review PDFs were not used for direct records because Practice 2 established that reviews should support snowballing and terminology checks, while primary sources should supply measurement values.

## Output files

- `specs/pdf_extraction_manifest.json` - selected PDFs, page numbers, methods, and curated records.
- `scripts/extract_pdf.py` - reproducible export script for the manifest records.
- `data/extracted/pdf_extracted_records.csv` - 22 schema-aligned PDF records.
- `data/interim/merged_records.csv` - merged table after `scripts/build_dataset.py`.
- `data/processed/dataset.csv` - cleaned dataset after `scripts/clean_dataset.py`.
- `data/extracted/extraction_log.jsonl` - JSONL audit trail for PDF extraction events.
