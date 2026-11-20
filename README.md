# Mexican Real Estate Analysis

## 1. Project Overview

This project explores the Mexican real estate market through practical data science techniques.

The objective is to investigate the dataset, understand its structure, clean and transform the data, perform exploratory data analysis (EDA), and identify meaningful patterns and insights.

This project is part of my ongoing development in Data Science and Machine Learning.

## 2. Project Objectives

- Understand and inspect the available dataset.
- Perform data cleaning and preprocessing.
- Handle missing values and inconsistent data.
- Conduct exploratory data analysis (EDA).
- Apply appropriate statistical techniques.
- Create meaningful data visualizations.
- Communicate findings and insights based on the data.

## 3. Technologies and Tools

- Python
- NumPy
- Pandas
- Matplotlib
- Seaborn
- Jupyter Notebook
- Visual Studio Code

## 4. Project Structure

```text
mexican-real-estate-analysis/
│
├── notebooks/
│   ├── 01_initial_exploration.ipynb
│   ├── 02_visualizing_housing_data.ipynb
│   ├── 03_correlation_&_variable_relationship.ipynb
│   └── 04_price_per_square_meter_&_location_effect.ipynb
│
├── src/
│   ├── __init__.py
│   └── real_estate_analysis.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
│
├── tests/
│   └── test_real_estate_analysis.py
│
├── reports/
│
├── requirements.txt
├── .gitignore
└── README.md
```

## 5. Project Workflow

The project will follow these general stages:

1. Data collection and loading
2. Data inspection and understanding
3. Data cleaning and preprocessing
4. Exploratory data analysis
5. Data visualization
6. Statistical investigation
7. Findings and conclusions

The actual workflow may be adjusted according to the dataset and project requirements.

## 6. Environment Setup

Clone the repository:

```bash
git clone https://github.com/danielabdouroihamane9-gif/mexican-real-estate-analysis.git
cd mexican-real-estate-analysis
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Launch Jupyter through VS Code or run:

```bash
jupyter notebook
```

## 7. Current Progress

- [X] Repository created
- [X] Development environment configured
- [X] Dataset inspection
- [X] Reproducible cleaning pipeline
- [X] Exploratory data analysis
- [X] Data visualization
- [X] Statistical regression and state-level analysis
- [X] Audit documentation

## 8. Findings

The four notebooks document the observed associations in the supplied listing sample.
The project does not interpret these relationships as causal effects. Final numerical
findings should be reproduced by executing the notebooks; the cleaning module is the
source of the processed datasets.

### Analytical result

The final multiple regression uses
`log(price_usd) ~ area_m2 + state + property_type` with 2,082 observations.
It estimates an adjusted area association of 0.005483 log-USD per additional square meter,
with HC3 confidence interval 0.005243 to 0.005723. This corresponds to approximately
0.550% per additional square meter in the log-price model. R-squared is 0.5203 and
adjusted R-squared is 0.5131.

This is a listing-level association, not a causal effect. State and property-type
coefficients describe grouped patterns and may reflect unmeasured quality, neighborhood,
market, and listing characteristics. Heteroskedasticity-robust standard errors are used,
but residual and multicollinearity diagnostics should be considered.

### Currency and data limitations

- Dataset 2's MXN prices are converted using an explicit, unresolved assumption of
  19 MXN per USD. The source and date of this rate cannot be verified in this repository,
  so it is not presented as historically accurate.
- Excluding Dataset 2 changes the regression sample to 1,391 observations and produces
  an area coefficient of 0.005599, R-squared 0.5311, and adjusted R-squared 0.5204.
- Dataset 3 state names are inferred from `place_with_parent_names`.
- Cross-source overlap detection uses standardized exact keys, but matching rows are not
  claimed to represent the same physical property because no listing identifier exists.
- Cross-source overlap counts require the same standardized key to occur in at least two
  distinct source datasets. Within-source repeated standardized keys are reported separately.
- Listing data may contain reporting errors and outliers.

### Nested model comparison

The main regression is compared on the same observations using state-only, area plus state,
area plus state plus property type, and state plus property type specifications. R-squared
changes measure incremental model-based explanatory association, not causal importance.
Detailed neighborhood-level location variables are not available in the main regression.

## 8A. Reproduction

Regenerate the cleaned datasets and audit report:

```powershell
python -m src.real_estate_analysis
python -m unittest discover -s tests -v
```

Execute all notebooks from the repository root:

```powershell
jupyter nbconvert --to notebook --execute notebooks/01_initial_exploration.ipynb
jupyter nbconvert --to notebook --execute notebooks/02_visualizing_housing_data.ipynb
jupyter nbconvert --to notebook --execute "notebooks/03_correlation_&_variable_relationship.ipynb"
jupyter nbconvert --to notebook --execute "notebooks/04_price_per_square_meter_&_location_effect.ipynb"
```

## 8B. Dashboard

The Market Overview dashboard reads the processed CSVs generated by the
existing cleaning module. Install the project dependencies and launch it from
the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app/Home.py
```

The home page summarizes market metrics, listing distributions, state coverage,
and the nested-model research finding. The other sidebar pages are placeholders
for later project phases.

## 9. Learning Objectives

Through this project, I aim to strengthen my practical understanding of:

- Python for data science
- Data manipulation with Pandas
- Numerical computing with NumPy
- Exploratory data analysis
- Statistical reasoning
- Data visualization
- Analytical problem-solving

## 10. Author

Daniel Abdouroihamane Ibrahim Mhadji

Computer Science Student | AI, Machine Learning & Software Engineering
