"""Scoring and ranking of shelters."""

import numpy as np
import pandas as pd


def geo_score(df, region, municipality=None):
    """Score from 0 to 1 for how close each shelter is to the search area."""
    # start from 0 for every shelter
    score = pd.Series(0.0, index=df.index)

    # same region -> 1/3
    ...

    if municipality:
        # massifs of the shelters that are in the chosen municipality
        massifs = ...
        # same massif -> 2/3
        ...
        # same municipality -> 1
        ...
    return score


def altitude_score(df, target_altitude):
    """Score from 0 to 1 for how close each altitude is to the target."""
    alt = df["altitude_geo"].to_numpy(dtype=float)
    span = np.nanmax(alt) - np.nanmin(alt)
    # 1 - |difference| / span, with NaN treated as 0
    ...


def recommend(df, region, municipality=None, target_altitude=None,
              w_geo=0.7, w_alt=0.3, top_n=10):
    """Return the top_n shelters, sorted by final score."""
    ...