"""Insights page dedicated to CAI bivouacs across Italy and by region."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from peakstay.data import load_all_shelters

ITALY = "Italy"
FOREIGN_REGIONS = ["Savoia Francia", "Svizzera"]
BEDS_COL = "posti_totali_service"
YEAR_COL = "buildYear_certification"
MAX_LABELLED_POINTS = 15  # annotate bivouac names only on sparse regional plots
CATEGORY_HELP = (
    "CAI shelter categories (A to E) classify altitude and accessibility: "
    "A = easily accessible near roads/villages; "
    "B = reachable via marked trails; "
    "C = high-altitude mountain huts; "
    "D/E = remote or mountaineering terrain."
)
DETAIL_FIELDS = {
    "title": "Official name",
    "altitude_geo": "Altitude (m)",
    "category": "Category",
    "seasons": "Opening",
    "region_geo" : "Region",
    "province_geo": "Province",
    "municipality_geo": "Municipality",
    "locality_geo": "Locality",
    "valley_geo": "Valley",
    "protected_area_geo": "Protected geographical area",
    "massif_geo": "Massif",
    "posti_totali_service": "Beds",
    "buildYear_certification": "Built in",
    "rebuildYear_certification": "Rebuilt in",
    "authority_jurisdiction_geo": "Jurisdiction of",
    "emailAddress": "Email address",
    "webAddress_contact": "Website"

}
LIST_COLS = ["alias", "altitude_geo", "region_geo", "province_geo", "municipality_geo"]


# --- DATA ---------------------------------------------------------------------


@st.cache_data
def load_bivouacs() -> pd.DataFrame:
    """Return the active bivouacs located in Italy."""
    df = load_all_shelters()
    df = df[df["type"].str.strip() == "Bivacco"]

    if "status" in df.columns:
        is_active = df["status"].astype(str).str.strip().str.lower() == "in attività"
        df = df[is_active]

    df = df[~df["region_geo"].isin(FOREIGN_REGIONS)]
    return df.reset_index(drop=True)


def get_altitudes(df: pd.DataFrame) -> np.ndarray:
    """Return the non-missing altitudes of `df` as a float array."""
    return df["altitude_geo"].dropna().to_numpy(dtype=float)


def compute_bivouacs_stats(df: pd.DataFrame) -> dict:
    """Compute altitude statistics for the given bivouacs (empty dict if no data)."""
    altitudes = get_altitudes(df)
    if altitudes.size == 0:
        return {}

    return {
        "count": int(altitudes.size),
        "mean": float(np.mean(altitudes)),
        "median": float(np.median(altitudes)),
        "max": float(np.max(altitudes)),
    }


# --- PLOTS --------------------------------------------------------------------
# All plot functions receive the bivouacs already filtered by scope;
# `scope` is only used for titles and styling.


def empty_figure(message: str, figsize: tuple = (8, 3.8)) -> Figure:
    """Return a figure containing only a centred message."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.axis("off")
    return fig


def plot_altitude_histogram(df: pd.DataFrame, scope: str) -> Figure:
    """Plot the altitude histogram with mean and median lines."""
    altitudes = get_altitudes(df)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(altitudes, bins="auto", color="#2E6F40", edgecolor="white", alpha=0.85)

    if altitudes.size > 0:
        mean_alt = np.mean(altitudes)
        median_alt = np.median(altitudes)
        ax.axvline(mean_alt, color="#D9534F", linestyle="--", linewidth=1.8,
                   label=f"Average: {int(mean_alt)} m")
        ax.axvline(median_alt, color="#F0AD4E", linestyle=":", linewidth=2.0,
                   label=f"Median: {int(median_alt)} m")
        ax.legend()

    ax.set_title(f"Altitude distribution of bivouacs ({scope})")
    ax.set_xlabel("Altitude (masl)")
    ax.set_ylabel("Number of bivouacs")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig


def plot_beds_vs_altitude(df: pd.DataFrame, scope: str) -> Figure:
    """Plot capacity (number of beds) against altitude."""
    valid = df.dropna(subset=["altitude_geo", BEDS_COL])
    altitudes = valid["altitude_geo"].astype(float)
    beds = valid[BEDS_COL].astype(float)

    fig, ax = plt.subplots(figsize=(6, 4))

    if not valid.empty:
        ax.scatter(
            altitudes,
            beds,
            color="#4B749F",
            s=35 if scope == ITALY else 80,
            alpha=0.85,
            edgecolors="black",
            zorder=3,
        )

        if scope != ITALY and "alias" in valid.columns and len(valid) <= MAX_LABELLED_POINTS:
            for name, x, y in zip(valid["alias"], altitudes, beds):
                ax.annotate(
                    str(name),
                    (x, y),
                    textcoords="offset points",
                    xytext=(0, 7),
                    ha="center",
                    fontsize=8,
                    color="#1f2937",
                )

    ax.set_title(f"Number of beds vs Altitude ({scope})")
    ax.set_xlabel("Altitude (masl)")
    ax.set_ylabel("Number of beds")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(True, linestyle="--", alpha=0.4, zorder=0)
    fig.tight_layout()
    return fig


def plot_cumulative_by_year(df: pd.DataFrame, scope: str) -> Figure:
    """Plot the cumulative number of bivouacs by construction year."""
    if YEAR_COL not in df.columns:
        return empty_figure("Construction year not available")

    # Extract a 4-digit year (handles both "1974" and "12/08/1974")
    years = df[YEAR_COL].dropna().astype(str).str.extract(r"(\d{4})")[0].dropna().astype(int)
    if years.empty:
        return empty_figure(f"No data for {scope}")

    cumulative = years.value_counts().sort_index().cumsum()

    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.plot(cumulative.index, cumulative.values, color="#2E7D32",
            linewidth=2.5, marker="o", markersize=5)
    ax.fill_between(cumulative.index, cumulative.values, color="#2E7D32", alpha=0.15)

    ax.set_title(f"Cumulative number of bivouacs by year ({scope})")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of bivouacs")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig


# --- UI HELPERS ---------------------------------------------------------------


def show_figure(fig: Figure) -> None:
    """Render a matplotlib figure in Streamlit and release its memory."""
    st.pyplot(fig)
    plt.close(fig)


def show_bivouac_details(bivouac: pd.Series) -> None:
    """Show a short, curated summary of the selected bivouac."""
    with st.container(border=True):
        st.markdown(f"### {bivouac.get('alias', 'Selected bivouac')}")
        for col, label in DETAIL_FIELDS.items():
            value = bivouac.get(col)
            if isinstance(value, (set, list, tuple)):
                cleaned = ", ".join(str(v).capitalize() for v in sorted(value) if v)
                if cleaned:
                    st.write(f"**{label}:** {cleaned}")
            elif pd.notna(value) and str(value).strip():
                if col == "category":
                    st.markdown(
                        f"**{label}:** {value} "
                        f"<span title='{CATEGORY_HELP}' style='cursor:help; color:#6b7280;'>ⓘ</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.write(f"**{label}:** {value}")


# --- PAGE ---------------------------------------------------------------------

st.title("Insights about CAI bivouacs")
st.write("Explore national data or filter by region. Click on a bivouac in the list for more info.")

df_italy = load_bivouacs()

# Scope selection (default: Italy)
regions = sorted(df_italy["region_geo"].dropna().unique())
scope = st.selectbox("Select region", [ITALY, *regions], index=0)

if scope == ITALY:
    df_scope = df_italy
else:
    df_scope = df_italy[df_italy["region_geo"] == scope].reset_index(drop=True)

# Key indicators
stats = compute_bivouacs_stats(df_scope)
if stats:
    st.subheader(f"Key indicators for {scope}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total number of bivouacs", stats["count"])
    c2.metric("Average Altitude", f"{int(stats['mean'])} m")
    c3.metric("Median Altitude", f"{int(stats['median'])} m")
    c4.metric("Maximum Altitude", f"{int(stats['max'])} m")

st.divider()

# Graphs
st.subheader(f"Graphical Analysis: {scope}")
col_left, col_right = st.columns(2)
with col_left:
    show_figure(plot_altitude_histogram(df_scope, scope))
with col_right:
    show_figure(plot_beds_vs_altitude(df_scope, scope))

st.divider()
show_figure(plot_cumulative_by_year(df_scope, scope))

# Clickable list + details
st.subheader(f"List of bivouacs ({len(df_scope)})")
st.caption("Select a row to view more info about a bivouac.")

display_cols = [c for c in LIST_COLS if c in df_scope.columns]

event = st.dataframe(
    df_scope[display_cols],
    width="stretch",
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "alias": "Name",
        "altitude_geo": "Altitude (m)",
        "region_geo": "Region",
        "province_geo": "Province",
        "municipality_geo": "Municipality",
    }
)


if event.selection.rows:
    show_bivouac_details(df_scope.iloc[event.selection.rows[0]])