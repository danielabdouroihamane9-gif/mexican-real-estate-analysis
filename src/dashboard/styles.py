"""Shared visual styling for the Streamlit application."""

import streamlit as st


def apply_dashboard_style() -> None:
    """Apply the dashboard's restrained visual treatment."""

    st.markdown(
        """
        <style>
        .block-container { max-width: 1200px; padding-top: 2rem; }
        [data-testid="stMetric"] {
            background: #f7fafb;
            border: 1px solid #dce7ea;
            border-radius: 0.6rem;
            padding: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

