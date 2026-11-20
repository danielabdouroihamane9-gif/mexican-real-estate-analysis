"""Reusable cleaning helpers for the Mexican real estate analysis."""

import json
from pathlib import Path
import re
import unicodedata
from collections.abc import Sequence

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

# The project documentation does not identify the source or date of this
# conversion assumption. It is kept explicit and is not presented as historical
# market exchange-rate data.
UNRESOLVED_MXN_TO_USD_RATE = 19.0
SOURCE_FILENAMES = (
    "mexico-real-estate-1.csv",
    "mexico-real-estate-2.csv",
    "mexico-real-estate-3.csv",
)


def _validate_mxn_rate(mxn_rate: float) -> None:
    if mxn_rate is None or mxn_rate <= 0:
        raise ValueError("MXN per USD conversion rate must be positive")


def _read_source(source: Path | pd.DataFrame) -> pd.DataFrame:
    if isinstance(source, pd.DataFrame):
        return source.copy()
    return pd.read_csv(source, encoding="utf-8")


def parse_usd_price(value: object) -> float:
    if pd.isna(value):
        return float("nan")
    return float(re.sub(r"[,$]", "", str(value)))


def parse_lat_lon(value: object) -> tuple[float, float]:
    if pd.isna(value):
        return float("nan"), float("nan")
    parts = str(value).split(",")
    if len(parts) != 2:
        return float("nan"), float("nan")
    try:
        return float(parts[0].strip()), float(parts[1].strip())
    except ValueError:
        return float("nan"), float("nan")


def state_from_place(value: object) -> str:
    if pd.isna(value):
        return float("nan")
    parts = [part for part in str(value).split("|") if part]
    return parts[1] if len(parts) >= 2 else float("nan")


def normalize_text(value: object) -> object:
    if pd.isna(value):
        return value
    return unicodedata.normalize("NFC", str(value).strip())


def find_cross_source_overlaps(
    cross_source: pd.DataFrame,
) -> dict:
    key_columns = ["property_type", "state", "area_m2", "price_usd"]
    valid = (
        cross_source["property_type"].notna()
        & cross_source["state"].notna()
        & cross_source["area_m2"].gt(0)
        & cross_source["price_usd"].gt(0)
        & cross_source["source_dataset"].notna()
    )
    candidates = cross_source.loc[valid, key_columns + ["source_dataset"]].copy()

    source_counts = candidates.groupby(key_columns)["source_dataset"].nunique()
    matching_keys = source_counts[source_counts >= 2].index

    if len(matching_keys) == 0:
        matching = pd.DataFrame(columns=key_columns + ["source_dataset"])
    else:
        matching_index = pd.MultiIndex.from_tuples(
            list(matching_keys),
            names=key_columns,
        )
        candidate_index = pd.MultiIndex.from_frame(candidates[key_columns])
        is_matching_key = candidate_index.isin(matching_index)
        matching = candidates.loc[is_matching_key].copy()

    sources = sorted(matching["source_dataset"].dropna().unique().tolist())
    return {
        "distinct_matching_key_count": int(len(matching_keys)),
        "rows_belonging_to_matching_keys": int(len(matching)),
        "source_datasets_involved": sources,
    }


def _standardized_core(df: pd.DataFrame, source_dataset: str) -> pd.DataFrame:
    result = df.copy()
    result["source_dataset"] = source_dataset
    result["property_type"] = result["property_type"].map(normalize_text).astype("string")
    result["state"] = result["state"].map(normalize_text).astype("string")
    result["area_m2"] = pd.to_numeric(result["area_m2"], errors="coerce")
    result["price_usd"] = pd.to_numeric(result["price_usd"], errors="coerce")
    result["price_mxn"] = pd.to_numeric(
        result.get("price_mxn", pd.Series(float("nan"), index=result.index)),
        errors="coerce",
    )
    if "conversion_rate_mxn_per_usd" not in result:
        result["conversion_rate_mxn_per_usd"] = float("nan")
    else:
        result["conversion_rate_mxn_per_usd"] = pd.to_numeric(
            result["conversion_rate_mxn_per_usd"], errors="coerce"
        )
    return result


def clean_dataset_1(path: Path | pd.DataFrame, mxn_rate: float = UNRESOLVED_MXN_TO_USD_RATE) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = _read_source(path)
    df["price_usd"] = pd.to_numeric(df["price_usd"].map(parse_usd_price), errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["area_m2"] = pd.to_numeric(df["area_m2"], errors="coerce")
    df["price_mxn"] = float("nan")
    df["conversion_rate_mxn_per_usd"] = float("nan")
    df = _standardized_core(df, "mexico-real-estate-1.csv")
    return analytical_dataframe(df), geospatial_dataframe(df)


def clean_dataset_2(path: Path | pd.DataFrame, mxn_rate: float = UNRESOLVED_MXN_TO_USD_RATE) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = _read_source(path)
    df["price_mxn"] = pd.to_numeric(df["price_mxn"], errors="coerce")
    df["price_usd"] = df["price_mxn"] / mxn_rate
    df["conversion_rate_mxn_per_usd"] = mxn_rate
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["area_m2"] = pd.to_numeric(df["area_m2"], errors="coerce")
    df = _standardized_core(df, "mexico-real-estate-2.csv")
    return analytical_dataframe(df), geospatial_dataframe(df)


def clean_dataset_3(path: Path | pd.DataFrame, mxn_rate: float = UNRESOLVED_MXN_TO_USD_RATE) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = _read_source(path)
    df["state"] = df["place_with_parent_names"].map(state_from_place)
    coordinates = df["lat-lon"].map(parse_lat_lon)
    df["lat"] = coordinates.map(lambda pair: pair[0])
    df["lon"] = coordinates.map(lambda pair: pair[1])
    df["price_usd"] = pd.to_numeric(df["price_usd"].map(parse_usd_price), errors="coerce")
    df["area_m2"] = pd.to_numeric(df["area_m2"], errors="coerce")
    df["price_mxn"] = float("nan")
    df["conversion_rate_mxn_per_usd"] = float("nan")
    df = _standardized_core(df, "mexico-real-estate-3.csv")
    return analytical_dataframe(df), geospatial_dataframe(df)


def analytical_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "source_dataset", "property_type", "state", "area_m2", "price_usd",
        "price_mxn", "conversion_rate_mxn_per_usd",
    ]
    result = (
        df.loc[:, columns]
        .assign(
            property_type=lambda x: x["property_type"].map(normalize_text).astype("string"),
            state=lambda x: x["state"].map(normalize_text).astype("string"),
        )
        .loc[
            lambda x:
            x["property_type"].notna()
            & x["state"].notna()
            & x["area_m2"].gt(0)
            & x["price_usd"].gt(0)
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    result["price_per_m2"] = result["price_usd"] / result["area_m2"]
    return result


def geospatial_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "source_dataset", "property_type", "state", "lat", "lon", "area_m2",
        "price_usd", "price_mxn", "conversion_rate_mxn_per_usd",
    ]
    result = (
        df.loc[:, columns]
        .assign(
            property_type=lambda x: x["property_type"].map(normalize_text).astype("string"),
            state=lambda x: x["state"].map(normalize_text).astype("string"),
        )
        .loc[
            lambda x:
            x["property_type"].notna()
            & x["state"].notna()
            & x["area_m2"].gt(0)
            & x["price_usd"].gt(0)
            & x["lat"].between(-90, 90)
            & x["lon"].between(-180, 180)
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    result["price_per_m2"] = result["price_usd"] / result["area_m2"]
    return result


def _build_datasets_from_frames(
    source_frames: Sequence[pd.DataFrame],
    mxn_rate: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    _validate_mxn_rate(mxn_rate)
    if len(source_frames) != len(SOURCE_FILENAMES):
        raise ValueError(
            f"Exactly {len(SOURCE_FILENAMES)} source datasets are required"
        )

    clean_parts = []
    geo_parts = []
    audit_sources = []
    cleaners = (clean_dataset_1, clean_dataset_2, clean_dataset_3)
    standardized_parts = []
    for index, (filename, raw, cleaner) in enumerate(
        zip(SOURCE_FILENAMES, source_frames, cleaners, strict=True),
        start=1,
    ):
        clean, geo = cleaner(raw, mxn_rate=mxn_rate)
        clean_parts.append(clean)
        geo_parts.append(geo)

        exact_raw_duplicates = int(raw.duplicated().sum())
        if index == 1:
            standardized = raw.copy()
            standardized["property_type"] = standardized["property_type"].map(normalize_text)
            standardized["state"] = standardized["state"].map(normalize_text)
            standardized["area_m2"] = pd.to_numeric(standardized["area_m2"], errors="coerce")
            standardized["price_usd"] = standardized["price_usd"].map(parse_usd_price)
        elif index == 2:
            standardized = raw.copy()
            standardized["property_type"] = standardized["property_type"].map(normalize_text)
            standardized["state"] = standardized["state"].map(normalize_text)
            standardized["area_m2"] = pd.to_numeric(standardized["area_m2"], errors="coerce")
            standardized["price_mxn"] = pd.to_numeric(standardized["price_mxn"], errors="coerce")
            standardized["price_usd"] = standardized["price_mxn"] / mxn_rate
        else:
            standardized = raw.copy()
            standardized["property_type"] = standardized["property_type"].map(normalize_text)
            standardized["state"] = standardized["place_with_parent_names"].map(state_from_place)
            standardized["area_m2"] = pd.to_numeric(standardized["area_m2"], errors="coerce")
            standardized["price_usd"] = standardized["price_usd"].map(parse_usd_price)

        standardized["source_dataset"] = filename
        standardized_parts.append(standardized)
        key_columns = ["property_type", "state", "area_m2", "price_usd"]
        valid_mask = (
            standardized["property_type"].notna()
            & standardized["state"].notna()
            & standardized["area_m2"].gt(0)
            & standardized["price_usd"].gt(0)
        )
        audit_sources.append({
            "source_dataset": filename,
            "raw_row_count": int(len(raw)),
            "raw_exact_duplicate_rows": exact_raw_duplicates,
            "invalid_or_missing_core_rows": int((~valid_mask).sum()),
            "rows_before_within_source_duplicate_removal": int(valid_mask.sum()),
            "duplicate_standardized_keys_removed_within_source": int(
                standardized.loc[valid_mask, key_columns].duplicated().sum()
            ),
            "rows_after_cleaning": int(clean.shape[0]),
        })

    clean = pd.concat(clean_parts, ignore_index=True).drop_duplicates().reset_index(drop=True)
    geospatial = pd.concat(geo_parts, ignore_index=True).drop_duplicates().reset_index(drop=True)

    cross_source = pd.concat(standardized_parts, ignore_index=True)
    key_columns = ["property_type", "state", "area_m2", "price_usd"]
    overlap_summary = find_cross_source_overlaps(cross_source)

    audit = {
        "currency_assumption": {
            "mxn_per_usd": mxn_rate,
            "historically_verified": False,
            "scope": "Applied only to mexico-real-estate-2.csv",
        },
        "sources": audit_sources,
        "cross_source_potential_overlaps": {
            "method": "Same standardized key in at least two distinct source_dataset values",
            "key": key_columns,
            "distinct_matching_key_count": overlap_summary["distinct_matching_key_count"],
            "rows_belonging_to_matching_keys": overlap_summary["rows_belonging_to_matching_keys"],
            "source_datasets_involved": overlap_summary["source_datasets_involved"],
            "note": "No unique listing identifier is available; matches are not claimed to be the same physical property.",
        },
        "final_counts": {
            "analytical_rows": int(clean.shape[0]),
            "geospatial_rows": int(geospatial.shape[0]),
        },
    }
    return clean, geospatial, audit


def build_processed_datasets_from_frames(
    source_frames: Sequence[pd.DataFrame],
    mxn_rate: float = UNRESOLVED_MXN_TO_USD_RATE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build analytical and geospatial dataframes without writing source data."""

    clean, geospatial, _ = _build_datasets_from_frames(source_frames, mxn_rate)
    return clean, geospatial


def build_processed_datasets(
    mxn_rate: float = UNRESOLVED_MXN_TO_USD_RATE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build and write processed datasets from the repository's raw CSV files."""

    _validate_mxn_rate(mxn_rate)
    source_frames = [
        pd.read_csv(RAW_DATA_DIR / filename, encoding="utf-8")
        for filename in SOURCE_FILENAMES
    ]
    clean, geospatial, audit = _build_datasets_from_frames(source_frames, mxn_rate)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    clean.to_csv(PROCESSED_DATA_DIR / "mexico-real-combined-clean.csv", index=False)
    geospatial.to_csv(
        PROCESSED_DATA_DIR / "mexico-real-combined-geospatial.csv",
        index=False,
    )
    with open(PROCESSED_DATA_DIR / "cleaning_audit.json", "w", encoding="utf-8") as handle:
        json.dump(audit, handle, ensure_ascii=False, indent=2)
    return clean, geospatial


if __name__ == "__main__":
    combined, geospatial = build_processed_datasets()
    print(f"Combined: {combined.shape}")
    print(f"Geospatial: {geospatial.shape}")
