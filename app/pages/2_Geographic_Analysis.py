"""Geographic market analysis using the processed coordinate dataset."""

import pandas as pd
import streamlit as st

from src.dashboard.charts import geographic_map_chart, state_median_chart
from src.dashboard.data_loader import DashboardDataError, load_processed_datasets
from src.dashboard.filtering import (
    available_category_values,
    filter_properties,
    numeric_range_bounds,
)
from src.dashboard.geographic_analysis import (
    summarize_states,
    valid_coordinate_mask,
)
from src.dashboard.metrics import calculate_market_metrics
from src.dashboard.styles import apply_dashboard_style


def _render_price_range(
    bounds: tuple[float, float] | None,
) -> tuple[float, float] | None:
    if bounds is None:
        st.caption("No valid listing prices are available for filtering.")
        return None

    lower, upper = bounds
    if lower == upper:
        st.caption(f"Listing price (USD): ${lower:,.2f} (only valid value)")
        return bounds

    value_range = st.slider(
        "Listing price (USD)",
        min_value=lower,
        max_value=upper,
        step=(upper - lower) / 1000,
        key="geographic_price_range",
        format="$%.0f",
    )
    return float(value_range[0]), float(value_range[1])


st.set_page_config(
    page_title="Geographic Analysis | Mexico Real Estate Insights",
    page_icon=":material/map:",
    layout="wide",
)
apply_dashboard_style()

st.title("Geographic Analysis")
st.markdown(
    "Explore the locations represented in the processed geospatial listings "
    "and compare descriptive market statistics across states."
)

try:
    analytical, geospatial = load_processed_datasets()
except DashboardDataError as exc:
    st.error(str(exc))
    st.stop()

state_options = available_category_values(geospatial, "state")
property_type_options = available_category_values(geospatial, "property_type")
price_bounds = numeric_range_bounds(geospatial, "price_usd")
filter_defaults: dict[str, list[object] | tuple[float, float]] = {
    "geographic_states": state_options,
    "geographic_property_types": property_type_options,
}
if price_bounds is not None:
    filter_defaults["geographic_price_range"] = price_bounds
for key, default in filter_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default


def reset_geographic_filters() -> None:
    for key, default in filter_defaults.items():
        st.session_state[key] = default


with st.sidebar:
    st.header("Geographic filters")
    st.button(
        "Reset filters",
        on_click=reset_geographic_filters,
        icon=":material/filter_alt_off:",
        width="stretch",
    )
    if state_options:
        st.multiselect(
            "State",
            options=state_options,
            key="geographic_states",
            help="All states are selected by default.",
        )
    else:
        st.caption("No valid state values are available.")
    if property_type_options:
        st.multiselect(
            "Property type",
            options=property_type_options,
            key="geographic_property_types",
            help="All property types are selected by default.",
        )
    else:
        st.caption("No valid property types are available.")
    price_range = _render_price_range(price_bounds)
    st.caption(
        "The price range spans all finite positive values, including outliers. "
        "Rows without a valid price are excluded when a range is active."
    )

filtered = filter_properties(
    geospatial,
    states=st.session_state["geographic_states"] if state_options else None,
    property_types=(
        st.session_state["geographic_property_types"]
        if property_type_options
        else None
    ),
    price_range=price_range,
)
coordinate_mask = valid_coordinate_mask(filtered)
map_data = filtered.loc[coordinate_mask].copy()
state_summary = summarize_states(filtered)
metrics = calculate_market_metrics(filtered)
coverage = (
    len(geospatial) / len(analytical) * 100
    if len(analytical)
    else 0.0
)

st.caption(
    f"The geospatial dataset contains {len(geospatial):,} of "
    f"{len(analytical):,} analytical records ({coverage:.1f}%). Geographic "
    "comparisons are limited to records in this processed geospatial dataset."
)
st.subheader("Selected geographic sample")
with st.container(horizontal=True):
    st.metric("Selected listings", f"{metrics.total_records:,}", border=True)
    st.metric("States represented", f"{len(state_summary):,}", border=True)
    st.metric("Mapped coordinates", f"{len(map_data):,}", border=True)
    st.metric(
        "Median listing price (USD)",
        f"${metrics.median_price_usd:,.0f}"
        if metrics.median_price_usd is not None
        else "N/A",
        border=True,
    )

st.subheader("Property locations")
if map_data.empty:
    st.info("No selected records have valid coordinates to display on the map.")
else:
    st.plotly_chart(
        geographic_map_chart(map_data),
        width="stretch",
        key="geographic_property_map",
        alt="Map of available property coordinates in the selected dataset",
    )
    st.caption(
        f"All {len(map_data):,} selected rows with valid coordinates are shown; "
        "no geographic observations were sampled or aggregated."
    )
if len(map_data) != len(filtered):
    st.caption(
        f"{len(filtered) - len(map_data):,} selected rows with missing or invalid "
        "coordinates are retained in the state statistics but not plotted."
    )

st.subheader("State-level market comparison")
chart_metric = st.selectbox(
    "Compare state medians",
    ["Median listing price (USD)", "Median price per m² (USD)"],
)
chart_column = (
    "median_price_usd"
    if chart_metric == "Median listing price (USD)"
    else "median_price_per_m2"
)
if state_summary[chart_column].notna().any():
    st.plotly_chart(
        state_median_chart(state_summary, metric=chart_metric),
        width="stretch",
        key="geographic_state_medians",
        alt=f"{chart_metric} by state, with listing counts in hover details",
    )
else:
    st.info("No valid state-level median values are available for this selection.")

table_data = state_summary.rename(
    columns={
        "state": "State",
        "listings": "Listings",
        "median_price_usd": "Median listing price (USD)",
        "median_price_per_m2": "Median price per m² (USD)",
        "median_area_m2": "Median area (m²)",
    }
)
st.dataframe(
    table_data,
    column_config={
        "Listings": st.column_config.NumberColumn(format="%,d"),
        "Median listing price (USD)": st.column_config.NumberColumn(
            format="$%,.0f"
        ),
        "Median price per m² (USD)": st.column_config.NumberColumn(
            format="$%,.2f"
        ),
        "Median area (m²)": st.column_config.NumberColumn(format="%.1f"),
    },
    hide_index=True,
    alt="State-level listing counts and median market statistics",
)
st.caption(
    "All represented states are included; no minimum sample-size threshold is "
    "applied. Listing counts are shown for context and to help assess stability."
)

st.subheader("What the selected sample shows")
ranked_prices = state_summary.dropna(subset=["median_price_usd"])
if ranked_prices.empty:
    st.write("There are no valid state-level listing-price medians to compare.")
elif len(ranked_prices) == 1:
    state = ranked_prices.iloc[0]
    st.write(
        f"{state['state']} has a median listing price of "
        f"${state['median_price_usd']:,.0f} across {int(state['listings']):,} "
        "selected geospatial listings."
    )
else:
    highest = ranked_prices.loc[ranked_prices["median_price_usd"].idxmax()]
    lowest = ranked_prices.loc[ranked_prices["median_price_usd"].idxmin()]
    st.write(
        f"In this selected geospatial sample, {highest['state']} has the highest "
        f"observed state median listing price (${highest['median_price_usd']:,.0f}; "
        f"n={int(highest['listings']):,}), while {lowest['state']} has the lowest "
        f"(${lowest['median_price_usd']:,.0f}; n={int(lowest['listings']):,})."
    )
st.caption(
    "These are descriptive differences, not explanations or causal effects. "
    "State medians do not adjust for property characteristics."
)

st.subheader("Geographic limitations")
st.write(
    "Coordinates are available for only a subset of the analytical observations. "
    "The map shows the coverage of the processed geospatial dataset, not the full "
    "Mexican housing market. State is a coarse geographic unit, and state-level "
    "medians do not account for every property characteristic. Coordinates do "
    "not establish exact street-level precision; observed geographic price "
    "differences do not establish causation."
)
