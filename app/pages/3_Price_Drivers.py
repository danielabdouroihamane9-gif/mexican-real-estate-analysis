"""Observational analysis of property price associations."""

import pandas as pd
import streamlit as st

from src.dashboard.charts import (
    area_price_scatter_chart,
    nested_model_r_squared_chart,
)
from src.dashboard.data_upload import load_dashboard_datasets
from src.dashboard.price_analysis import (
    MAIN_MODEL_FORMULA,
    PriceDriverAnalysis,
    analyze_price_drivers,
)
from src.dashboard.styles import apply_dashboard_style


def _format_statistic(value: float | None) -> str:
    return f"{value:.4f}" if value is not None else "N/A"


st.set_page_config(
    page_title="Price Drivers | Mexico Real Estate Insights",
    page_icon=":material/analytics:",
    layout="wide",
)
apply_dashboard_style()

st.title("Price Drivers")
st.markdown(
    "Are property prices in the Mexican real estate dataset more strongly "
    "associated with property size or geographical location?"
)
st.caption(
    "This page reports observational correlations and model-based explanatory "
    "comparisons. It does not estimate causal effects."
)

datasets = load_dashboard_datasets()
if datasets is None:
    st.stop()
analytical, _ = datasets


@st.cache_data(show_spinner=False)
def _cached_price_analysis(
    dataframe: pd.DataFrame,
) -> PriceDriverAnalysis:
    return analyze_price_drivers(dataframe)


try:
    analysis = _cached_price_analysis(analytical)
except ValueError as exc:
    st.error(f"Price-driver analysis could not be calculated: {exc}")
    st.stop()
pair_sample = analysis.correlation_sample
correlations = analysis.correlations
regression = analysis.regression
model_fits = analysis.model_fits
model_increments = analysis.model_increments

st.header("Area and total listing price")
log_price_scale = st.toggle(
    "Use a logarithmic USD price axis",
    value=True,
    help="Turn this off to display the listing-price axis on a linear scale.",
)
st.caption(
    "A logarithmic price axis helps display lower and higher priced listings "
    "together; it changes only the visualization, not the model or data."
    if log_price_scale
    else "The chart uses a linear USD price axis."
)
st.plotly_chart(
    area_price_scatter_chart(pair_sample, log_price_scale=log_price_scale),
    width="stretch",
    key="price_drivers_area_price",
    alt="Property area compared with listing price, colored by property type",
)

st.header("Correlation analysis")
with st.container(horizontal=True):
    st.metric("Valid area-price pairs", f"{correlations.observations:,}", border=True)
    st.metric(
        "Pearson correlation",
        _format_statistic(correlations.pearson),
        border=True,
    )
    st.metric(
        "Spearman correlation",
        _format_statistic(correlations.spearman),
        border=True,
    )
st.write(
    "Pearson measures linear association; Spearman measures rank-based "
    "monotonic association. Both are calculated on the same observations with "
    "finite, positive area and listing price. Neither correlation establishes "
    "causation."
)

st.header("Adjusted regression")
st.code(MAIN_MODEL_FORMULA, language="text")
with st.container(horizontal=True):
    st.metric("Model observations", f"{regression.observations:,}", border=True)
    st.metric("R²", f"{regression.r_squared:.4f}", border=True)
    st.metric("Adjusted R²", f"{regression.adjusted_r_squared:.4f}", border=True)
    st.metric(
        "Area coefficient",
        f"{regression.area_coefficient:.6f}",
        border=True,
    )
st.write(
    f"The area coefficient's HC3 robust standard error is "
    f"{regression.area_hc3_standard_error:.6f}; its 95% confidence interval is "
    f"[{regression.area_ci_low:.6f}, {regression.area_ci_high:.6f}]. Under this "
    f"log-price model, one additional square meter is associated with about "
    f"{regression.area_associated_percent:.3f}% higher listing price, holding "
    "state and property type constant."
)
st.caption(
    f"Correlations use n={correlations.observations:,} valid area-price pairs. "
    f"Regression uses n={regression.observations:,} observations with valid "
    "positive price and area plus non-missing state and property type. "
    f"{len(analytical) - regression.observations:,} analytical rows are excluded "
    "from regression only when they fail those model requirements."
)

st.header("Nested-model comparison")
st.write(
    "All four specifications use the same complete-case sample, so their "
    "in-sample R² values can be compared consistently."
)
st.plotly_chart(
    nested_model_r_squared_chart(model_fits),
    width="stretch",
    key="price_drivers_nested_model_r_squared",
    alt="R-squared values for four nested state, area, and property-type models",
)

model_table = model_fits.rename(
    columns={
        "model_id": "Model",
        "model": "Specification",
        "formula": "Formula",
        "observations": "N",
        "r_squared": "R²",
        "adjusted_r_squared": "Adjusted R²",
    }
)
st.dataframe(
    model_table,
    column_config={
        "N": st.column_config.NumberColumn(format="%,d"),
        "R²": st.column_config.NumberColumn(format="%.4f"),
        "Adjusted R²": st.column_config.NumberColumn(format="%.4f"),
    },
    hide_index=True,
    alt="Model formulas, sample sizes, and R-squared results",
)

increment_table = model_increments.rename(
    columns={
        "comparison": "Comparison",
        "reduced_model": "Reduced model",
        "expanded_model": "Expanded model",
        "observations": "N",
        "r_squared_change": "Change in R²",
    }
)
st.dataframe(
    increment_table,
    column_config={
        "N": st.column_config.NumberColumn(format="%,d"),
        "Change in R²": st.column_config.NumberColumn(format="%+.4f"),
    },
    hide_index=True,
    alt="Incremental R-squared comparisons between models using the same sample",
)
st.write(
    "In this sample, adding area to a state-only model contributes more "
    "incremental R² than adding property type to the area + state model. "
    "Property type alone adds little to the state-only model, while adding "
    "area to state + property type produces the larger R² change."
)
st.caption(
    "R² changes describe incremental in-sample explanatory association for "
    "these specifications; they do not measure causal importance. State is "
    "only a coarse measure of location."
)

st.header("Interpretation and limitations")
st.write(
    "The fitted area coefficient is a conditional observational association. "
    "Unmeasured property quality, neighborhood, market conditions, and listing "
    "characteristics may contribute to the observed patterns. State does not "
    "capture neighborhood-level location, and the listing sample may not "
    "represent the full Mexican housing market."
)
st.info(
    "Price per square meter is total price divided by area. Because area is "
    "its denominator, relationships between area and price per square meter "
    "are mathematically coupled and are not used here as primary evidence for "
    "the research question.",
    title="Price-per-square-meter caveat",
)
