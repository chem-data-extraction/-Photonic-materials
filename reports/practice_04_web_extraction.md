# Practice 4 - Web extraction

This practice continues the topic and schema defined in Practice 1, the source priorities from Practice 2, and the measurement rules used for PDF extraction in Practice 3. The web step extracts additional schema-aligned sensor-performance records from article HTML pages for the same photonic-material optical-sensing project.

The machine-readable plan is stored in `specs/web_extraction_manifest.json`. The extracted records are written to `data/extracted/web_extracted_records.csv`; raw HTML snapshots are stored under `data/raw/web/`.

## Selected web pages

| source_id | page_id | URL | Extracted records |
|-----------|---------|-----|-------------------|
| `paper_wang_2022_uio66_pc` | `rsc_wang_2022_uio66_pc_html` | `https://pubs.rsc.org/en/content/articlehtml/2022/ra/d2ra05494a` | 5 |
| `paper_nazeri_2020_hcpcf_mzi_gas` | `pmc_nazeri_2020_hcpcf_mzi_html` | `https://pmc.ncbi.nlm.nih.gov/articles/PMC7284782/` | 3 |
| `paper_shaban_2017_plasmonic_1d_pc` | `pmc_shaban_2017_plasmonic_1d_pc_html` | `https://pmc.ncbi.nlm.nih.gov/articles/PMC5296759/` | 2 |
| `paper_zaky_2020_tamm_1d_pc_gas` | `pmc_zaky_2020_tamm_1d_pc_html` | `https://pmc.ncbi.nlm.nih.gov/articles/PMC7297992/` | 2 |

These pages were selected because they are already documented in `specs/source_map.json`, match the project scope, provide open article HTML or a stable PMC full-text mirror, and contain scalar values that either complement the PDF extraction or expose table values more directly than the PDF text layer.

## Page structure

The pages are article HTML pages rather than database browse pages. RSC is used directly from the publisher. MDPI and Nature records use PMC full-text mirrors because the publisher pages can block simple script requests or return a client challenge instead of article text.

| Article page | Useful HTML content |
|--------------|---------------------|
| RSC article HTML | Article body, figure text, concentration-response discussion, sensitivity and LOD statements |
| PMC full-text HTML for MDPI article | Article body and embedded HTML tables, including gas spectral-shift values |
| PMC full-text HTML for Nature articles | Article body, equations, figure/table text, and sensitivity statements |

The extraction did not need pagination, login handling, JavaScript rendering, or iframe traversal. The script stores full HTML snapshots so the exact source text used for manual verification is retained locally.

## Extraction method

The executable extraction step is:

```bash
python scripts/extract_web.py
```

The script:

1. Reads `specs/web_extraction_manifest.json`.
2. Downloads each article HTML page to `data/raw/web/` with `urllib.request`.
3. Checks page-specific validation terms such as `0.06063`, `4629`, `48.56`, and `3100`.
4. Writes curated records from the manifest into the schema columns from `specs/dataset_schema.json`.
5. Appends one audit event per web page to `data/extracted/extraction_log.jsonl`.

Manual curation is used for the same reason as in Practice 3: the target values are short scalar metrics embedded in prose, captions, or compact tables, and the course schema needs a controlled mapping of one numeric metric to one record.

## Extracted records

The web extraction produced 12 schema-aligned records:

| Source | Number of records | Main extracted metrics |
|--------|-------------------|------------------------|
| Wang et al. 2022 UiO-66 3D PC | 5 | chlorobenzene concentration-series wavelength shifts at 80-400 ppm |
| Nazeri et al. 2020 HC-PCF MZI | 3 | helium, methane, and argon spectral shifts for sensor C |
| Shaban et al. 2017 Au/1D PC | 2 | separate SPR-resonance and left-PBG-edge RI sensitivity values |
| Zaky et al. 2020 Tamm-state 1D PC | 2 | theoretical intermediate sensitivity values before final optimization |

All rows use the Practice 1 schema:

`record_id`, `material_name`, `material_class`, `sensor_architecture`, `sensing_target`, `measurement_type`, `measurement_value`, `measurement_unit`, `source_id`, `source_url`, `doi`, `raw_file`, `extraction_confidence`, and `notes`.

## Mapping decisions

- The Wang et al. web records split the chlorobenzene concentration-response values into separate `wavelength_shift` rows for 80, 160, 240, 320, and 400 ppm. The 500 ppm value is already present in the PDF extraction, so it was not duplicated here.
- The Nazeri et al. web records use `wavelength_shift` with units of `pm` because Table 1 reports spectral shifts for pure gases. The methane value is negative and is kept as reported.
- The Shaban et al. records use `sensitivity` with units of `nm/RIU`; the specific resonance label is preserved in `notes`.
- The Zaky et al. records are retained because the source map includes simulation/theoretical sources, but `notes` explicitly mark the values as theoretical intermediate optimization results.
- No review article values were ingested directly. Reviews remain discovery and terminology sources as stated in Practice 2.

## Extraction problems

- Article HTML pages are less stable than PDFs: class names, table markup, and surrounding text can change. The local snapshots in `data/raw/web/` preserve the exact version used for this practice.
- Some values appear in figure discussion rather than table cells, so simple automatic selectors are not reliable enough for unattended extraction.
- Units are not normalized in this practice. The reported units are preserved (`nm`, `pm`, `nm/RIU`); unit harmonization remains part of Practice 5.
- Negative wavelength shifts are allowed when the source reports a directional spectral shift. This applies to the methane record from Nazeri et al.

## Output files

- `specs/web_extraction_manifest.json` - selected web pages, parser plan, validation terms, and curated records.
- `scripts/extract_web.py` - reproducible export script for the web manifest.
- `data/raw/web/*.html` - local article HTML snapshots.
- `data/extracted/web_extracted_records.csv` - 12 schema-aligned web records.
- `data/extracted/extraction_log.jsonl` - JSONL audit trail with web extraction events.

