"""PeakStay: find CAI shelters by region and municipality."""

import math

import pandas as pd
import streamlit as st

from peakstay.cleaning import keep_staffed_open
from peakstay.data import load_all_shelters
from peakstay.recommender import recommend

ALTITUDE_STEP = 50
SHELTERS_PER_PAGE = 3
SEASON_ORDER = [
    "year-round",
    "summer",
    "winter",
    "weekends",
    "christmas period",
    "spring ski mountaineering",
]
CATEGORY_HELP = (
    "CAI shelter categories (A to E) classify altitude and accessibility: "
    "A = easily accessible near roads/villages; "
    "B = reachable via marked trails; "
    "C = high-altitude mountain huts; "
    "D/E = remote or mountaineering terrain."
)


# Extra top padding so the Streamlit header bar does not overlap the title
PAGE_CSS = """
<style>
    .block-container { padding-top: 3rem; }
</style>
"""


# --- HELPERS ------------------------------------------------------------------


@st.cache_data
def load_staffed_shelters() -> pd.DataFrame:
    """Load all shelters and keep only the staffed ones that are open."""
    return keep_staffed_open(load_all_shelters())


def has_value(value) -> bool:
    """Return True if `value` is neither missing nor an empty string/collection."""
    if isinstance(value, (set, list, tuple)):
        return len(value) > 0
    return pd.notna(value) and str(value).strip() != ""


def format_value(value) -> str:
    """Format collections as clean comma-separated strings."""
    if isinstance(value, (set, list, tuple)):
        return ", ".join(str(v).capitalize() for v in sorted(value) if v)
    return str(value)


def write_fields(fields: dict) -> None:
    """Write 'label: value' lines, skipping missing values."""
    lines = [
        f"**{label}:** {format_value(value)}"
        for label, value in fields.items()
        if has_value(value)
    ]
    st.markdown("  \n".join(lines))



def reset_filters() -> None:
    """Reset optional filters and discarded shelters when changing region."""
    st.session_state["selected_municipality"] = None
    st.session_state["use_altitude"] = False
    st.session_state.pop("altitude_range", None)
    st.session_state["use_season"] = False
    st.session_state["selected_seasons"] = []
    st.session_state["discarded_indices"] = []


def render_filters(df: pd.DataFrame):
    """Render the selection criteria and return the chosen values."""
    st.subheader("Selection Criteria")

    # 1) Region: resets all other filters when changed
    region = st.selectbox(
        "Region",
        sorted(df["region_geo"].dropna().unique()),
        key="selected_region",
        on_change=reset_filters,
    )
    region_df = df[df["region_geo"] == region]

    # 2) Municipality: only those of the chosen region, optional
    municipality = st.selectbox(
        "Municipality (optional)",
        sorted(region_df["municipality_geo"].dropna().unique()),
        index=None,
        placeholder="Any",
        key="selected_municipality",
    )

    # 3) Altitude range: optional
    altitude_min = altitude_max = None
    if st.checkbox("I have a preferred altitude", key="use_altitude"):
        low = math.floor(region_df["altitude_geo"].min() / ALTITUDE_STEP) * ALTITUDE_STEP
        high = math.ceil(region_df["altitude_geo"].max() / ALTITUDE_STEP) * ALTITUDE_STEP
        altitude_min, altitude_max = st.slider(
            "Altitude range (m)",
            min_value=low,
            max_value=high,
            value=(low, high),
            step=ALTITUDE_STEP,
            key="altitude_range",
        )

    # 4) Opening season: optional, multiple unless "year-round" is selected
    seasons = []
    if st.checkbox("I have a preferred opening season", key="use_season"):
        present = {s for seasons_set in df["seasons"].dropna() for s in seasons_set}
        available_seasons = sorted(
            present,
            key=lambda s: SEASON_ORDER.index(s) if s in SEASON_ORDER else len(SEASON_ORDER),
        )

        current_selection = st.session_state.get("selected_seasons", [])
        if "year-round" in current_selection:
            if len(current_selection) > 1:
                st.session_state["selected_seasons"] = ["year-round"]
            options = ["year-round"]
        else:
            options = available_seasons

        seasons = st.multiselect(
            "Opening season",
            options=options,
            format_func=lambda s: s.capitalize(),
            placeholder="Any",
            key="selected_seasons",
        )
    else:
        st.session_state.pop("selected_seasons", None)

    find_clicked = st.button("Find shelters")
    return region, municipality, altitude_min, altitude_max, seasons, find_clicked


def render_shelter_card(idx, row: pd.Series, has_more: bool) -> None:
    """Render one shelter: photo, main details, replace button and extra info."""
    with st.container(border=True):
        col_img, col_info, col_action = st.columns([1.2, 2.5, 1], vertical_alignment="center")

        with col_img:
            img = row.get("image_url")
            if isinstance(img, str) and img.startswith("http"):
                st.image(img.replace("http://", "https://", 1), width="stretch")
            else:
                st.caption("No photo")

        with col_info:
            st.subheader(row["alias"])
            write_fields({
                "Locality": row.get("locality_geo"),
                "Municipality": row.get("municipality_geo"),
                "Province": row.get("province_geo"),
                "Altitude": f"{int(row['altitude_geo'])} m",
                "Opening": row.get("seasons"),
            })

        with col_action:
            if st.button("Load another shelter", key=f"replace_{idx}",
                         disabled=not has_more, width="stretch"):
                st.session_state.discarded_indices.append(idx)
                st.rerun()

        with st.expander("More info"):
            write_fields({
                "Official name": row.get("title"),
            })

            cat = row.get("category")
            if has_value(cat):
                st.markdown(
                    f"**Category:** {cat} "
                    f"<span title='{CATEGORY_HELP}' style='cursor:help; color:#6b7280;'>ⓘ</span>",
                    unsafe_allow_html=True,
                )

            write_fields({
                "Website": row.get("webAddress_contact"),
                "Region": row.get("region_geo"),
                "Massif": row.get("massif_geo"),
            })



# --- PAGE ---------------------------------------------------------------------

st.markdown(PAGE_CSS, unsafe_allow_html=True)

df = load_staffed_shelters()

st.title("PeakStay")
st.caption("A recommender for CAI mountain shelters")

col_filters, col_results = st.columns([1, 2], gap="large")

with col_filters:
    region, municipality, alt_min, alt_max, seasons, find_clicked = render_filters(df)

with col_results:
    st.subheader("Recommended Shelters")

    # Computed on every rerun (outside the button) so filters persist
    result = recommend(df, region, municipality, alt_min, alt_max, seasons)

    # Indices of shelters the user has already replaced
    if "discarded_indices" not in st.session_state or find_clicked:
        st.session_state.discarded_indices = []

    available = result[~result.index.isin(st.session_state.discarded_indices)]
    to_show = available.head(SHELTERS_PER_PAGE)

    if available.empty:
        st.warning("No more shelters available matching your criteria.")
    else:
        st.write(f"Showing {len(to_show)} recommended shelters ({len(available)} remaining):")
        has_more = len(available) > len(to_show)
        for idx, row in to_show.iterrows():
            render_shelter_card(idx, row, has_more)
