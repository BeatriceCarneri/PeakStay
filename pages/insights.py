"""Insights page dedicated to CAI bivouacs across Italy and by region."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from peakstay.data import load_all_shelters

df_all = load_all_shelters()
df_bivacchi = df_all[df_all["type"].str.strip() == "Bivacco"].reset_index(drop=True)

def compute_bivacchi_stats(df_bivacchi: pd.DataFrame, scope: str = "Tutta Italia") -> dict:
    """Compute altitude statistics for Italy or a specific region using NumPy."""
    subset = df_bivacchi if scope == "Italiy" else df_bivacchi[df_bivacchi["region_geo"] == scope]
    altitudes = subset["altitude_geo"].dropna().to_numpy(dtype=float)
    national_altitudes = df_bivacchi["altitude_geo"].dropna().to_numpy(dtype=float)

    if len(altitudes) == 0:
        return {}

    mean_val = float(np.mean(altitudes))
    national_mean = float(np.mean(national_altitudes)) if len(national_altitudes) > 0 else mean_val

    return {
        "count": int(len(subset)),
        "mean": mean_val,
        "median": float(np.median(altitudes)),
        "std": float(np.std(altitudes)),
        "max": float(np.max(altitudes)),
        "delta_national": mean_val - national_mean,
    }


def plot_bivacchi_altitude(df_bivacchi: pd.DataFrame, scope: str = "Tutta Italia"):
    """Plot altitude histogram with mean and median lines."""
    subset = df_bivacchi if scope == "Italy" else df_bivacchi[df_bivacchi["region_geo"] == scope]
    altitudes = subset["altitude_geo"].dropna().to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(altitudes, bins=15, color="#2E6F40", edgecolor="white", alpha=0.85)

    if len(altitudes) > 0:
        mean_alt = np.mean(altitudes)
        median_alt = np.median(altitudes)
        ax.axvline(mean_alt, color="#D9534F", linestyle="--", linewidth=1.8, label=f"Media: {int(mean_alt)} m")
        ax.axvline(median_alt, color="#F0AD4E", linestyle=":", linewidth=2.0, label=f"Mediana: {int(median_alt)} m")
        ax.legend()

    ax.set_title(f"Distribuzione Altitudine Bivacchi ({scope})")
    ax.set_xlabel("Altitudine (m s.l.m.)")
    ax.set_ylabel("Numero di bivacchi")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig


def plot_bivacchi_territory(df_bivacchi: pd.DataFrame, scope: str = "Tutta Italia", top_n: int = 10):
    """Plot top regions for Italy or top provinces/areas for a single region."""
    fig, ax = plt.subplots(figsize=(6, 4))

    if scope == "Tutta Italia":
        counts = df_bivacchi["region_geo"].dropna().value_counts().head(top_n)[::-1]
        title = f"Top {top_n} Regioni per Numero di Bivacchi"
    else:
        subset = df_bivacchi[df_bivacchi["region_geo"] == scope]
        group_col = "province" if "province" in subset.columns and subset["province"].notna().any() else "region_geo"
        counts = subset[group_col].dropna().value_counts().head(top_n)[::-1]
        title = f"Distribuzione Bivacchi in {scope}"

    bars = ax.barh(counts.index.astype(str), counts.values, color="#3B7A9E")
    ax.bar_label(bars, padding=4, fontsize=9)
    ax.set_title(title)
    ax.set_xlabel("Numero di bivacchi")
    ax.set_xlim(0, max(counts.values) * 1.15 if len(counts) > 0 else 10)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig


def plot_bivacchi_map(df_bivacchi: pd.DataFrame, scope: str = "Tutta Italia"):
    """Plot geographic scatter (lon vs lat) colored by altitude."""
    subset = df_bivacchi if scope == "Tutta Italia" else df_bivacchi[df_bivacchi["region_geo"] == scope]
    geo = subset.dropna(subset=["lat", "lon", "altitude_geo"])

    fig, ax = plt.subplots(figsize=(8, 4.2))
    scatter = ax.scatter(
        geo["lon"],
        geo["lat"],
        c=geo["altitude_geo"],
        cmap="viridis",
        alpha=0.85,
        edgecolors="black",
        linewidth=0.4,
        s=45,
    )
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Altitudine (m)")

    ax.set_title(f"Mappa Geografica e Quote dei Bivacchi ({scope})")
    ax.set_xlabel("Longitudine")
    ax.set_ylabel("Latitudine")
    ax.grid(True, linestyle="--", alpha=0.35)
    fig.tight_layout()
    return fig


# --- INTERFACCIA STREAMLIT ---


st.title("Insights Bivacchi CAI")
st.write("Esplora i dati nazionali o filtra per regione. Clicca su un bivacco nell'elenco per aprire la sua scheda dettagliata.")

# 1. Selettore ambito (default: Tutta Italia)
regions = sorted(df_bivacchi["region_geo"].dropna().unique().tolist())
options = ["Tutta Italia"] + regions
selected_scope = st.selectbox("Seleziona l'area da analizzare", options, index=0)

if selected_scope == "Tutta Italia":
    df_view = df_bivacchi.reset_index(drop=True)
else:
    df_view = df_bivacchi[df_bivacchi["region_geo"] == selected_scope].reset_index(drop=True)

# 2. Metriche principali
stats = compute_bivacchi_stats(df_bivacchi, selected_scope)
if stats:
    st.subheader(f"Indicatori chiave: {selected_scope}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Totale Bivacchi", stats["count"])
    c2.metric(
        "Altitudine Media",
        f"{int(stats['mean'])} m",
        delta=None if selected_scope == "Tutta Italia" else f"{int(stats['delta_national']):+d} m vs Italia",
    )
    c3.metric("Altitudine Mediana", f"{int(stats['median'])} m")
    c4.metric("Quota Massima", f"{int(stats['max'])} m")

st.divider()

# 3. Grafici
st.subheader(f"Analisi Grafica: {selected_scope}")
col_left, col_right = st.columns(2)

with col_left:
    fig_alt = plot_bivacchi_altitude(df_bivacchi, selected_scope)
    st.pyplot(fig_alt)
    plt.close(fig_alt)

with col_right:
    fig_ter = plot_bivacchi_territory(df_bivacchi, selected_scope)
    st.pyplot(fig_ter)
    plt.close(fig_ter)

if {"lat", "lon"}.issubset(df_view.columns) and len(df_view[["lat", "lon"]].dropna()) > 0:
    fig_map = plot_bivacchi_map(df_bivacchi, selected_scope)
    st.pyplot(fig_map)
    plt.close(fig_map)

st.divider()

# 4. Lista completa cliccabile + Scheda dettagli
st.subheader(f"Elenco Bivacchi ({len(df_view)})")
st.caption("Seleziona una riga nella tabella per visualizzare tutte le informazioni disponibili sul bivacco.")

candidate_cols = ["name", "region_geo", "province", "municipality", "altitude_geo", "beds", "cai_section"]
display_cols = [c for c in candidate_cols if c in df_view.columns]

event = st.dataframe(
    df_view[display_cols],
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
)

selected_rows = event.selection.rows
if selected_rows:
    row_idx = selected_rows[0]
    bivacco = df_view.iloc[row_idx]

    with st.container(border=True):
        st.markdown(f"### {bivacco.get('name', 'Bivacco selezionato')}")
        info_col, map_col = st.columns([2, 1])

        with info_col:
            for col in df_view.columns:
                val = bivacco[col]
                if pd.notna(val) and str(val).strip() != "":
                    label = col.replace("_", " ").capitalize()
                    st.write(f"**{label}:** {val}")

        with map_col:
            if {"lat", "lon"}.issubset(df_view.columns) and pd.notna(bivacco["lat"]) and pd.notna(bivacco["lon"]):
                st.map(df_view.iloc[[row_idx]][["lat", "lon"]], zoom=11)
