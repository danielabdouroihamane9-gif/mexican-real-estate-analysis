"""Reusable calculations for geographic market analysis."""

import pandas as pd


STATE_SUMMARY_COLUMNS = [
    "state",
    "listings",
    "median_price_usd",
    "median_price_per_m2",
    "median_area_m2",
]


def valid_coordinate_mask(dataframe: pd.DataFrame) -> pd.Series:
    """Identify rows with finite latitude and longitude inside valid bounds."""

    missing_columns = {"lat", "lon"}.difference(dataframe.columns)
    if missing_columns:
        raise ValueError(
            "Coordinate data is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    latitude = pd.to_numeric(dataframe["lat"], errors="coerce")
    longitude = pd.to_numeric(dataframe["lon"], errors="coerce")
    valid_latitude = latitude.between(-90, 90).fillna(False)
    valid_longitude = longitude.between(-180, 180).fillna(False)
    return valid_latitude & valid_longitude


def summarize_states(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calculate listing counts and medians for every state present."""

    required_columns = {
        "state",
        "price_usd",
        "price_per_m2",
        "area_m2",
    }
    missing_columns = required_columns.difference(dataframe.columns)
    if missing_columns:
        raise ValueError(
            "State summary is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    states = dataframe["state"].astype("string")
    has_state = states.notna() & states.str.strip().ne("")
    has_state = has_state.fillna(False)
    if not has_state.any():
        return pd.DataFrame(columns=STATE_SUMMARY_COLUMNS)

    working = dataframe.loc[has_state].copy()
    working["state"] = states.loc[has_state].str.strip()
    for column in ("price_usd", "price_per_m2", "area_m2"):
        values = pd.to_numeric(working[column], errors="coerce")
        values = values.replace([float("inf"), float("-inf")], pd.NA)
        working[column] = values.where(values.gt(0))

    summary = (
        working.groupby("state", dropna=True)
        .agg(
            listings=("state", "size"),
            median_price_usd=("price_usd", "median"),
            median_price_per_m2=("price_per_m2", "median"),
            median_area_m2=("area_m2", "median"),
        )
        .reset_index()
    )
    return summary.loc[:, STATE_SUMMARY_COLUMNS].sort_values(
        ["median_price_usd", "state"],
        ascending=[False, True],
        na_position="last",
        ignore_index=True,
    )
