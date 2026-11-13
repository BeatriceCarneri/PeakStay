"""Download of the CAI shelters from the Unico Rifugi API."""

import time
import requests
import json
from pathlib import Path

SEARCH_URL = "https://rifugi.cai.it/api/v1/shelters/search"


def fetch_page(page, per_page=None):
    """Download one page of the search endpoint."""
    params = {"page": page}
    if per_page:
        params["per_page"] = per_page
    resp = requests.get(SEARCH_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()["results"]


def fetch_all_shelters(delay=0.2):
    """Download every page and return the list of all shelters."""
    shelters = []
    page = 1
    while True:
        results = fetch_page(page)

        # 1) add the shelters of this page to the list
        shelters.extend(results["data"])

        # 2) stop when this was the last page
        if results["current_page"] == results["last_page"]:
            break

        page += 1
        time.sleep(delay)
    return shelters


def save_raw(shelters, path):
    """Save the raw shelters list to a JSON file."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(shelters, f, ensure_ascii=False, indent=2)


def load_raw(path):
    """Load the raw shelters list from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)