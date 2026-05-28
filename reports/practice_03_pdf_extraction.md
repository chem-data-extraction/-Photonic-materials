# Practice 3 - PDF extraction

This practice implements automatic PDF extraction for the topic defined in Practice 1 and the source priorities defined in Practice 2: quantitative performance data for optical sensors based on photonic materials.

The machine-readable plan is stored in `specs/pdf_extraction_manifest.json`. The extraction script scans every local PDF listed in `specs/source_map.json`, writes extracted records to `data/extracted/pdf_extracted_records.csv`, and logs both extracted and skipped PDFs in `data/extracted/extraction_log.jsonl`.

## Automatic pipeline

```text
data/raw/pdf/*.pdf
  -> PyMuPDF text extraction
  -> text normalization
  -> source-specific regex rules
  -> schema-aligned PDF CSV
  -> build_dataset.py
  -> clean_dataset.py
  -> validate_project.py and pytest
```

The script used for extraction is:

```bash
python scripts/extract_pdf.py
```

It performs the following steps automatically:

1. Reads `specs/source_map.json`.
2. Finds every local PDF with a `raw_file` path.
3. Opens each PDF with PyMuPDF.
4. Normalizes extracted text: whitespace, ligatures, dash variants, multiplication signs, and scientific notation variants.
5. Applies source-specific regex rules to primary sources.
6. Writes rows using the exact schema from `specs/dataset_schema.json`.
7. Logs every scanned PDF, including review PDFs skipped because they are not primary extraction sources.

## PDFs scanned

All 10 local PDFs in `data/raw/pdf/` are scanned.

| Status | PDF group | Count | Reason |
|--------|-----------|-------|--------|
| Extracted | Primary sources with automatic rules | 6 | Direct scalar performance metrics are available in PDF text |
| Skipped | Review articles | 4 | Practice 2 defines reviews as snowballing and terminology sources, not direct measurement sources |

## Automatic extraction rules

| source_id | Pages targeted | Automatically extracted metrics |
|-----------|----------------|---------------------------------|
| `paper_wang_2022_uio66_pc` | 6 | sensitivity, limit_of_detection, quality_factor, response_time, recovery_time, wavelength_shift |
| `paper_nazeri_2020_hcpcf_mzi_gas` | 9, 10, 11 | sensitivity, resolution, response_time, recovery_time |
| `paper_dolci_2025_fiber_tip_pc_biosensing` | 5, 6 | sensitivity, limit_of_detection |
| `paper_shaban_2017_plasmonic_1d_pc` | 6, 8 | sensitivity |
| `paper_zaky_2020_tamm_1d_pc_gas` | 1, 8 | sensitivity, limit_of_detection, quality_factor |
| `paper_lin_2018_seira_on_chip_gas` | 7 | limit_of_detection, quality_factor |

The rules are source-specific because each article reports values differently: some values are in prose, some in table text, and some in figure-discussion paragraphs.

## Extracted records

The automatic PDF extraction produced 22 records:

| Source | Number of records | Main extracted metrics |
|--------|-------------------|------------------------|
| Wang et al. 2022 UiO-66 3D PC | 6 | sensitivity, LOD, Q factor, response time, recovery time, wavelength shift |
| Nazeri et al. 2020 HC-PCF MZI | 4 | RI sensitivity, resolution, methane response time, methane recovery time |
| Dolci et al. 2025 fiber-tip PC | 2 | bulk RI sensitivity, anti-IgG LOD in undiluted serum |
| Shaban et al. 2017 Au/1D PC | 5 | RI sensitivity, glucose sensitivity, PBG-width slope |
| Zaky et al. 2020 Tamm-state 1D PC | 3 | theoretical sensitivity, theoretical LOD, theoretical Q factor |
| Chong et al. 2018 SEIRA gas sensor | 2 | CO2 LOD, measured Q factor |

## Examples

Example automatic match from Wang et al. 2022:

```text
source text pattern -> "LOD ... was 1.64 ppm"
dataset row        -> limit_of_detection = 1.64 ppm
```

Example automatic match from Nazeri et al. 2020:

```text
source text pattern -> "highest sensitivity was achieved by sensor C: 4629 (nm/RIU)"
dataset row        -> sensitivity = 4629 nm/RIU
```

Example automatic match from Zaky et al. 2020:

```text
source text pattern -> "S = 1.9 x 10 5 nm/RIU"
dataset row        -> sensitivity = 190000 nm/RIU
```

## Mapping decisions

- Each row still represents one quantitative performance metric for one sensor architecture, one sensing target, and one source.
- Review PDFs are scanned but skipped for direct records, following the source-map rule that reviews are used for snowballing and vocabulary checks.
- Source-specific regex rules are used instead of one generic regex because the same metric is phrased differently across articles.
- For Zaky et al. 2020, records are retained but notes explicitly mark the sensor as theoretical.
- For Shaban et al. 2017, the PBG-width glucose slope is stored as `sensitivity` because the schema does not have a separate PBG-width-slope metric.

## Tests

Automatic extraction is covered by `tests/test_pdf_extraction.py`.

The tests check that:

- every local PDF is discovered;
- all PDFs are scanned;
- 6 PDFs produce records and 4 are logged as skipped;
- 22 records are extracted;
- key numeric values are extracted correctly from PDF text;
- extracted rows match `specs/dataset_schema.json`.

## Output files

- `specs/pdf_extraction_manifest.json` - automatic extraction plan and rule inventory.
- `scripts/extract_pdf.py` - automatic PyMuPDF and regex extraction script.
- `data/extracted/pdf_extracted_records.csv` - schema-aligned PDF records.
- `data/extracted/extraction_log.jsonl` - JSONL audit trail for all scanned PDFs.
- `data/interim/merged_records.csv` - merged table after `scripts/build_dataset.py`.
- `data/processed/dataset.csv` - cleaned dataset after `scripts/clean_dataset.py`.
