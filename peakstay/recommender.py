"""Scoring and ranking of shelters."""

import numpy as np
import pandas as pd


def geo_score(df, region, municipality=None):
    """Score from 0 to 1 for how close each shelter is to the search area."""
    # start from 0 for every shelter
    score = pd.Series(0.0, index=df.index)

    # for same region: 1/3
    score[df["region_geo"] == region] = 1/3

    if municipality:
        # massifs of the shelters that are in the chosen municipality
        massifs = df.loc[df["municipality_geo"] == municipality, "massif_geo"].dropna().unique()
        # for same massif: 2/3
        score[df["massif_geo"].isin(massifs)] = 2/3
        # for same municipality: 1
        score[df["municipality_geo"] == municipality] = 1.0
    return score


def altitude_score(df, target_altitude):
    """Score from 0 to 1 for how close each altitude is to the target."""
    alt = df["altitude_geo"].to_numpy(dtype=float)
    span = np.nanmax(alt) - np.nanmin(alt)
    # "relative error" between 0 and 1
    score = np.clip(1.0 - (alt - target_altitude) / span, 0.0, 1.0)
    score = np.nan_to_num(score, nan=0.0)
    score = np.where((score >= 0.0) & (score <= 1.0), score, 0.0)
    return pd.Series(score, index=df.index)


def category_score(df, target_category):
    """Score from 0 to 1 based on ASCII distance using ord() between categories A and E."""
    if "category" not in df.columns or not target_category:
        return pd.Series(0.0, index=df.index)

    target_char = str(target_category).strip().upper()[0]
    target_code = ord(target_char)

    # Convert the first letter of each category to its ASCII code (A=65 ... E=69)
    cat_codes = (
        df["category"]
        .fillna("E")
        .astype(str)
        .str.strip()
        .str.upper()
        .apply(lambda x: ord(x[0]) if len(x) > 0 else ord("E"))
        .to_numpy(dtype=float)
    )

    # Distance between A (65) and E (69) is 4
    score = 1.0 - (target_code - cat_codes) / 4.0
    score = np.nan_to_num(score, nan=0.0)
    score = np.where((score >= 0.0) & (score <= 1.0), score, 0.0)
    return pd.Series(score, index=df.index)


def recommend(df, region, municipality=None, target_altitude=None,target_category=None,
              w_geo=0.5, w_alt=0.25 , w_cat=0.25,top_n=70):
    """Return the top_n recommended shelters in the selected region."""
    # only refuges in the selected region are taken into consideration
    sub = df[df["region_geo"] == region].copy()
    g_score = geo_score(sub, region, municipality)

    if target_altitude is not None:
        a_score = altitude_score(sub, target_altitude)
        
        if target_category is not None:
            c_score = category_score(sub, target_category)
            sub["score"] = w_geo * g_score + w_alt * a_score + w_cat * c_score
        else:
            sub["score"] = (w_geo + w_cat / 2) * g_score + (w_alt + w_cat / 2) * a_score
    else:

        if target_category is not None:
            c_score = category_score(sub, target_category)
            sub["score"] = (w_geo + w_alt / 2) * g_score + (w_cat + w_alt / 2) * c_score
        else:
            sub["score"] = g_score

    return sub.sort_values(by=["score", "title"], ascending=[False, True]).head(top_n)