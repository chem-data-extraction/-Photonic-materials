# Practice 1 — Record Definition and Dataset Schema

## Topic

Photonic materials for optical sensing.

## Scientific Task

Collect structured, quantitative performance data for optical sensors based on photonic materials. The dataset will cover photonic crystals, plasmonic/photonic hybrid structures, photonic crystal fibers, MOF-based photonic crystals, and related nanophotonic sensing platforms used for gas, chemical, refractive-index, and biosensing.

The practical goal is to make reported sensor performance comparable across papers: material, architecture, analyte, metric type, metric value, unit, and source provenance.

## One-Record Definition

**One record** = one reported quantitative sensor-performance measurement for a specific photonic material or device architecture, analyte or sensing target, and source under stated experimental or simulation conditions.

This means that one paper can contribute multiple records. For example, the same UiO-66 photonic crystal sensor may have separate records for sensitivity, limit_of_detection, response_time, recovery_time, wavelength_shift, quality_factor, resolution, and detection_range.

## LLM-assisted candidate records

The schema is also used by the optional DeepSeek helper added after the main extraction pipeline. Its output is deliberately called a candidate record, not a final dataset record. A candidate becomes a final record only after a human reviewer checks the source evidence, confirms the page or section, verifies the value and unit, and copies the schema-aligned row into a curated CSV or manifest.

This keeps the Practice 1 definition stable: the LLM can suggest rows in the same shape as `specs/dataset_schema.json`, but it cannot relax the requirement that every final record must be supported by a specific source text fragment.

## Examples of Records

Literal example row from `data/processed/dataset.csv`:

```csv
record_id,material_name,material_class,sensor_architecture,sensing_target,measurement_type,measurement_value,measurement_unit,source_id,source_url,doi,raw_file,extraction_confidence,notes
rec_wang_2022_uio66_lod_001,UiO-66 3D photonic crystal,MOF-based photonic crystal,3D photonic crystal vapor sensor,chlorobenzene vapor,limit_of_detection,1.64,ppm,paper_wang_2022_uio66_pc,https://doi.org/10.1039/D2RA05494A,10.1039/D2RA05494A,data/raw/pdf/rsc_2022_uio66_3d_photonic_crystal_optical_sensor.pdf,high,"Example row for Practice 1; concentration range 0-500 ppm; value verified from article abstract/conclusion."
```

This row counts as a record because it contains one numeric sensing-performance metric (`limit_of_detection = 1.64 ppm`) for one material, one sensor architecture, one sensing target, and one source.

## Non-Record Examples

| Example | Why it is not a record |
|---------|-------------------------|
| A general review statement that photonic crystals are promising for sensing | No specific material-analyte-metric-value tuple |
| A schematic drawing of a photonic crystal sensor without measured or simulated performance | No quantitative measurement |
| A material synthesis paragraph without optical sensing data | Describes fabrication only, not sensor performance |
| A repeated value copied from another source without clear provenance | Duplicate or secondary citation; primary source should be preferred |

## Dataset Fields

The machine-readable schema is stored in `specs/dataset_schema.json`. The final dataset must use exactly these columns, in this order:

| Field | Purpose |
|-------|---------|
| `record_id` | Stable unique identifier for one measurement record |
| `material_name` | Name of the active photonic material or sensing structure |
| `material_class` | Broad class such as 1D photonic crystal, 3D photonic crystal, photonic crystal fiber, MOF-based photonic crystal, or plasmonic/photonic hybrid |
| `sensor_architecture` | Device geometry or sensing platform |
| `sensing_target` | Analyte or physical property being detected |
| `measurement_type` | Controlled metric name: sensitivity, limit_of_detection, wavelength_shift, response_time, recovery_time, quality_factor, resolution, or detection_range |
| `measurement_value` | Numeric value of the metric |
| `measurement_unit` | Unit corresponding to `measurement_value` |
| `source_id` | Link to `specs/source_map.json` |
| `source_url` | DOI landing page or source URL |
| `doi` | DOI when available |
| `raw_file` | Local path to downloaded raw PDF/snapshot |
| `extraction_confidence` | high, medium, low, unknown, or empty |
| `notes` | Caveats, extraction details, operating wavelength, measurement medium, fabrication method, temperature, or other details that are not common enough for separate columns |

## Ambiguous Cases and Decisions

- If one article reports multiple metrics for the same sensor, store each metric as a separate record.
- `measurement_type` must use only one of the controlled values: `sensitivity`, `limit_of_detection`, `wavelength_shift`, `response_time`, `recovery_time`, `quality_factor`, `resolution`, `detection_range`.
- If a metric is reported for several analyte concentrations, store the summary metric as one record and keep the interval in `notes`. If every concentration has a separate numeric response, split it into separate records during extraction.
- If both experimental and simulation data are reported, prioritize experimental values. Simulation-only values can be included only when `notes` clearly states that they are simulated.
- If the same performance value appears in a review and in the original paper, use the original paper as the primary source. Reviews are useful for finding sources and cross-checking values.
- If the paper gives a range instead of one number, keep `measurement_value` empty until a defensible extraction rule is defined, and put the original range in `notes`.
- If units differ across papers, keep the reported unit in `measurement_unit`. Unit normalization rules will be finalized in Practice 5.
- If operating wavelength, sensing medium, concentration range, temperature, or fabrication details are important for a record, write them in `notes` instead of adding sparse columns.
- If operating wavelength is not explicitly reported, do not infer it from figures without documentation.
- If a value is suggested by the DeepSeek candidate extractor, treat it as `needs_review=true` until evidence text, page number, measurement type, numeric value, and unit are checked against the original source.

## Initial Raw Sources Downloaded

Open-access PDFs have been saved under `data/raw/pdf/` for later source mapping and extraction. The downloaded set includes photonic crystal, photonic crystal fiber, MOF-photonic crystal, plasmonic/photonic, and nanophotonic gas/bio/chemical sensing examples. These PDFs are raw source files only; numeric extraction will be documented in later practices.
