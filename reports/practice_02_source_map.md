# Practice 2 - Source map

## Source search strategy

The source map for this project is maintained in `specs/source_map.json` and is the machine-readable authority for source identifiers, access conditions, expected data types, and extraction priorities.

The search started from the already downloaded raw PDFs in `data/raw/pdf/`. For each PDF, I checked the title, DOI, abstract, first-page text, and available metadata. I then aligned the sources with the project scope: quantitative performance measurements for optical sensors based on photonic materials.

Search queries used for additional verification and snowballing:

| Search channel | Query pattern | Purpose |
|----------------|---------------|---------|
| Publisher and DOI pages | `"photonic crystal" "gas sensor" sensitivity`, `"MOF" "photonic crystal" "gas sensing"` | Verify primary sources and DOI landing pages |
| Photonic crystal fiber search | `"hollow-core photonic crystal fiber" "gas sensing"` | Find HC-PCF gas and refractive-index sensing papers |
| Hybrid sensor search | `"plasmonic/1D photonic crystal" sensing` | Find plasmonic/photonic hybrid sources |
| Review snowballing | Wang 2022 MOF PC review, Yu 2020 HC-PCF review, Dantl 2022 1D PC review | Identify additional primary sources and terminology |

## Source groups

### Scientific papers

The main group contains primary experimental or theoretical papers plus review articles used for snowballing.

| source_id | Role | Expected yield |
|-----------|------|----------------|
| `paper_wang_2022_uio66_pc` | Primary MOF-based 3D photonic crystal vapor sensor | Sensitivity, LOD, quality factor, selectivity, response/recovery metrics |
| `paper_nazeri_2020_hcpcf_mzi_gas` | Primary hollow-core photonic crystal fiber gas sensor | RI sensitivity, pure-gas measurements, response/recovery behavior |
| `paper_dolci_2025_fiber_tip_pc_biosensing` | Primary fiber-tip photonic crystal biosensor | Biosensing response and detection metrics in serum |
| `paper_shaban_2017_plasmonic_1d_pc` | Primary plasmonic/1D photonic crystal sensor | RI response, wavelength shifts, glucose and chemical sensing |
| `paper_zaky_2020_tamm_1d_pc_gas` | Theoretical 1D photonic crystal gas sensor | Simulated sensitivity and detection-limit values |
| `paper_lin_2018_seira_on_chip_gas` | Primary SEIRA on-chip gas sensor | Gas-sensing performance and enhancement metrics |
| `review_wang_2022_mof_pc_gas` | Review/snowballing | MOF-photonic crystal terminology and candidate sources |
| `review_yu_2020_hcpcf_gas` | Review/snowballing | HC-PCF gas-sensing terminology and candidate sources |
| `review_dantl_2022_1d_pc_sensors` | Review/snowballing | 1D photonic crystal stimuli-response mechanisms |
| `review_chiappini_2020_chromatic_pc` | Review/snowballing | Chromatic sensor examples and references |

### Supplementary materials

Supplementary information is included only when it can clarify fabrication, measurement setup, concentration ranges, or values that are not fully tabulated in the main article. The selected supplementary entries are linked to the UiO-66, plasmonic/1D photonic crystal, and SEIRA sources.

### Databases

Databases are used in two roles: (1) external comparison sources with overlapping sensor/material fields, and (2) metadata support sources for analyte and article normalization. The three best database matches found after inspecting the final dataset are listed first.

| source_id | Database | Main overlap with this dataset | Use |
|-----------|----------|--------------------------------|-----|
| `db_mof_sers_zenodo` | MOF-based SERS substrates dataset, Zenodo | MOF/substrate, plasmonic metal, analyte, analyte phase, LOD, linear range, DOI | Best external comparison source for MOF/plasmonic sensing records; use for validation, not automatic replacement |
| `db_opticalmaterials` | OpticalMaterials.org refractive-index and dielectric-constant databases | Material/compound, optical property type, refractive index, dielectric constant, wavelength, DOI | Check optical-property plausibility and add context for refractive-index-sensitive records |
| `db_refractiveindex_info` | RefractiveIndex.INFO optical constants database | Material name, refractive index `n`, extinction coefficient `k`, wavelength range, source reference | Validate optical constants for photonic layers, plasmonic metals, and sensing media |
| `db_pubchem_analytes` | PubChem compound records | Analyte names, synonyms, formulae, identifiers | Standardize chemical names for gas, vapor, solvent, and biomolecular targets |
| `db_pmc_open_access` | PubMed Central open-access full text | DOI, article text, figures, supplementary links | Cross-check open-access full text and article-specific licenses |

The MOF-based SERS dataset is the closest field-level match because it combines `material/substrate`, `sensing_target`, `measurement_type`-like performance values, and DOI provenance. OpticalMaterials.org and RefractiveIndex.INFO do not report sensor performance, but they are useful for validating optical context, especially records expressed in `nm/RIU`, `RIU`, and wavelength-shift units.

## Downloaded database artifacts

The database sources listed above were downloaded to `data/raw/external/` on `2026-05-28`. The reproducible file inventory, URLs, byte counts, and SHA-256 checksums are stored in `specs/database_download_manifest.json`.

| source_id | Local raw artifact(s) | Role in this project |
|-----------|------------------------|----------------------|
| `db_mof_sers_zenodo` | `db_mof_sers_zenodo_dataset.csv`, `db_mof_sers_zenodo_dataset.xlsx`, README and pore-diameter workbook | External comparison source for MOF/plasmonic sensing performance fields |
| `db_opticalmaterials` | `db_opticalmaterials_scidata_database.csv`, `db_opticalmaterials_master.zip` | Optical-property plausibility checks |
| `db_refractiveindex_info` | `db_refractiveindex_info_database_main.zip` | Material optical-constant reference |
| `db_pubchem_analytes` | `db_pubchem_analytes_compounds.json` | Analyte-name and formula normalization |
| `db_pmc_open_access` | `db_pmc_open_access_idconv.json`, three PMC OAI XML records | Open-access full-text cross-checks for article extraction |

These external files are kept as raw database snapshots. The processed CSV remains based on primary article extraction; database values are reserved for validation, comparison, and metadata normalization unless a later practice explicitly defines a separate database-ingestion table.

### Aggregators

Aggregators are used for bibliographic validation and snowballing only:

| source_id | Use |
|-----------|-----|
| `agg_crossref_metadata` | DOI, title, author, publication-date validation |
| `agg_openalex_metadata` | Reference snowballing and open-access status checks |
| `agg_semantic_scholar_metadata` | Citation and related-paper discovery |

### GitHub repositories and ML datasets

No GitHub repository or ML dataset was selected for direct ingestion in this practice. Search results in this topic were either unrelated to experimentally reported sensor metrics, did not provide clear provenance, or did not have a suitable redistribution license. These groups remain as empty arrays in `source_map.json`.

## Priority sources

Extraction should start with primary sources that are open access, contain directly reported quantitative metrics, and cover distinct sensor classes:

1. `paper_wang_2022_uio66_pc` - strong first source because the abstract and article text report multiple metrics for a MOF-based 3D photonic crystal vapor sensor.
2. `paper_nazeri_2020_hcpcf_mzi_gas` - clear HC-PCF gas-sensing source with an explicit RI sensitivity and response/recovery information.
3. `paper_dolci_2025_fiber_tip_pc_biosensing` - recent biosensing source that broadens the dataset beyond gas sensing.
4. `paper_shaban_2017_plasmonic_1d_pc` - covers plasmonic/photonic hybrid sensing and glucose/chemical examples.
5. `paper_lin_2018_seira_on_chip_gas` - useful on-chip gas-sensing source, but reuse terms must be checked carefully.

Reviews are lower priority for extraction because they may repeat values from primary papers. Their main role is source discovery and vocabulary normalization.

## Access conditions

Most selected primary sources are open-access publisher articles or open institutional/publisher PDFs. ACS material is marked separately because reuse may be governed by publisher terms. Supplementary files must be checked individually before derived data are redistributed.

Required fields in the source map:

- `access_status` records whether the source is open access, publisher terms, or metadata-only.
- `access_method` records how the source should be accessed.
- `access_date` is set to `2026-05-26` for the current source audit.
- `license` records the known or expected reuse condition; uncertain entries explicitly say that reuse terms must be verified.

No API key is required for PubChem, Crossref, or OpenAlex for the planned metadata checks. Semantic Scholar may require rate-limit handling if used at scale.

## Expected data types

Expected data types include:

- publisher HTML with article text and references;
- PDF text for abstracts, methods, captions, and performance sections;
- tables when available;
- figures requiring manual reading or later digitization;
- supplementary PDFs or supporting information;
- metadata-only API responses from Crossref, OpenAlex, Semantic Scholar, PubChem, or PMC.

The target dataset fields are mainly `material_name`, `material_formula`, `material_class`, `sensor_architecture`, `fabrication_method`, `sensing_target`, `sensing_medium`, `measurement_type`, `measurement_value`, `measurement_unit`, `operating_wavelength_nm`, `wavelength_shift_nm`, `refractive_index_range`, `concentration_range`, `temperature_c`, and source-provenance fields.

## Expected conflicts and overlaps

Conflict resolution rules:

- Primary experimental articles override reviews and aggregators.
- Supplementary tables override plotted values when both describe the same measurement.
- If an abstract, table, and figure report different values, keep the table value and record the discrepancy in `notes`.
- Simulation-only values are allowed only when `notes` clearly marks them as theoretical.
- If one source reports a range and another reports a single derived value, keep the reported value in its original unit and document the derivation status.
- Duplicate values found through reviews are traced back to the primary source before extraction.

## Coverage gaps

Current coverage is strongest for gas and refractive-index sensing. Gaps remain for:

- negative or low-performance examples;
- commercial sensor comparisons;
- humidity, temperature, and long-term stability metrics;
- biosensing beyond the fiber-tip serum example;
- open ML-ready datasets with clear experimental provenance and redistribution rights.

These gaps should be addressed during later extraction practices by snowballing from the four selected reviews and adding more primary sources only when they provide extractable quantitative records.
