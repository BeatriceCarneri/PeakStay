import json

import pandas as pd

# Opening-season values that need special handling (all lowercase, stripped)
SEASON_ALIASES = {
    "apertura annuale": "year-round",
    "annuale": "year-round",
    "estiva": "summer",
    "invernale": "winter",
    "fine settimana": "weekends",
    "periodo natalizio": "christmas period",
    "scialpinismo primaverile": "spring ski mountaineering",
}

IGNORED_SEASONS = {"aperto tutti i festivi escluso natale e pasqua"}


def parse_seasons(blocks):
    """Return the set of normalised opening seasons from the openingTime_contact blocks."""
    seasons = set()
    for block in blocks or []:
        raw_type = (block.get("attributes") or {}).get("type")
        # `type` is a JSON list stored as a string, e.g. '["annuale"]'
        try:
            values = json.loads(raw_type) if isinstance(raw_type, str) else (raw_type or [])
        except json.JSONDecodeError:
            values = [raw_type]
        for value in values:
            value = str(value).strip().lower()
            value = SEASON_ALIASES.get(value, value)
            if value and value not in IGNORED_SEASONS:
                seasons.add(value)
    return seasons


def flatten(shelter):
    """Turn one shelter into a flat dict: id_cai, title, seasons and one key per field."""
    media_list = shelter.get("media", [])
    image_url = media_list[0].get("original_url") if media_list else None

    row = {
        "id_cai": shelter["id_cai"],
        "title": shelter["title"],
        "image_url": image_url,
    }
    for f in shelter["fields"]:
        row[f["name"]] = f["value"]

    # The opening time has no plain value: its seasons are in the field's `data` blocks
    opening = next(
        (f.get("data") for f in shelter["fields"] if f["name"] == "openingTime_contact"),
        None,
    )
    row["seasons"] = parse_seasons(opening)
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