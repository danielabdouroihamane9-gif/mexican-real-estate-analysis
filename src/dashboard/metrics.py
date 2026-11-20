"""Reusable calculations for the market overview dashboard."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class MarketMetrics:
    total_records: int
    state_count: int
    median_price_usd: float | None
    median_area_m2: float | None
    median_price_per_m2: float | None


def _median_numeric_value(dataframe: pd.DataFrame, column: str) -> float | None:
    if column not in dataframe:
        return None

    values = pd.to_numeric(dataframe[column], errors="coerce")
    values = values.replace([float("inf"), float("-inf")], pd.NA).dropna()
    if values.empty:
        return None
    return float(values.median())


def calculate_market_metrics(dataframe: pd.DataFrame) -> MarketMetrics:
    """Calculate market KPIs from the analytical dataset."""

    state_count = (
        int(
            dataframe.loc[
                _nonempty_category_mask(dataframe["state"]),
                "state",
            ].nunique()
        )
        if "state" in dataframe
        else 0
    )
    return MarketMetrics(
        total_records=len(dataframe),
        state_count=state_count,
        median_price_usd=_median_numeric_value(dataframe, "price_usd"),
        median_area_m2=_median_numeric_value(dataframe, "area_m2"),
        median_price_per_m2=_median_numeric_value(dataframe, "price_per_m2"),
    )


def aggregate_listing_counts(
    dataframe: pd.DataFrame,
    category_column: str,
) -> pd.DataFrame:
    """Count listings by an existing, non-null category value."""

    if category_column not in dataframe:
        return pd.DataFrame(columns=[category_column, "listings"])

    counts = (
        dataframe.loc[_nonempty_category_mask(dataframe[category_column])]
        .groupby(category_column, dropna=True)
        .size()
        .rename("listings")
        .reset_index()
    )
    return counts.sort_values(
        ["listings", category_column],
        ascending=[False, True],
        ignore_index=True,
    )


def aggregate_property_types(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Count listings by property type."""

    return aggregate_listing_counts(dataframe, "property_type")


def aggregate_states(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Count listings by state."""

    return aggregate_listing_counts(dataframe, "state")


def _nonempty_category_mask(values: pd.Series) -> pd.Series:
    nonempty = ~values.map(
        lambda value: isinstance(value, str) and not value.strip()
    )
    return values.notna() & nonempty
