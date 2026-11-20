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


def area_price_scatter_chart(
    dataframe: pd.DataFrame,
    *,
    log_price_scale: bool = True,
) -> go.Figure:
    required_columns = ["area_m2", "price_usd", "property_type", "state"]
    available_columns = [column for column in required_columns if column in dataframe]
    points = dataframe.loc[:, available_columns].copy()

    for column in ("area_m2", "price_usd"):
        if column in points:
            points[column] = pd.to_numeric(points[column], errors="coerce")
            points[column] = points[column].replace(
                [float("inf"), float("-inf")], pd.NA
            )

    if "area_m2" in points and "price_usd" in points:
        valid = (
            points["area_m2"].gt(0)
            & points["price_usd"].gt(0)
            & points["area_m2"].notna()
            & points["price_usd"].notna()
        )
        points = points.loc[valid]
    else:
        points = points.iloc[0:0]

    figure = px.scatter(
        points,
        x="area_m2",
        y="price_usd",
        color="property_type" if "property_type" in points else None,
        hover_data={
            "area_m2": ":,.1f",
            "price_usd": ":$,.0f",
            "property_type": True,
            "state": True,
        },
        render_mode="auto",
        opacity=0.7,
        title="Property area versus listing price",
        labels={
            "area_m2": "Property area (m²)",
            "price_usd": "Listing price (USD)",
            "property_type": "Property type",
        },
        template=CHART_TEMPLATE,
    )
    figure.update_yaxes(
        type="log" if log_price_scale else "linear",
        tickprefix="$",
        tickformat="~s" if log_price_scale else ",.0f",
        title_text="Listing price (USD; logarithmic scale)"
        if log_price_scale
        else "Listing price (USD)",
    )
    figure.update_layout(margin={"l": 8, "r": 16, "t": 56, "b": 8})
    return figure


def geographic_map_chart(dataframe: pd.DataFrame) -> go.Figure:
    center = {
        "lat": float(dataframe["lat"].median()),
        "lon": float(dataframe["lon"].median()),
    }
    figure = px.scatter_map(
        dataframe,
        lat="lat",
        lon="lon",
        color="property_type",
        hover_name="state",
        hover_data={
            "lat": False,
            "lon": False,
            "property_type": True,
            "area_m2": ":,.1f",
            "price_usd": ":$,.0f",
            "price_per_m2": ":$,.2f",
        },
        zoom=3,
        center=center,
        map_style="open-street-map",
        opacity=0.7,
        size_max=9,
        title="Available property locations",
        labels={
            "property_type": "Property type",
            "area_m2": "Area (m²)",
            "price_usd": "Listing price (USD)",
            "price_per_m2": "Price per m² (USD)",
        },
        template=CHART_TEMPLATE,
    )
    figure.update_layout(margin={"l": 8, "r": 8, "t": 56, "b": 8})
    return figure


def state_median_chart(
    dataframe: pd.DataFrame,
    *,
    metric: str,
) -> go.Figure:
    metric_settings = {
        "Median listing price (USD)": (
            "median_price_usd",
            "Median listing price by state",
            "$",
        ),
        "Median price per m² (USD)": (
            "median_price_per_m2",
            "Median price per square meter by state",
            "$",
        ),
    }
    if metric not in metric_settings:
        raise ValueError(f"Unsupported state comparison metric: {metric}")
    value_column, title, prefix = metric_settings[metric]
    chart_data = dataframe.dropna(subset=[value_column]).sort_values(
        value_column, ascending=True
    )
    figure = go.Figure(
        go.Bar(
            x=chart_data[value_column],
            y=chart_data["state"],
            orientation="h",
            marker_color=CHART_COLOR,
            customdata=chart_data[["listings"]].to_numpy(),
            hovertemplate=(
                "%{y}<br>"
                + metric
                + ": %{x:$,.0f}<br>Listings: %{customdata[0]:,}<extra></extra>"
            ),
            text=chart_data["listings"],
            textposition="outside",
        )
    )
    figure.update_layout(
        title=title,
        xaxis_title=metric,
        yaxis_title="State",
        xaxis={"tickprefix": prefix, "tickformat": "~s"},
        margin={"l": 8, "r": 32, "t": 56, "b": 8},
        template=CHART_TEMPLATE,
        showlegend=False,
    )
    return figure


def nested_model_r_squared_chart(dataframe: pd.DataFrame) -> go.Figure:
    figure = go.Figure(
        go.Bar(
            x=dataframe["model"],
            y=dataframe["r_squared"],
            marker_color=CHART_COLOR,
            customdata=dataframe[["observations", "formula"]].to_numpy(),
            text=dataframe["r_squared"].map(lambda value: f"{value:.3f}"),
            textposition="outside",
            hovertemplate=(
                "%{x}<br>R²: %{y:.4f}<br>Observations: %{customdata[0]:,}"
                "<br>Formula: %{customdata[1]}<extra></extra>"
            ),
        )
    )
    maximum = float(dataframe["r_squared"].max()) if not dataframe.empty else 1.0
    figure.update_layout(
        title="Nested-model R² comparison",
        xaxis_title="Model specification",
        yaxis_title="R²",
        yaxis={"range": [0, min(1.0, maximum * 1.2)]},
        template=CHART_TEMPLATE,
        margin={"l": 8, "r": 16, "t": 56, "b": 8},
        showlegend=False,
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
