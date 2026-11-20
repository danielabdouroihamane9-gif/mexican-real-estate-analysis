"""Market overview for Mexico Real Estate Insights."""

import streamlit as st

from src.dashboard.charts import (
    listing_price_chart,
    property_size_chart,
    property_type_chart,
    state_distribution_chart,
)
from src.dashboard.data_loader import DashboardDataError, load_processed_datasets
from src.dashboard.metrics import calculate_market_metrics
from src.dashboard.styles import apply_dashboard_style


st.set_page_config(
    page_title="Mexico Real Estate Insights",
    page_icon=":material/home:",
    layout="wide",
)
apply_dashboard_style()

st.title("Mexico Real Estate Insights")
st.markdown(
    "An analytical overview of property listings combined from three Mexican "
    "real-estate source datasets. This application explores property prices, "
    "property characteristics, and geographical differences."
)

with st.container(border=True):
    st.markdown("**Research question**")
    st.write(
        "Are property prices in the Mexican real estate dataset more strongly "
        "associated with property size or geographical location?"
    )
    st.caption(
        "The overview summarizes prices, property characteristics, and "
        "state-level differences in the available listing data."
    )

try:
    analytical, _ = load_processed_datasets()
except DashboardDataError as exc:
    st.error(str(exc))
    st.stop()

metrics = calculate_market_metrics(analytical)

st.header("Market at a glance")
with st.container(horizontal=True):
    st.metric("Property records", f"{metrics.total_records:,}", border=True)
    st.metric("States represented", f"{metrics.state_count:,}", border=True)
    st.metric(
        "Median listing price (USD)",
        f"${metrics.median_price_usd:,.0f}" if metrics.median_price_usd is not None else "N/A",
        border=True,
    )
    st.metric(
        "Median property size (m²)",
        f"{metrics.median_area_m2:,.1f} m²" if metrics.median_area_m2 is not None else "N/A",
        border=True,
    )
    st.metric(
        "Median price per m² (USD)",
        f"${metrics.median_price_per_m2:,.2f} / m²"
        if metrics.median_price_per_m2 is not None
        else "N/A",
        border=True,
    )

st.header("Property market distribution")
price_log_scale = st.toggle(
    "Use a logarithmic price axis",
    value=True,
    help="A logarithmic axis makes the price distribution easier to read when listings span a wide range.",
)

left, right = st.columns(2)
with left:
    st.plotly_chart(
        property_type_chart(analytical),
        width="stretch",
        key="market_property_types",
        alt="Listing counts by property type",
    )
with right:
    st.plotly_chart(
        listing_price_chart(analytical, log_scale=price_log_scale),
        width="stretch",
        key="market_listing_prices",
        alt="Distribution of listing prices in US dollars",
    )

left, right = st.columns(2)
with left:
    st.plotly_chart(
        property_size_chart(analytical),
        width="stretch",
        key="market_property_sizes",
        alt="Distribution of property sizes in square meters",
    )
with right:
    st.plotly_chart(
        state_distribution_chart(analytical),
        width="stretch",
        key="market_state_counts",
        alt="Listing counts for the most represented states",
    )

st.header("Main research finding")
with st.container(border=True):
    st.subheader("Property area adds substantially more explanatory power than state alone")
    st.write(
        "In the notebook's nested-model comparison (2,082 observations), the "
        "state-only model has R² = 0.0632, compared with R² = 0.4757 for the "
        "area + state model. Adding property area to the state-only model "
        "increases R² by approximately 0.4125."
    )
    st.write(
        "Adding property type to the area + state model increases R² from "
        "0.4757 to 0.5203 (approximately 0.0446). For context, the state + "
        "property type model has R² = 0.0641."
    )
    st.caption(
        "These are comparisons within this dataset and model specification; "
        "they do not establish causation. State is a coarse geographical "
        "measure, not a complete representation of location."
    )

st.header("Methodological note")
st.write(
    "The analytical dataset combines three source datasets. Dataset 2's "
    "original prices in MXN were converted to USD using an assumed, "
    "configurable rate of 19 MXN per USD; that exchange-rate assumption has "
    "not been independently verified. These observational results should not "
    "be interpreted as causal evidence."
)
st.page_link("pages/4_Methodology.py", label="View the methodology page")

