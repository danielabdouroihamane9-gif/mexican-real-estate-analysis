
# Data Documentation — Mexican Real Estate Market

## 1. Research Context

Real estate prices are influenced by multiple characteristics of a property and its surrounding environment.

Two important dimensions are:

- **Property size:** The physical dimensions of a property, including its built area and, where available, its land area.
- **Location:** The geographical position of a property and the characteristics of the surrounding area.

A larger property may have a higher total price because it offers more living or usable space. However, a smaller property in a highly desirable location may be more expensive than a larger property elsewhere.

This creates an interesting question for real estate analysis: how much of a property's market value is associated with its physical characteristics, and how much is associated with where it is located?

This project investigates that question using real estate listings from Mexico City as part of WorldQuant University's Data Science Fundamentals Lab.

## 2. Central Research Question

> **Are property prices in Mexico more influenced by property size or by location?**

The objective is to investigate the relationships between property prices, property characteristics, and geographical location using exploratory data analysis, statistical techniques, and data visualization.

The analysis will focus on identifying patterns, measuring associations, comparing geographical differences, and determining which of the two dimensions has a stronger relationship with property prices in the available dataset.

The investigation will not assume in advance that either size or location is more important.

## 3. Background: The Mexican Real Estate Market

### 3.1 Regional Differences in Housing Prices

Mexico's housing market is not geographically uniform. Property values and housing-price movements differ across metropolitan areas and states.

According to the Sociedad Hipotecaria Federal (SHF), its national housing price index recorded an annual increase of 8.7% in 2025.

The reported annual changes also differed across metropolitan areas:

| Metropolitan area | Housing price index change in 2025 |
| ----------------- | ---------------------------------: |
| Guadalajara       |                             +11.3% |
| Tijuana           |                             +10.6% |
| Monterrey         |                              +9.4% |
| Puebla–Tlaxcala   |                              +8.7% |
| Querétaro         |                              +7.2% |
| Valley of Mexico  |                              +5.1% |
| Toluca            |                              +4.6% |

**Source:** Sociedad Hipotecaria Federal (SHF), Housing Price Index, Fourth Quarter 2025.

These figures illustrate regional differences in housing-price appreciation. They do not represent the absolute price of a property in each location.

For this project, the relevance is that geographical context deserves careful investigation rather than treating all properties as if they belong to one homogeneous market.

### 3.2 Housing Affordability and Market Conditions

The Organisation for Economic Co-operation and Development (OECD), in its 2024 Economic Survey of Mexico, reported that:

- Real housing prices increased by 31% between 2005 and 2020.
- Housing prices increased 1.5 times faster than average income over the same period.
- Low housing supply and high demand contributed to rising housing prices.

The OECD also highlighted affordability challenges, particularly for lower-income households.

This broader economic context demonstrates that property prices are connected to more than the physical dimensions of individual homes.

### 3.3 Why Property Size Matters

Property size is an important characteristic because it affects the amount of usable residential space available to buyers.

Potential size-related variables include:

- Built area.
- Land area.
- Number of bedrooms.
- Number of bathrooms.
- Property type.

A larger property may have a higher total selling price. However, the relationship may not be proportional.

For example, doubling the built area does not necessarily double the property's market price.

It is therefore useful to investigate both:

- Total property price.
- Price per square meter, where the necessary measurements are available.

### 3.4 Why Location Matters

Location can influence property values through several characteristics of the surrounding area.

Potential location-related factors include:

- City or metropolitan area.
- State and municipality.
- Neighborhood.
- Distance to employment centers.
- Access to public transportation.
- Access to schools, hospitals, and commercial facilities.
- Local infrastructure and public services.
- Neighborhood desirability and safety.

These characteristics can influence housing demand and the prices buyers are willing to pay.

However, not all these variables will necessarily be available in the project dataset. The analysis must distinguish between factors that can be measured and factors that are only part of the broader market context.

## 4. Research Objectives

The project has the following objectives:

1. Understand the structure and characteristics of the real estate dataset.
2. Investigate the distribution of property prices and property sizes.
3. Identify missing values, inconsistent records, and potential outliers.
4. Examine the relationship between property size and price.
5. Investigate geographical differences in property prices.
6. Compare property prices across available geographical categories.
7. Use correlation analysis to quantify relationships between numerical variables.
8. Interpret the findings in the context of the research question.

## 5. Data Requirements and Relevant Variables

The analysis will depend on the actual variables available in the dataset.

The following table identifies the types of information that would be useful.

| Variable category        | Potential variables                | Analytical purpose               |
| ------------------------ | ---------------------------------- | -------------------------------- |
| Property price           | Listing price                      | Main outcome variable            |
| Property size            | Built area, land area              | Measure property dimensions      |
| Property characteristics | Bedrooms, bathrooms, property type | Additional explanatory variables |
| Geographic information   | Latitude, longitude                | Examine spatial distribution     |
| Administrative location  | State, municipality, neighborhood  | Compare geographical groups      |

**Important:** This is a list of relevant variable categories, not a confirmed description of the dataset's actual columns. The actual schema will be documented after inspecting the supplied files.

## 6. Analytical Approach

The investigation will follow a structured data science workflow.

### Stage 1 — Data Inspection

- Load the supplied datasets.
- Inspect their dimensions and data types.
- Identify available variables.
- Examine missing values.
- Check for duplicate records and inconsistent values.

### Stage 2 — Data Cleaning

- Handle missing or invalid observations.
- Standardize relevant data types.
- Check price and area measurements.
- Investigate extreme values and potential outliers.
- Prepare location information for analysis.

### Stage 3 — Exploratory Data Analysis

Investigate the distribution of:

- Property prices.
- Property sizes.
- Available property characteristics.
- Geographic locations.

Use appropriate visualizations, including histograms, box plots, scatter plots, and geographical visualizations where appropriate.

### Stage 4 — Property Size Analysis

Investigate whether larger properties tend to have higher listing prices.

Potential techniques:

- Scatter plots of property size against price.
- Pearson correlation for linear association.
- Spearman correlation for rank-based monotonic association.
- Comparison of price distributions across size groups.
- Price-per-square-meter analysis, where possible.

### Stage 5 — Location Analysis

Investigate how property prices vary geographically.

Potential techniques:

- Compare price distributions across available locations.
- Calculate group-level mean and median prices.
- Visualize geographical price patterns.
- Examine latitude and longitude where available.
- Compare properties in different locations while considering their size.

### Stage 6 — Comparative Interpretation

Compare the observed relationships between:

1. Property size and listing price.
2. Location and listing price.

The objective is to assess which dimension has a stronger association with price in the available sample.

Correlation alone will not be treated as proof of causation.

## 7. Research Hypotheses

The investigation will consider the following hypotheses.

### Hypothesis 1 — Property Size

Larger properties tend to have higher listing prices.

### Hypothesis 2 — Location

Properties in certain geographical areas tend to have higher listing prices than comparable properties in other areas.

### Hypothesis 3 — Combined Influence

Property size and location may both be associated with listing prices, and their relationships may differ depending on the geographical area.

These are hypotheses to investigate, not established findings.

## 8. Important Statistical Considerations

### Correlation versus Causation

A strong correlation between property size and price does not prove that size alone causes the increase in price.

Similarly, differences in average prices between neighborhoods do not establish that location itself causes those differences.

Other variables may influence both.

### Confounding Variables

Potential confounding factors include:

- Property type.
- Property condition.
- Number of bedrooms and bathrooms.
- Neighborhood characteristics.
- Local infrastructure.
- Market demand.
- Property age.

If these factors are not available, their potential influence must be acknowledged.

### Total Price versus Price per Square Meter

Total price and price per square meter measure different things.

A larger property may have a higher total price while having a lower price per square meter.

Both measures can provide useful perspectives, but they should not be treated as interchangeable.

### Geographic Granularity

The meaning of location depends on the available level of geographic detail.

A city-level comparison is different from a neighborhood-level comparison. Latitude and longitude can provide more detailed spatial information, but their usefulness depends on data quality and coverage.

## 9. Dataset Information

The project uses real estate listings from Mexico City, as described by WorldQuant University.

The exact dataset metadata will be documented after inspecting the supplied files.

| Metadata                                    | Status                                            |
| ------------------------------------------- | ------------------------------------------------- |
| Dataset name                                | To be confirmed                                   |
| Original source                             | To be confirmed                                   |
| Geographic coverage                         | Mexico City, according to WQU project description |
| Time period                                 | To be confirmed                                   |
| Number of records                           | To be calculated                                  |
| Number of variables                         | To be calculated                                  |
| File formats                                | To be inspected                                   |
| Currency                                    | To be verified                                    |
| Area measurement units                      | To be verified                                    |
| Data license and redistribution permissions | To be checked                                     |

## 10. Data Storage Structure

```text
data/
│
├── README.md
│
├── raw/
│   └── Original datasets
│
└── processed/
    └── Cleaned and transformed datasets
```

### raw/

Contains original datasets in their supplied form.

Original files should remain unchanged so that the analysis can be reproduced.

### processed/

Contains cleaned or transformed datasets generated during the analysis.

Processed files should be derived from the original data through documented steps.

**Data management principle:** Do not overwrite original datasets during cleaning and preprocessing.

## 11. Data Quality and Limitations

Real estate listing data may have limitations that affect the conclusions.

Potential issues include:

- Missing property characteristics.
- Incorrect or inconsistent listing prices.
- Duplicate listings.
- Extreme property prices or areas.
- Inconsistent geographical information.
- Differences in property types.
- Asking prices that differ from actual transaction prices.
- Uneven representation of neighborhoods.

The analysis will document these issues rather than assuming that the dataset perfectly represents the entire housing market.

In particular, findings from a dataset of listings should be interpreted as patterns within the observed listings, not necessarily as definitive estimates of all completed property transactions.

## 12. External Research and References

The following sources provide broader context for understanding the Mexican housing market.

1. **WorldQuant University — Data Science Lab**

   Project description: Hands-on Data Science in the Mexican Real Estate Market.

   <https://www.wqu.edu/data-science-lab>
2. **Sociedad Hipotecaria Federal (SHF) — Housing Price Index, 2025–2026**

   Official housing price index publications and geographical breakdowns.

   <https://www.gob.mx/shf/documentos/indice-shf-de-precios-de-la-vivienda-en-mexico-2025-a-2026>
3. **Sociedad Hipotecaria Federal (SHF) — Fourth Quarter 2025 Results**

   National housing-price statistics and metropolitan-area comparisons.

   <https://www.gob.mx/shf/documentos/indice-shf-de-precios-de-la-vivienda-en-mexico-cuarto-trimestre-de-2025>
4. **OECD — Economic Surveys: Mexico 2024**

   Housing affordability, price developments, and housing supply and demand.

   <https://www.oecd.org/en/publications/oecd-economic-surveys-mexico-2024_b8d974db-en/full-report/component-8.html>
5. **Banco de México — Housing Registry for Mexico**

   Documentation of Mexican housing data, including property characteristics, geographical information, and prices.

   <https://www.banxico.org.mx/apps/econlab/fichas/espanol/%7B85EB273E-668F-DC4D-1B3F-C928773F8810%7D.pdf>

---

## 13. Research Integrity

The conclusions of this project must come from the supplied dataset and the analysis performed on it.

External research provides context, but it must not be used as a substitute for evidence from the project data.

No numerical findings, statistical relationships, or conclusions will be reported until they have been calculated and verified.

The ultimate objective is to answer the central research question using transparent, reproducible, and evidence-based analysis.
