# Mexico Real Estate Insights

An observational data analysis project and Streamlit dashboard for exploring
Mexican real-estate listings, property area, listing prices, and the geographic
coverage represented by the available records. This is an analysis project, not
a property marketplace.

## Research question

> Are property prices in the Mexican real estate dataset more strongly
> associated with property size or geographical location?

The analysis compares property area and broad state categories using the
available listing data. It does not estimate causal effects, and state is only
a coarse proxy for location.

## Project objectives

- Standardize the three Mexican real-estate source files through the existing
  cleaning pipeline.
- Describe the distribution of listing prices, property sizes, property types,
  and states.
- Explore how total listing price is associated with property area.
- Compare model-based explanatory power when area, state, and property type
  terms are included.
- Disclose assumptions, data coverage, and limits on interpretation.

## Verified findings

The figures below were reproduced from the current processed analytical
dataset using the project's analysis functions:

- The area-price sample contains **2,082 listings**. Pearson correlation is
  **0.5935** and Spearman correlation is **0.6117**.
- The fitted model
  `log(price_usd) ~ area_m2 + C(state) + C(property_type)` has **R² = 0.5203**
  and **adjusted R² = 0.5131** on 2,082 complete observations.
- The area coefficient is **0.005483 log-price units per m²**, with HC3 robust
  standard error **0.000122** and 95% confidence interval
  **[0.005243, 0.005723]**. Its log-linear transformation is about **0.550%**
  higher fitted listing price per additional m², conditional on the included
  model terms.

| Same-sample specification | R² |
| --- | ---: |
| State only | 0.0632 |
| Area + state | 0.4757 |
| Area + state + property type | 0.5203 |
| State + property type | 0.0641 |

Adding area to the state-only specification increases R² by **0.4125**;
adding property type to the area + state specification increases R² by
**0.0446**. These are in-sample comparisons for this dataset and specification.
They do not show that area causes prices to change or that state captures all
relevant location differences.

## Dashboard screenshots

No screenshots are currently included. If screenshots are added, place reviewed
captures at these paths and link them here:

- `docs/screenshots/market-overview.png`
- `docs/screenshots/market-explorer.png`
- `docs/screenshots/geographic-analysis.png`
- `docs/screenshots/price-drivers.png`
- `docs/screenshots/methodology.png`

## Dashboard features

- **Home — Market Overview:** dynamic market metrics, listing distributions,
  state counts, the verified nested-model finding, and a methodological note.
- **Market Explorer:** state, property-type, area, and price filters. Metrics,
  charts, the table, and CSV export use the same filtered records.
- **Geographic Analysis:** filters over the processed coordinate dataset,
  mapped listings, and state-level medians with listing counts.
- **Price Drivers:** Pearson and Spearman correlation, the HC3 regression,
  nested-model comparisons, and explicit observational caveats.
- **Methodology:** data preparation, variable definitions, statistical methods,
  verified baseline results, and limitations.

## Dataset overview

The cleaning pipeline reads these three inputs:

| Input file | Contribution |
| --- | --- |
| `mexico-real-estate-1.csv` | USD listing price, property type, state, area, latitude, longitude |
| `mexico-real-estate-2.csv` | MXN listing price, property type, state, area, latitude, longitude |
| `mexico-real-estate-3.csv` | USD listing price and area; state and coordinates are parsed from location fields |

The current audit records 700 raw rows per file, 2,082 analytical rows after
within-source cleaning, and 1,734 rows in the geospatial output. Dataset 2 prices
are converted using the configurable assumption of **19 MXN/USD**. The project
does not independently verify the historical validity of this rate.

The analytical output contains `source_dataset`, `property_type`, `state`,
`area_m2`, `price_usd`, `price_mxn`, `conversion_rate_mxn_per_usd`, and
`price_per_m2`. The geospatial output additionally contains `lat` and `lon`.
`price_per_m2` is calculated as `price_usd / area_m2`.

The files under `data/raw/` and `data/processed/` are excluded by
[`.gitignore`](.gitignore) and are not present in the tracked repository. Local
reproduction and deployment therefore require authorized copies of the input
or processed data at the expected paths. The dashboard specifically requires:

- `data/processed/mexico-real-combined-clean.csv`
- `data/processed/mexico-real-combined-geospatial.csv`

The repository does not establish original publishers, collection dates,
collection methods, or redistribution permissions for the input files. Confirm
provenance and terms before publishing or sharing any data. See
[`data/README.md`](data/README.md) for the cleaning audit and schema notes.

## Methodology summary

The pipeline standardizes fields, converts Dataset 2 prices from MXN, filters
for property type, state, positive area, and positive USD price, and removes
within-source duplicate standardized records. Potential cross-source matches
are reported but not removed because no unique listing identifier is available.
The geospatial file contains only records with coordinates within valid
latitude and longitude bounds.

Pearson measures linear association; Spearman measures rank-based monotonic
association. The regression uses log USD listing price with area, categorical
state, and categorical property type; HC3 robust standard errors are used for
uncertainty estimates. The four nested models use the same complete-case sample.
State-level medians are descriptive and are not adjusted for property mix.

For detailed definitions and limitations, see
[`app/pages/4_Methodology.py`](app/pages/4_Methodology.py).

## Limitations

- The listing data are observational and cannot establish causation.
- Geographic coverage is incomplete; the current geospatial file has 1,734 of
  2,082 analytical rows.
- State is a coarse location measure; neighborhood-level spatial modeling is
  not implemented.
- Source differences and the unverified Dataset 2 exchange-rate assumption may
  affect comparisons.
- The recorded values are listing prices, not verified transaction prices.
- The lack of unique listing identifiers prevents confirming physical
  cross-source duplicates.
- Price per square meter is mathematically coupled with area because area is
  its denominator.
- Regression estimates depend on the specified model and available variables.
  Property condition, age, neighborhood, and other characteristics are not
  modeled.
- The sample should not be generalized to the entire Mexican housing market
  without additional evidence.

## Technology stack

- Python (locally verified with Python 3.13)
- Streamlit
- pandas and NumPy
- Plotly
- statsmodels
- Jupyter, Matplotlib, and Seaborn for notebook-based analysis
- `unittest` and Streamlit AppTest

Dependencies are listed in [`requirements.txt`](requirements.txt). No
environment-specific paths or secrets are required by the application.

## Project structure

```text
mexican-real-estate-analysis/
├── app/
│   ├── Home.py
│   └── pages/
│       ├── 1_Market_Explorer.py
│       ├── 2_Geographic_Analysis.py
│       ├── 3_Price_Drivers.py
│       └── 4_Methodology.py
├── data/
│   ├── README.md
│   ├── raw/                         # local inputs; git-ignored
│   └── processed/                   # local outputs; git-ignored
├── notebooks/
├── src/
│   ├── dashboard/
│   └── real_estate_analysis.py
├── tests/
├── .gitignore
└── requirements.txt
```

## Local installation and environment

Use Python 3.13, the version verified for this project. From the repository
root, create and activate a virtual environment.

**Windows PowerShell**

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**macOS/Linux**

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

To regenerate processed data, place the three authorized Mexican input CSVs in
`data/raw/` and run:

```powershell
python -m src.real_estate_analysis
```

This command writes the processed CSVs and `cleaning_audit.json` under
`data/processed/`. It cannot run from a clone until the ignored raw files have
been supplied.

## Running the dashboard

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app\Home.py
```

Or, after activating the environment:

```bash
python -m streamlit run app/Home.py
```

The app reports an actionable data-loading error if its required processed CSVs
are absent.

## Running tests

The test suite uses synthetic data fixtures and does not require the ignored
source CSVs:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Streamlit Community Cloud preparation

**The repository is not currently deployable as-is:** the two processed CSVs
required by the dashboard are local and git-ignored. Before deployment, confirm
that sharing the derived data is permitted, then make both files available in
the GitHub repository under the paths listed above. Do not publish the raw
inputs unless their terms explicitly permit redistribution. If the processed
files cannot be included, the app needs an approved data-hosting approach and
corresponding loader changes before it can run in Cloud.

No secrets or external system packages are required. No custom
`.streamlit/config.toml` is currently needed. After the data-access question is
resolved:

1. Push the application source, `requirements.txt`, and the authorized
   processed files to the target GitHub repository and branch.
2. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/) and
   choose **Create app**.
3. Select the repository and branch containing the deployment-ready version.
4. Set the entrypoint to `app/Home.py`.
5. In **Advanced settings**, choose Python 3.13 to match the locally verified
   environment, then deploy. Community Cloud currently defaults to Python 3.12;
   confirm 3.13 remains available in the version selector.
6. Review the build logs and open each page after startup.

For dependency failures, compare Cloud build logs with `requirements.txt` and
the selected Python version. For missing-data errors, verify that both
processed CSV files are committed at the expected repository-relative paths.
Streamlit's current instructions are in the
[Community Cloud deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

The application has **not** been deployed.

## Future improvements

- Verify and document source attribution, collection dates, and data
  redistribution terms.
- Replace the unresolved currency assumption with a documented, defensible
  conversion basis if the required source information becomes available.
- Obtain unique listing identifiers and richer location/property variables.
- Evaluate additional model diagnostics and more detailed spatial methods.
- Add reviewed dashboard screenshots after they are captured.

## Author

Daniel Abdouroihamane Ibrahim Mhadji
