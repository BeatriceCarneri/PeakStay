"""Insights page dedicated to CAI bivouacs across Italy and by region."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from peakstay.data import load_all_shelters
from matplotlib.ticker import MaxNLocator

df_all = load_all_shelters()
df_bivouacs = df_all[df_all["type"].str.strip() == "Bivacco"].reset_index(drop=True)

if "status" in df_bivouacs.columns:
    df_bivouacs = df_bivouacs[
        df_bivouacs["status"].astype(str).str.strip().str.lower() == "in attività"
    ].copy()
regioni_estere = ["Savoia Francia", "Svizzera"]
df_bivouacs = df_bivouacs[~df_bivouacs["region_geo"].isin(regioni_estere)].copy()

def compute_bivouacs_stats(df_bivouacs: pd.DataFrame, scope: str = "Italy") -> dict:
    """Compute altitude statistics for Italy or a specific region."""
    subset = df_bivouacs if scope == "Italy" else df_bivouacs[df_bivouacs["region_geo"] == scope]
    altitudes = subset["altitude_geo"].dropna().to_numpy(dtype=float)

    if len(altitudes) == 0:
        return {}

    return {
        "count": int(len(altitudes)),
        "mean": float(np.mean(altitudes)),
        "median": float(np.median(altitudes)),
        "max": float(np.max(altitudes)),
    }


def plot_bivouacs_altitude(df_bivouacs: pd.DataFrame, scope: str = "Italy"):
    """Plot altitude histogram with mean and median lines."""
    subset = df_bivouacs if scope == "Italy" else df_bivouacs[df_bivouacs["region_geo"] == scope]
    altitudes = subset["altitude_geo"].dropna().to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(altitudes, bins="auto", color="#2E6F40", edgecolor="white", alpha=0.85)

    if len(altitudes) > 0:
        mean_alt = np.mean(altitudes)
        median_alt = np.median(altitudes)
        ax.axvline(mean_alt, color="#D9534F", linestyle="--", linewidth=1.8, label=f"Media: {int(mean_alt)} m")
        ax.axvline(median_alt, color="#F0AD4E", linestyle=":", linewidth=2.0, label=f"Mediana: {int(median_alt)} m")
        ax.legend()

    ax.set_title(f"Altitude distribution of bivouacs ({scope})")
    ax.set_xlabel("Altitude (masl)")
    ax.set_ylabel("Number of bivouacs")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    return fig


def plot_bivouacs_beds_vs_altitude(df_bivouacs: pd.DataFrame, scope: str = "Italy"):
    """Plot capacity (number of beds) vs altitude for Italy or a single region."""
    subset = df_bivouacs if scope == "Italy" else df_bivouacs[df_bivouacs["region_geo"] == scope]
    
    beds_col = "posti_totali_service" 
    
    fig, ax = plt.subplots(figsize=(6, 4))
    
    # Filtra i dati validi
    valid_data = subset.dropna(subset=["altitude_geo", beds_col]).copy()
    valid_data["altitude_geo"] = valid_data["altitude_geo"].astype(float)
    valid_data[beds_col] = valid_data[beds_col].astype(float)

    if not valid_data.empty:
        ax.scatter(
            valid_data["altitude_geo"],
            valid_data[beds_col],
            color="#4B749F",
            s=80 if scope != "Italy" else 35,
            alpha=0.85,
            edgecolors="black",
            zorder=3
        )

        name_col = next((col for col in ["alias"] if col in valid_data.columns), None)
        if scope != "Italy" and name_col and len(valid_data) <= 15:
            for _, row in valid_data.iterrows():
                ax.annotate(
                    str(row[name_col]),
                    (row["altitude_geo"], row[beds_col]),
                    textcoords="offset points",
                    xytext=(0, 7),
                    ha="center",
                    fontsize=8,
                    color="#1f2937"
                )

    ax.set_title(f"Number of beds vs Altitude ({scope})")
    ax.set_xlabel("Altitude (masl)")
    ax.set_ylabel("Number of beds")
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.grid(True, linestyle="--", alpha=0.4, zorder=0)
    fig.tight_layout()
    return fig


def plot_bivouacs_year(df_bivouacs: pd.DataFrame, scope: str = "Italy"):
    """Plot bivouacs construction year distribution or timeline."""
    subset = df_bivouacs if scope == "Italy" else df_bivouacs[df_bivouacs["region_geo"] == scope]
    
    # Cerca automaticamente la colonna dell'anno di costruzione
    possible_year_cols = ["buildYear_certification"]
    year_col = next((col for col in possible_year_cols if col in df_bivouacs.columns), None)
    
    fig, ax = plt.subplots(figsize=(8, 3.8))
    
    if year_col is None:
        ax.text(
            0.5, 0.5,
            f"Column year not found.\nAvailable columns:\n{list(df_bivouacs.columns)}",
            ha="center", va="center", fontsize=8, wrap=True
        )
        ax.axis("off")
        return fig
    
    # Estrae l'anno numerico a 4 cifre (gestisce anche stringhe tipo "1974" o "12/08/1974")
    years = subset[year_col].dropna().astype(str).str.extract(r"(\d{4})")[0].dropna().astype(int)

    if years.empty:
        ax.text(0.5, 0.5, f"No data for {scope}", ha="center", va="center")
        ax.axis("off")
        return fig

    valid_rows = subset.loc[years.index].copy()
    valid_rows["year_num"] = years

    # Conta i bivacchi per anno e calcola la somma cumulativa
    counts_by_year = valid_rows["year_num"].value_counts().sort_index()
    cumulative_bivouacs = counts_by_year.cumsum()

    # Disegna la linea cumulativa e l'area sottostante
    ax.plot(cumulative_bivouacs.index, cumulative_bivouacs.values, color="#2E7D32", linewidth=2.5, marker="o", markersize=5)
    ax.fill_between(cumulative_bivouacs.index, cumulative_bivouacs.values, color="#2E7D32", alpha=0.15)

    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.yaxis.get_major_locator().set_params(integer=True)

    ax.set_title(f"Cumulative number of bivouacs by year ({scope})")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of bivouacs")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig


# STREAMLIT INTERFACE 


st.title("Insights about CAI bivouacs")
st.write("Explore national data or filter by region. Click on a bivouac in the list for more info."
)

# (Default: Italy)
regions = sorted(df_bivouacs["region_geo"].dropna().unique().tolist())
options = ["Italy"] + regions
selected_scope = st.selectbox("Select region", options, index=0)

if selected_scope == "Italy":
    df_bivouacs = df_bivouacs.reset_index(drop=True)
else:
    df_bivouacs = df_bivouacs[df_bivouacs["region_geo"] == selected_scope].reset_index(drop=True)

# 2. Metrics
stats = compute_bivouacs_stats(df_bivouacs, selected_scope)
if stats:
    st.subheader(f"Key indicators for {selected_scope}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total number of bivouacs", stats["count"])
    c2.metric("Average Altitude", f"{int(stats['mean'])} m")
    c3.metric("Median Altitude", f"{int(stats['median'])} m")
    c4.metric("Maximum Altitude", f"{int(stats['max'])} m")

st.divider()

# 3. Graphs
st.subheader(f"Graphical Analysis: {selected_scope}")
col_left, col_right = st.columns(2)

with col_left:
    fig_alt = plot_bivouacs_altitude(df_bivouacs, selected_scope)
    st.pyplot(fig_alt)
    plt.close(fig_alt)

with col_right:
    fig_ter = plot_bivouacs_beds_vs_altitude(df_bivouacs, selected_scope)
    st.pyplot(fig_ter)
    plt.close(fig_ter)

st.divider()

fig_year = plot_bivouacs_year(df_bivouacs, selected_scope)
st.pyplot(fig_year)
plt.close(fig_year)


# 4. Lista completa cliccabile + Scheda dettagli
st.subheader(f"List of bivouacs ({len(df_bivouacs)})")
st.caption("Select a row to view more info about a bivouac.")

candidate_cols = ["alias", "altitude_geo", "region_geo", "province_geo", "municipality_geo"]
display_cols = [c for c in candidate_cols if c in df_bivouacs.columns]

event = st.dataframe(
    df_bivouacs[display_cols],
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
)

selected_rows = event.selection.rows
if selected_rows:
    row_idx = selected_rows[0]
    bivacco = df_bivouacs.iloc[row_idx]

    with st.container(border=True):
        st.markdown(f"### {bivacco.get('alias', 'Selected bivouac')}")
        info_col, map_col = st.columns([2, 1])

        with info_col:
            for col in df_bivouacs.columns:
                val = bivacco[col]
                if pd.notna(val) and str(val).strip() != "":
                    label = col.replace("_", " ").capitalize()
                    st.write(f"**{label}:** {val}")