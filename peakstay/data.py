"""Shared data loading for the PeakStay app."""

from pathlib import Path

import pandas as pd
import streamlit as st

from peakstay.api import fetch_all_shelters, load_raw, save_raw
from peakstay.cleaning import build_dataframe, normalize_text

RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "shelters.json"


@st.cache_data
def load_all_shelters() -> pd.DataFrame:
    """Load all shelters (download them the first time) and clean them."""
    if RAW_PATH.exists():
        shelters = load_raw(RAW_PATH)
    else:
        shelters = fetch_all_shelters()
        save_raw(shelters, RAW_PATH)

    df = build_dataframe(shelters)
    df = normalize_text(df)
    return df