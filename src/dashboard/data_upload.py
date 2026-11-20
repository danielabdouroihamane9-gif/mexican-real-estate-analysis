"""Shared per-session upload workflow for dashboard source datasets."""

import hashlib

import pandas as pd
import streamlit as st

from src.dashboard import data_loader
from src.dashboard.data_loader import DashboardDataError, SOURCE_REQUIRED_COLUMNS
from src.real_estate_analysis import SOURCE_FILENAMES


_UPLOAD_LABELS = ("Dataset 1", "Dataset 2", "Dataset 3")
_UPLOADED_DATA_KEY = "_dashboard_uploaded_datasets"
_UPLOAD_GENERATION_KEY = "_dashboard_upload_generation"


def _upload_state_keys(index: int) -> tuple[str, str, str]:
    generation = st.session_state.get(_UPLOAD_GENERATION_KEY, 0)
    return (
        f"dashboard_source_file_{generation}_{index}",
        f"_dashboard_source_{index}_contents",
        f"_dashboard_source_{index}_name",
    )


def _remember_upload(index: int) -> None:
    widget_key, contents_key, name_key = _upload_state_keys(index)
    uploaded_file = st.session_state.get(widget_key)
    st.session_state[contents_key] = (
        uploaded_file.getvalue() if uploaded_file is not None else None
    )
    st.session_state[name_key] = (
        uploaded_file.name if uploaded_file is not None else None
    )
    st.session_state.pop(_UPLOADED_DATA_KEY, None)


def _clear_uploaded_sources() -> None:
    for index in range(1, len(SOURCE_FILENAMES) + 1):
        _, contents_key, name_key = _upload_state_keys(index)
        st.session_state[contents_key] = None
        st.session_state[name_key] = None
    st.session_state.pop(_UPLOADED_DATA_KEY, None)
    st.session_state[_UPLOAD_GENERATION_KEY] += 1


def _uploaded_signature(contents: tuple[bytes, ...]) -> tuple[bytes, ...]:
    return tuple(hashlib.sha256(source).digest() for source in contents)


def _process_session_uploads(
    contents: tuple[bytes, ...],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    signature = _uploaded_signature(contents)
    cached = st.session_state.get(_UPLOADED_DATA_KEY)
    if cached is not None and cached[0] == signature:
        return cached[1], cached[2]

    analytical, geospatial = data_loader.load_uploaded_datasets(contents)
    st.session_state[_UPLOADED_DATA_KEY] = (
        signature,
        analytical,
        geospatial,
    )
    return analytical, geospatial


def load_dashboard_datasets() -> tuple[pd.DataFrame, pd.DataFrame] | None:
    """Render shared source uploaders and return the active dashboard datasets.

    Uploaded source bytes and their processed dataframes are kept in the user's
    Streamlit session state; they are not written to the repository or disk.
    Local processed datasets remain available as a development fallback.
    """

    st.session_state.setdefault(_UPLOAD_GENERATION_KEY, 0)
    with st.sidebar:
        st.header("Dashboard data")
        st.caption(
            "Upload all three original source CSVs. The geospatial dataset is "
            "derived automatically."
        )
        st.caption("Required columns are shown below each upload control.")
        st.caption(
            "Uploads are sent to this app server and retained only in the "
            "current session. Use files only when your terms permit processing "
            "through this hosted app."
        )

        for index, dataset_label in enumerate(_UPLOAD_LABELS, start=1):
            widget_key, contents_key, name_key = _upload_state_keys(index)
            required_columns = ", ".join(
                sorted(SOURCE_REQUIRED_COLUMNS[index - 1])
            )
            uploaded_file = st.file_uploader(
                f"{dataset_label}: {SOURCE_FILENAMES[index - 1]}",
                type=["csv"],
                key=widget_key,
                help=f"Required columns: {required_columns}",
                on_change=_remember_upload,
                args=(index,),
            )
            if uploaded_file is not None:
                st.session_state[contents_key] = uploaded_file.getvalue()
                st.session_state[name_key] = uploaded_file.name

        contents = tuple(
            st.session_state.get(_upload_state_keys(index)[1])
            for index in range(1, len(SOURCE_FILENAMES) + 1)
        )
        st.button(
            "Clear uploaded sources",
            key="clear_dashboard_uploads",
            on_click=_clear_uploaded_sources,
            disabled=not any(content is not None for content in contents),
            icon=":material/delete_sweep:",
            width="stretch",
        )
        names = tuple(
            st.session_state.get(_upload_state_keys(index)[2])
            for index in range(1, len(SOURCE_FILENAMES) + 1)
        )
        supplied_count = sum(content is not None for content in contents)

        if supplied_count:
            missing = [
                SOURCE_FILENAMES[index]
                for index, content in enumerate(contents)
                if content is None
            ]
            if missing:
                st.warning(
                    f"Upload the remaining source file(s): {', '.join(missing)}.",
                    title="Upload incomplete",
                )
                return None

            complete_contents = tuple(
                content for content in contents if isinstance(content, bytes)
            )
            if len(complete_contents) != len(SOURCE_FILENAMES):
                st.error(
                    "One or more uploaded files could not be read from the "
                    "current session. Re-upload all three source CSVs.",
                    title="Upload incomplete",
                )
                return None

            try:
                analytical, geospatial = _process_session_uploads(complete_contents)
            except DashboardDataError as exc:
                st.error(str(exc), title="Uploaded data could not be used")
                return None

            st.success("Uploaded sources are validated and ready for analysis.")
            st.caption(
                "The analytical and geospatial datasets are derived in memory "
                "for this session; no data files are saved."
            )
            st.caption(
                "Active files: " + ", ".join(str(name) for name in names)
            )
            return analytical, geospatial

        try:
            analytical, geospatial = data_loader.load_processed_datasets()
        except DashboardDataError as exc:
            st.info(
                "No dataset is loaded yet. Upload all three source CSVs above "
                "to enable the analytical pages.",
                title="Data required",
            )
            st.caption(f"Local processed data is unavailable: {exc}")
            return None

        st.caption("Using local processed datasets.")
        return analytical, geospatial
