"""Reusable filtering helpers for property listings."""

import pandas as pd


def available_category_values(
    dataframe: pd.DataFrame,
    column: str,
) -> list[object]:
    """Return sorted, non-missing category values that can be selected."""

    if column not in dataframe:
        return []

    values = dataframe[column].dropna().unique().tolist()
    values = [
        value
        for value in values
        if not isinstance(value, str) or value.strip()
    ]
    return sorted(values, key=lambda value: str(value).casefold())


def numeric_range_bounds(
    dataframe: pd.DataFrame,
    column: str,
) -> tuple[float, float] | None:
    """Return the full finite positive range, or None when none is valid."""

    if column not in dataframe:
        return None

    values = pd.to_numeric(dataframe[column], errors="coerce")
    values = values.replace([float("inf"), float("-inf")], pd.NA).dropna()
    values = values[values.gt(0)]
    if values.empty:
        return None
    return float(values.min()), float(values.max())


def filter_properties(
    dataframe: pd.DataFrame,
    *,
    states: list[object] | None = None,
    property_types: list[object] | None = None,
    area_range: tuple[float, float] | None = None,
    price_range: tuple[float, float] | None = None,
) -> pd.DataFrame:
    """Apply all selected filters and return a copy of the matching rows.

    A category selection of ``None`` leaves that category unfiltered; an empty
    selection matches no rows. Numeric ranges are inclusive and exclude values
    that are missing or cannot be parsed as finite numbers.
    """

    mask = pd.Series(True, index=dataframe.index)
    if states is not None:
        if "state" not in dataframe:
            raise KeyError("Cannot filter states: the dataset has no 'state' column.")
        mask &= dataframe["state"].isin(states)

    if property_types is not None:
        if "property_type" not in dataframe:
            raise KeyError(
                "Cannot filter property types: the dataset has no "
                "'property_type' column."
            )
        mask &= dataframe["property_type"].isin(property_types)

    if area_range is not None:
        mask &= _numeric_range_mask(dataframe, "area_m2", area_range)

    if price_range is not None:
        mask &= _numeric_range_mask(dataframe, "price_usd", price_range)

    return dataframe.loc[mask].copy()


def _numeric_range_mask(
    dataframe: pd.DataFrame,
    column: str,
    value_range: tuple[float, float],
) -> pd.Series:
    if column not in dataframe:
        raise KeyError(f"Cannot filter by {column}: the dataset has no '{column}' column.")

    lower, upper = value_range
    if lower > upper:
        raise ValueError(f"The lower {column} bound cannot exceed the upper bound.")

    values = pd.to_numeric(dataframe[column], errors="coerce")
    values = values.replace([float("inf"), float("-inf")], pd.NA)
    return values.gt(0) & values.ge(lower) & values.le(upper)
