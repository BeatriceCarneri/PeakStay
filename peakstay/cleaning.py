import pandas as pd


def flatten(shelter):
    """Turn one shelter into a flat dict: id_cai, title and one key per field."""
    media_list = shelter.get("media", [])
    image_url = media_list[0].get("original_url") if media_list else None

    row = {
        "id_cai": shelter["id_cai"],
        "title": shelter["title"],
        "image_url": image_url,
    }
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


def keep_staffed_open(df):
    """Keep only staffed shelters that are currently operative."""
    df = df.copy()
    is_staffed = df["type"].str.strip() == "Rifugio custodito" 
    is_open = df["status"].str.strip() == "In attività"    
    return df[is_staffed & is_open].reset_index(drop=True)


def normalize_text(df):
    """Strip whitespace and unify case variants, avoiding all-caps or all-lowercase."""
    cols = ["region_geo", "municipality_geo", "massif_geo", "locality_geo"]

    def pick_best(group):
        valid = group.dropna()
        if valid.empty:
            return pd.NA
        counts = valid.value_counts()
        best = sorted(
            counts.index,
            key=lambda x: (x.isupper() or x.islower(), -counts[x]),
        )
        return best [0]

    for col in cols:
        if col in df.columns:
            s = df[col].str.strip()
            df[col] = s.groupby(s.str.lower(), dropna=False).transform(pick_best)
            df[col] = df[col].str[0].str.upper() + df[col].str[1:]

    return df
