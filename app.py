"""PeakStay: find CAI shelters by region and municipality."""

from pathlib import Path

import streamlit as st

from peakstay.api import fetch_all_shelters, load_raw, save_raw
from peakstay.cleaning import build_dataframe, clean_altitude,keep_staffed_open, normalize_text
from peakstay.recommender import recommend

RAW_PATH = Path("data/raw/shelters.json")


@st.cache_data
def load_data():
    """Load the shelters (download them the first time) and clean them."""
    if RAW_PATH.exists():
        shelters = load_raw(RAW_PATH)
    else:
        shelters = fetch_all_shelters()
        save_raw(shelters, RAW_PATH)

    df = build_dataframe(shelters)
    df = clean_altitude(df)
    df = keep_staffed_open(df)
    df = normalize_text(df)
    return df


df = load_data()

st.title("PeakStay")
st.caption("A recommender for CAI mountain shelters")

# 1) region: a sorted list of the regions in the data
regions = sorted(df["region_geo"].dropna().unique())
region = st.selectbox("Region", regions)

# 2) municipality: only those of the chosen region, optional
municipalities = sorted(df.loc[df["region_geo"] == region,"municipality_geo"].dropna().unique())
municipality = st.selectbox(
    "Municipality (optional)", municipalities, index=None, placeholder="Any"
)

# 3) altitude: optional
use_altitude = st.checkbox("I have a preferred altitude")
target = None
if use_altitude:
    target = st.slider(
        "Altitude (m)", min_value=500, max_value=5000, value=2000, step=50
        )                      # the min and max are: 611, 4554 m


# 4) results
if st.button("Find shelters"):
    result = recommend(df, region, municipality, target)
    if result.empty:
        st.warning("No shelters found.")
    else:
        st.dataframe(result[["title", "municipality_geo", "locality_geo",
                             "massif_geo", "altitude_geo"]])