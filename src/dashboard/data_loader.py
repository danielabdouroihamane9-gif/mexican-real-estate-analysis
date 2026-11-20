"""Load, validate, and prepare the dashboard's source and processed datasets."""

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from src.real_estate_analysis import (
    PROCESSED_DATA_DIR,
    SOURCE_FILENAMES,
    UNRESOLVED_MXN_TO_USD_RATE,
    build_processed_datasets_from_frames,
)


ANALYTICAL_FILENAME = "mexico-real-combined-clean.csv"
GEOSPATIAL_FILENAME = "mexico-real-combined-geospatial.csv"

ANALYTICAL_COLUMNS = frozenset(
    {
        "source_dataset",
        "property_type",
        "state",
        "area_m2",
        "price_usd",
        "price_mxn",
        "conversion_rate_mxn_per_usd",
        "price_per_m2",
    }
)
GEOSPATIAL_COLUMNS = ANALYTICAL_COLUMNS | {"lat", "lon"}
NUMERIC_COLUMNS = frozenset(
    {
        "area_m2",
        "price_usd",
        "price_mxn",
        "conversion_rate_mxn_per_usd",
        "price_per_m2",
        "lat",
        "lon",
    }
)
SOURCE_REQUIRED_COLUMNS = (
    frozenset({"property_type", "state", "lat", "lon", "area_m2", "price_usd"}),
    frozenset({"property_type", "state", "lat", "lon", "area_m2", "price_mxn"}),
    frozenset(
        {
            "property_type",
            "place_with_parent_names",
            "lat-lon",
            "area_m2",
            "price_usd",
        }
    ),
)


class DashboardDataError(ValueError):
    """Raised when dashboard source data cannot be used safely."""


def _validate_dataset(path: Path, required_columns: frozenset[str]) -> pd.DataFrame:
    if not path.is_file():
        raise DashboardDataError(
            f"Processed dataset not found: {path}. "
            "Run `python -m src.real_estate_analysis` to generate it."
        )

    try:
        dataframe = pd.read_csv(path, encoding="utf-8")
    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
    ) as exc:
        raise DashboardDataError(f"Could not read processed dataset {path}: {exc}") from exc

    if dataframe.empty:
        raise DashboardDataError(f"Processed dataset is empty: {path}")

    missing_columns = sorted(required_columns.difference(dataframe.columns))
    if missing_columns:
        raise DashboardDataError(
            f"Processed dataset {path} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    invalid_numeric = sorted(
        column
        for column in required_columns.intersection(NUMERIC_COLUMNS)
        if not pd.api.types.is_numeric_dtype(dataframe[column])
    )
    if invalid_numeric:
        raise DashboardDataError(
            f"Processed dataset {path} has non-numeric columns where numeric values "
            f"are required: {', '.join(invalid_numeric)}"
        )

    return dataframe


@st.cache_data(show_spinner=False)
def load_processed_datasets(
    analytical_path: str | Path | None = None,
    geospatial_path: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and validate the analytical and geospatial processed datasets.

    Paths default to the repository's ``data/processed`` directory and can be
    overridden to make validation behavior easy to test with temporary files.
    """

    analytical = Path(analytical_path) if analytical_path else PROCESSED_DATA_DIR / ANALYTICAL_FILENAME
    geospatial = Path(geospatial_path) if geospatial_path else PROCESSED_DATA_DIR / GEOSPATIAL_FILENAME
    return (
        _validate_dataset(analytical, ANALYTICAL_COLUMNS),
        _validate_dataset(geospatial, GEOSPATIAL_COLUMNS),
    )


def load_uploaded_datasets(
    source_contents: tuple[bytes, ...],
    mxn_rate: float = UNRESOLVED_MXN_TO_USD_RATE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate and process the three uploaded raw source CSVs in memory."""

    if len(source_contents) != len(SOURCE_FILENAMES):
        raise DashboardDataError(
            f"Upload exactly these {len(SOURCE_FILENAMES)} source CSV files: "
            f"{', '.join(SOURCE_FILENAMES)}."
        )

    source_frames: list[pd.DataFrame] = []
    for filename, required_columns, contents in zip(
        SOURCE_FILENAMES,
        SOURCE_REQUIRED_COLUMNS,
        source_contents,
        strict=True,
    ):
        if not contents:
            raise DashboardDataError(
                f"{filename} is empty. Upload the original CSV with its header "
                "and data rows."
            )
        try:
            dataframe = pd.read_csv(BytesIO(contents), encoding="utf-8-sig")
        except (
            OSError,
            UnicodeDecodeError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
        ) as exc:
            raise DashboardDataError(
                f"Could not read {filename} as a CSV file: {exc}. "
                "Check the file encoding and upload the original CSV."
            ) from exc

        missing_columns = sorted(required_columns.difference(dataframe.columns))
        if missing_columns:
            raise DashboardDataError(
                f"{filename} is missing required columns: "
                f"{', '.join(missing_columns)}. Upload the matching source CSV, "
                "not a processed output."
            )
        if dataframe.empty:
            raise DashboardDataError(
                f"{filename} has a header but no data rows. Upload a non-empty "
                "source CSV."
            )
        source_frames.append(dataframe)

    try:
        analytical, geospatial = build_processed_datasets_from_frames(
            source_frames,
            mxn_rate=mxn_rate,
        )
    except ValueError as exc:
        raise DashboardDataError(f"Could not process the uploaded CSVs: {exc}") from exc

    if analytical.empty:
        raise DashboardDataError(
            "The uploaded CSVs contained no usable property listings. Check that "
            "property type and state are present and that area and USD price are "
            "valid and positive."
        )

    return analytical, geospatial

