"""PeakStay: find CAI shelters by region and municipality."""

from pathlib import Path

import streamlit as st

from peakstay.api import fetch_all_shelters, load_raw, save_raw
from peakstay.cleaning import build_dataframe, clean_altitude, keep_staffed_open, normalize_text
from peakstay.recommender import recommend

st.set_page_config(page_title="PeakStay", layout="wide")

# Add extra top padding so the Streamlit header bar does not overlap the title
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 3rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

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

col_filters, col_results = st.columns([1, 2], gap="large")

# --- LEFT COLUMN: FILTERS ---
with col_filters:
    st.subheader("Selection Criteria")

    # 1) region: a sorted list of the regions in the data
    regions = sorted(df["region_geo"].dropna().unique())
    region = st.selectbox("Region", regions)

    # 2) municipality: only those of the chosen region, optional
    municipalities = sorted(df.loc[df["region_geo"] == region, "municipality_geo"].dropna().unique())
    municipality = st.selectbox(
        "Municipality (optional)", municipalities, index=None, placeholder="Any"
    )

    # 3) altitude: optional
    use_altitude = st.checkbox("I have a preferred altitude")
    target = None
    if use_altitude:
        target = st.slider(
            "Altitude (m)", min_value=500, max_value=5000, value=2000, step=50
        )  # the min and max are: 611, 4554 m

    # Search button placed under the filters
    find_clicked = st.button("Find refuges")

# --- RIGHT COLUMN: RESULTS ---
with col_results:
    st.subheader("Recommended Refuges")

    # Calculate filtered results ALWAYS (outside the button block so filters persist on rerun)
    result = recommend(df, region, municipality, target)

    # Initialize list of discarded shelter indices in session state
    if "discarded_indices" not in st.session_state:
        st.session_state.discarded_indices = []

    # Search button resets the discarded list to show the top 3 again
    if find_clicked:
        st.session_state.discarded_indices = []

    # Exclude shelters that the user has already replaced
    available_df = result[~result.index.isin(st.session_state.discarded_indices)]
    total_available = len(available_df)

    if total_available == 0:
        st.warning("No more refuges available matching your criteria.")
    else:
        # Always take the top 3 from the remaining available shelters
        shelters_to_show = available_df.head(3)

        st.write(f"Showing {len(shelters_to_show)} recommended refuges ({total_available} remaining):")

        # Display each shelter in a card with photo, details, action button, and expander
        for idx, row in shelters_to_show.iterrows():
            with st.container(border=True):
                col_img, col_info, col_action = st.columns([1.2, 2.5, 1], vertical_alignment="center")

                with col_img:
                    img = row.get("image_url")
                    if isinstance(img, str) and img.startswith("http"):
                        img = img.replace("http://", "https://", 1)
                        st.image(img, width="stretch")
                    else:
                        st.caption("No photo")

                with col_info:
                    st.subheader(row["alias"])
                    st.markdown(
                        f"**Municipality:** {row['municipality_geo']}  \n"
                        f"**Locality:** {row['locality_geo']}  \n"
                        f"**Massif:** {row['massif_geo']}  \n"
                        f"**Altitude:** {int(row['altitude_geo'])}"
                    )

                with col_action:
                    has_more = total_available > len(shelters_to_show)
                    if st.button("Load another refuge", key=f"replace_{idx}", disabled=not has_more, use_container_width=True):
                        st.session_state.discarded_indices.append(idx)
                        st.rerun()

                # Expandable section with extra text details only
                with st.expander("More info"):
                    st.write(f"**Official name:** {row.get('title', 'N/A')}")
                    st.write(f"**Category:** {row.get('category', 'N/A')}")
                    st.write(f"**Website:** {row.get('webAddress_contact', 'N/A')}")
                    st.write(f"**Region:** {row.get('region_geo', 'N/A')}")
                    st.write(f"**Province:** {row.get('province_geo', 'N/A')}")
                    st.write(f"**Massif:** {row.get('massif_geo', 'N/A')}")
