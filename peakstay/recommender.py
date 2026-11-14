"""Scoring and ranking of shelters."""

import numpy as np
import pandas as pd


def geo_score(df, municipality):
    """Score from 0 to 1 for how close each shelter is to the search area."""
    # start from 0 for every shelter
    score = pd.Series(0.0, index=df.index)
    score[df["municipality_geo"] == municipality] = 1.0
    return score


def altitude_score(df, target_altitude_min=None, target_altitude_max=None):
    """Score from 0 to 1 for how close each altitude is to the target."""
    alt = df["altitude_geo"].to_numpy(dtype=float)

    target_altitude_min = target_altitude_min or np.nannmin(alt)
    target_altitude_max = target_altitude_max or np.nannmax(alt)

    span = target_altitude_max - target_altitude_min
    # "relative error" between 0 and 1
    score = 1.0 - (target_altitude_max - alt) / span
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


def recommend(df, region, municipality=None, target_altitude_min=None, target_altitude_max=None,target_category=None,
              w_geo=0.2, w_alt=0.3 , w_cat=0.5,top_n=70):
    """Return the top_n recommended shelters in the selected region."""
    # only refuges in the selected region are taken into consideration
    sub = df[df["region_geo"] == region].copy()
    if target_altitude_min is not None:
        sub = sub[sub["altitude_geo"] >= target_altitude_min].copy()
    if target_altitude_max is not None:
        sub = sub[sub["altitude_geo"] <= target_altitude_max].copy()
    if target_category is not None:
        sub = sub[sub["category"] <= target_category].copy()

    if sub.empty:
        return sub

    total_score = pd.Series(0.0, index=sub.index)
    total_weight = 0.0

    if municipality is not None:
        total_score += w_geo * geo_score(sub, municipality)
        total_weight = w_geo

    if (target_altitude_min is not None) or (target_altitude_max is not None):
        total_score += w_alt * altitude_score(sub, target_altitude_min, target_altitude_max)
        total_weight = w_alt
        
    if target_category is not None:
        total_score += w_cat * category_score(sub, target_category)
        total_weight = w_cat

    if total_weight > 0:
        sub["score"] = total_score / total_weight
    else:
        sub["score"] = 0.0

    return sub.sort_values(by=["score", "altitude_geo"], ascending=[False, False]).head(top_n)
