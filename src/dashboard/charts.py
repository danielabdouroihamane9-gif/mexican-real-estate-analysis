"""Plotly figures for the market overview dashboard."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.metrics import aggregate_property_types, aggregate_states


CHART_COLOR = "#26736f"
CHART_TEMPLATE = "plotly_white"


def property_type_chart(dataframe: pd.DataFrame) -> go.Figure:
    counts = aggregate_property_types(dataframe)
    figure = px.bar(
        counts,
        x="listings",
        y="property_type",
        orientation="h",
        color_discrete_sequence=[CHART_COLOR],
        title="Listings by property type",
        labels={"listings": "Number of listings", "property_type": "Property type"},
        template=CHART_TEMPLATE,
    )
    figure.update_traces(
        hovertemplate="%{y}<br>Listings: %{x:,}<extra></extra>"
    )
    figure.update_layout(
        yaxis={"categoryorder": "total ascending"},
        margin={"l": 8, "r": 16, "t": 56, "b": 8},
    )
    return figure


def listing_price_chart(
    dataframe: pd.DataFrame,
    *,
    log_scale: bool = True,
) -> go.Figure:
    values = _positive_numeric_values(dataframe, "price_usd")
    figure = px.histogram(
        x=values,
        nbins=40,
        color_discrete_sequence=[CHART_COLOR],
        title="Listing price distribution",
        labels={"x": "Listing price (USD)", "y": "Number of listings"},
        template=CHART_TEMPLATE,
    )
    figure.update_traces(
        hovertemplate="Price: $%{x:,.0f}<br>Listings: %{y:,}<extra></extra>"
    )
    figure.update_xaxes(
        type="log" if log_scale else "linear",
        tickprefix="$",
        tickformat="~s" if log_scale else ",.0f",
    )
    figure.update_layout(
        margin={"l": 8, "r": 16, "t": 56, "b": 8},
        xaxis_title="Listing price (USD; logarithmic scale)"
        if log_scale
        else "Listing price (USD)",
    )
    return figure


def property_size_chart(dataframe: pd.DataFrame) -> go.Figure:
    values = _positive_numeric_values(dataframe, "area_m2")
    figure = px.histogram(
        x=values,
        nbins=40,
        color_discrete_sequence=[CHART_COLOR],
        title="Property size distribution",
        labels={"x": "Property size (m²)", "y": "Number of listings"},
        template=CHART_TEMPLATE,
    )
    figure.update_traces(
        hovertemplate="Size: %{x:,.0f} m²<br>Listings: %{y:,}<extra></extra>"
    )
    figure.update_layout(
        margin={"l": 8, "r": 16, "t": 56, "b": 8},
        xaxis_title="Property size (m²)",
        yaxis_title="Number of listings",
    )
    return figure


def state_distribution_chart(
    dataframe: pd.DataFrame,
    *,
    top_n: int = 15,
) -> go.Figure:
    counts = aggregate_states(dataframe).head(top_n).sort_values(
        "listings", ascending=True
    )
    figure = px.bar(
        counts,
        x="listings",
        y="state",
        orientation="h",
        color_discrete_sequence=[CHART_COLOR],
        title=f"Listings by state (top {top_n})",
        labels={"listings": "Number of listings", "state": "State"},
        template=CHART_TEMPLATE,
    )
    figure.update_traces(
        hovertemplate="%{y}<br>Listings: %{x:,}<extra></extra>"
    )
    figure.update_layout(margin={"l": 8, "r": 16, "t": 56, "b": 8})
    return figure


def _positive_numeric_values(dataframe: pd.DataFrame, column: str) -> pd.Series:
    if column not in dataframe:
        return pd.Series(dtype="float64", name=column)
    values = pd.to_numeric(dataframe[column], errors="coerce")
    values = values.replace([float("inf"), float("-inf")], pd.NA).dropna()
    return values[values.gt(0)]
