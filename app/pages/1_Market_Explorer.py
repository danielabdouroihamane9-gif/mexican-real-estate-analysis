"""Interactive market explorer for property listings."""

import pandas as pd
import streamlit as st

from src.dashboard.charts import (
    area_price_scatter_chart,
    listing_price_chart,
    property_size_chart,
)
from src.dashboard.data_upload import load_dashboard_datasets
from src.dashboard.filtering import (
    available_category_values,
    filter_properties,
    numeric_range_bounds,
)
from src.dashboard.metrics import calculate_market_metrics
from src.dashboard.styles import apply_dashboard_style


def _render_numeric_range_filter(
    *,
    label: str,
    bounds: tuple[float, float] | None,
    key: str,
    currency: bool = False,
) -> tuple[float, float] | None:
    if bounds is None:
        st.caption(f"No valid numeric values are available for {label.lower()}.")
        return None

    lower, upper = bounds
    if lower == upper:
        st.caption(f"{label}: {lower:,.2f} (only valid value)")
        return bounds

    value_range = st.slider(
        label,
        min_value=lower,
        max_value=upper,
        step=(upper - lower) / 1000,
        key=key,
        format="$%.0f" if currency else "%.1f",
    )
    return float(value_range[0]), float(value_range[1])


def _format_currency(value: float | None, decimals: int) -> str:
    if value is None:
        return "N/A"
    return f"${value:,.{decimals}f}"


st.set_page_config(
    page_title="Market Explorer | Mexico Real Estate Insights",
    page_icon=":material/search:",
    layout="wide",
)
apply_dashboard_style()

st.title("Market Explorer")
st.markdown(
    "Filter the analytical listings by state, property type, area, and price. "
    "Every metric, chart, table, and export below uses the same filtered records."
)

datasets = load_dashboard_datasets()
if datasets is None:
    st.stop()
analytical, _ = datasets

state_options = available_category_values(analytical, "state")
property_type_options = available_category_values(analytical, "property_type")
area_bounds = numeric_range_bounds(analytical, "area_m2")
price_bounds = numeric_range_bounds(analytical, "price_usd")

filter_defaults: dict[str, list[object] | tuple[float, float]] = {
    "explorer_states": state_options,
    "explorer_property_types": property_type_options,
}
if area_bounds is not None:
    filter_defaults["explorer_area_range"] = area_bounds
if price_bounds is not None:
    filter_defaults["explorer_price_range"] = price_bounds
for key, default in filter_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default


def reset_filters() -> None:
    for key, default in filter_defaults.items():
        st.session_state[key] = default


with st.sidebar:
    st.header("Filter listings")
    st.button(
        "Reset filters",
        on_click=reset_filters,
        icon=":material/filter_alt_off:",
        width="stretch",
    )

    if state_options:
        st.multiselect(
            "State",
            options=state_options,
            key="explorer_states",
            help="All states are selected by default. Clear the selection to show no listings.",
        )
    else:
        st.caption("No valid state values are available to filter.")

    if property_type_options:
        st.multiselect(
            "Property type",
            options=property_type_options,
            key="explorer_property_types",
            help="All property types are selected by default. Clear the selection to show no listings.",
        )
    else:
        st.caption("No valid property types are available to filter.")

    area_range = _render_numeric_range_filter(
        label="Property area (m²)",
        bounds=area_bounds,
        key="explorer_area_range",
    )
    price_range = _render_numeric_range_filter(
        label="Listing price (USD)",
        bounds=price_bounds,
        key="explorer_price_range",
        currency=True,
    )
    st.caption(
        "Area and price ranges use all finite numeric values, including outliers. "
        "Rows missing a value for an active range filter are excluded."
    )

filtered = filter_properties(
    analytical,
    states=(
        st.session_state["explorer_states"]
        if state_options
        else None
    ),
    property_types=(
        st.session_state["explorer_property_types"]
        if property_type_options
        else None
    ),
    area_range=area_range,
    price_range=price_range,
)
metrics = calculate_market_metrics(filtered)

st.subheader("Selected market")
with st.container(horizontal=True):
    st.metric("Listings", f"{metrics.total_records:,}", border=True)
    st.metric(
        "Median listing price (USD)",
        _format_currency(metrics.median_price_usd, 0),
        border=True,
    )
    st.metric(
        "Median area (m²)",
        f"{metrics.median_area_m2:,.1f} m²"
        if metrics.median_area_m2 is not None
        else "N/A",
        border=True,
    )
    st.metric(
        "Median price per m² (USD)",
        _format_currency(metrics.median_price_per_m2, 2),
        border=True,
    )

if filtered.empty:
    st.info(
        "No listings match the selected filters. Reset the filters or select "
        "additional values to continue exploring."
    )
else:
    st.subheader("Listing distributions")
    log_price_scale = st.toggle(
        "Use a logarithmic USD price axis",
        value=True,
        help=(
            "A logarithmic price axis helps compare listings across a wide "
            "price range. Turn it off to use a linear scale."
        ),
    )
    st.caption(
        "The logarithmic scale changes only the chart axis; it does not change "
        "the filtered data or the values shown in tooltips."
        if log_price_scale
        else "The charts use a linear USD price axis."
    )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            listing_price_chart(filtered, log_scale=log_price_scale),
            width="stretch",
            key="explorer_listing_prices",
            alt="Listing price distribution for the selected records",
        )
    with right:
        st.plotly_chart(
            property_size_chart(filtered),
            width="stretch",
            key="explorer_property_sizes",
            alt="Property size distribution for the selected records",
        )

    st.subheader("Property area versus listing price")
    st.plotly_chart(
        area_price_scatter_chart(filtered, log_price_scale=log_price_scale),
        width="stretch",
        key="explorer_area_price",
        alt="Property area compared with listing price for selected listings",
    )
    st.caption(
        "The scatter plot includes records with valid positive area and price; "
        "no trend line or causal interpretation is applied."
    )

st.subheader("Filtered listings")
display_columns = [
    "property_type",
    "state",
    "area_m2",
    "price_usd",
    "price_per_m2",
]
column_labels = {
    "property_type": "Property type",
    "state": "State",
    "area_m2": "Area (m²)",
    "price_usd": "Listing price (USD)",
    "price_per_m2": "Price per m² (USD)",
}
table_data = filtered.loc[:, display_columns].rename(columns=column_labels)
st.caption("Blank cells indicate values unavailable in the processed dataset.")
st.dataframe(
    table_data,
    column_config={
        "Area (m²)": st.column_config.NumberColumn(format="%.1f"),
        "Listing price (USD)": st.column_config.NumberColumn(format="$%,.0f"),
        "Price per m² (USD)": st.column_config.NumberColumn(format="$%,.2f"),
    },
    hide_index=True,
    height=420,
    alt="Filtered property listings with type, state, area, and price fields",
)
st.download_button(
    "Download filtered listings (CSV)",
    data=table_data.to_csv(index=False).encode("utf-8"),
    file_name="mexico_real_estate_filtered.csv",
    mime="text/csv",
    disabled=filtered.empty,
    icon=":material/download:",
)
