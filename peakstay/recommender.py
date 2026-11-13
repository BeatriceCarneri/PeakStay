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
    score = np.clip(1.0 - np.abs(alt - target_altitude) / span, 0.0, 1.0)
    score = np.nan_to_num(score, nan=0.0)
    score = np.clip(score, 0.0, 1.0)
    return pd.Series(score, index=df.index)


def recommend(df, region, municipality=None, target_altitude=None, w_geo=0.7, w_alt=0.3, top_n=10):
    """Return the top_n recommended shelters in the selected region."""
    # only refuges in the selected region are taken into consideration
    sub = df[df["region_geo"] == region].copy()
    g_score = geo_score(sub, region, municipality)

    if target_altitude is not None:
        a_score = altitude_score(sub, target_altitude)
        sub["score"] = w_geo * g_score + w_alt * a_score
    else:
        sub["score"] = g_score

    return sub.sort_values(by=["score", "title"], ascending=[False, True]).head(top_n)
