# Data files and cleaning audit

## Inputs used by the pipeline

`src/real_estate_analysis.py` reads these three files from `data/raw/`:

| File | Relevant input fields | Processing |
| --- | --- | --- |
| `mexico-real-estate-1.csv` | Property type, state, latitude, longitude, area, USD price | Parses numeric fields and standardizes text. |
| `mexico-real-estate-2.csv` | Property type, state, latitude, longitude, area, MXN price | Converts MXN price to USD using the configurable assumption described below. |
| `mexico-real-estate-3.csv` | Property type, place hierarchy, `lat-lon`, area, USD price | Extracts state from the place hierarchy and parses latitude and longitude. |

The pipeline uses these Mexico-named files only. It does not read other raw CSVs
that may be present in a local `data/raw/` directory.

WQU provides these course datasets, but the project does not independently
verify the original listing publishers, collection dates, or collection
methods. Filenames and column contents describe what the code expects, not
verified source attribution. Check the applicable terms before processing or
sharing raw or derived data.

## Getting data into the dashboard

The three Mexico CSVs listed above are the only source files required. Obtain
them from an authorized WQU course-data source or other authorized source; no
WQU-provided dataset files are bundled in this repository. Do not commit or
redistribute course materials. Confirm that using the files with a remote
Streamlit Community Cloud app is allowed before uploading them there.

On any dashboard page, use the **Dashboard data** sidebar controls to upload
one CSV into each matching source slot. The required columns are:

| File | Required columns |
| --- | --- |
| `mexico-real-estate-1.csv` | `property_type`, `state`, `lat`, `lon`, `area_m2`, `price_usd` |
| `mexico-real-estate-2.csv` | `property_type`, `state`, `lat`, `lon`, `area_m2`, `price_mxn` |
| `mexico-real-estate-3.csv` | `property_type`, `place_with_parent_names`, `lat-lon`, `area_m2`, `price_usd` |

The dashboard checks each CSV and then calls the existing cleaning pipeline to
build the analytical and geospatial dataframes in memory. Users do not upload
processed files: coordinates in the source files are parsed by the pipeline to
derive the geographic dataset. Uploaded files and resulting dataframes are kept
in the current Streamlit session and are not written to this repository or to
`data/processed/`. All data-dependent pages use that same session dataset.
When no source files have been uploaded, a local development copy may use the
processed files described below if they exist.

Missing files, unreadable CSVs, and missing required columns are reported in
the sidebar with instructions for correction. Rows with invalid core listing
values continue through the existing pipeline's coercion and filtering rules;
rows with invalid or missing coordinates remain in the analytical output when
otherwise valid, but are omitted from the geospatial output.

## Standardized outputs

The pipeline writes these files into `data/processed/`:

- `mexico-real-combined-clean.csv`: analytical records with
  `source_dataset`, `property_type`, `state`, `area_m2`, `price_usd`,
  `price_mxn`, `conversion_rate_mxn_per_usd`, and `price_per_m2`.
- `mexico-real-combined-geospatial.csv`: the same standardized fields plus
  `lat` and `lon`, limited to records with valid coordinate bounds.
- `cleaning_audit.json`: source-level row counts, duplicate diagnostics,
  potential cross-source matches, conversion assumption, and output counts.

These files are written only when the local command below is run. They are
optional for the interactive upload workflow and remain excluded from Git.

`price_per_m2` is calculated as `price_usd / area_m2`; it is not an independent
input field.

## Currency assumption

Dataset 2's USD price is calculated as:

```text
price_usd = price_mxn / mxn_rate
```

The default configurable value is `19.0` MXN per USD. The code and audit mark
this assumption as not historically verified. Changing `mxn_rate` changes
Dataset 2's USD price values; it does not affect the other two sources.

## Reference audit

The audit generated from the original local reference inputs reports:

| Input | Raw rows | Raw exact-duplicate rows | Repeated standardized keys removed within source | Analytical rows |
| --- | ---: | ---: | ---: | ---: |
| `mexico-real-estate-1.csv` | 700 | 0 | 2 | 698 |
| `mexico-real-estate-2.csv` | 700 | 2 | 9 | 691 |
| `mexico-real-estate-3.csv` | 700 | 3 | 7 | 693 |
| **Total** | **2,100** | **5** | **18** | **2,082** |

Raw exact-duplicate counts are diagnostics that overlap with the within-source
duplicate counts; they are not an additional five rows removed after the 18
standardized-key removals. The audit's core-validity check reports zero rows
with missing required values or nonpositive area/price.

Within each source, the analytical output drops duplicate rows across its
standardized analytical fields; the geospatial output includes coordinates in
its duplicate-row comparison. Separately, the audit field
`duplicate_standardized_keys_removed_within_source` counts repeated
`(property_type, state, area_m2, price_usd)` keys. Those counts match the
within-source analytical rows removed for the current inputs; the audit key is
not a cross-source deduplication rule.

The geospatial output contains **1,734** records. The geographic analysis
therefore describes a smaller sample than the 2,082-row analytical dataset.
Coordinates are checked against latitude bounds −90 to 90 and longitude bounds
−180 to 180.

The audit reports **14 potential standardized keys across 29 rows** that occur
in at least two source files. It does not remove these rows across sources:
without a unique listing identifier, a matching property type, state, area, and
price does not prove that records refer to the same physical property.

## Rebuild outputs

For optional local preprocessing, provide the three input files at the expected
paths and run from the repository root:

```powershell
python -m src.real_estate_analysis
```

The files under `data/raw/` and `data/processed/` are excluded by the root
`.gitignore` and are not tracked in the repository. A fresh clone can run the
dashboard by uploading authorized source CSVs; local preprocessing additionally
requires placing those files under `data/raw/`. Do not add WQU course datasets
or generated outputs to a public deployment repository.
