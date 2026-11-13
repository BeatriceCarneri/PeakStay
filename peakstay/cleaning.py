import pandas as pd


def flatten(shelter):
    """Turn one shelter into a flat dict: id_cai, title and one key per field."""
    row = {"id_cai": shelter["id_cai"], "title": shelter["title"]}
    for f in shelter["fields"]:
        row[f["name"]] = f["value"]
    return row


def build_dataframe(shelters):
    """Turn the raw shelters list into a DataFrame, one row per shelter."""
    return pd.DataFrame([flatten(s) for s in shelters])


def clean_altitude(df):
    """Convert altitude_geo to numbers; invalid values become NaN."""
    df["altitude_geo"] = pd.to_numeric(df["altitude_geo"], errors="coerce")
    return df


def normalize_text(df):
    """Strip whitespace from the geographic text columns"""
    cols = ["region_geo", "municipality_geo", "massif_geo", "locality_geo"]
    for col in cols:
        if col in df.columns:
            df[col] = df[col].str.strip()
    return df

