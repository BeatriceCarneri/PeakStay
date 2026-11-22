# PeakStay

> **Draft version**: the project is under development and this README will be updated.

PeakStay is a mountain hut recommender built for a Python course. The user says **where** they want to go (region and municipality) and PeakStay suggests the staffed, active huts that best match their preferences.

## Data

The dataset comes from the **Unico Rifugi CAI** API:

- Documentation: https://rifugi.cai.it/api/documentation
- JSON schema: https://rifugi.cai.it/docs/api-docs.json

The dataset also includes bivouacs and unstaffed huts: the recommender only shows **staffed huts that are currently active**.

## How it works

**User input**

- Region (`ownerRegion_geo`)
- Municipality (`municipality_geo`)
- Altitude range (min-max slider, 50 m steps)
- Hut category (A-E)

**Scoring criteria**

- Altitude (`altitude_geo`)
- Category (A-E)

**Output**

Cards with 3 huts each, showing locality (`locality_geo`) and massif (`massif_geo`), plus a button to replace a suggested hut.

Coordinates are not used by the recommender.

## Project structure

```
PeakStay/
├── peakstay/        # Python package (data cleaning, recommender)
├── notebooks/       # exploration and analysis
├── app.py           # Streamlit web interface
├── requirements.txt # dependencies
├── pyproject.toml   # package configuration
└── .env.example     # example environment variables
```

Main modules:

- `cleaning.py`: data cleaning (e.g. `normalize_text` to unify capitalisation variants in geographic text fields)
- `recommender.py`: score computation and recommendations
- `app.py`: web interface built with Streamlit

## Getting started

```bash
# 1. clone the repository
git clone https://github.com/BeatriceCarneri/PeakStay.git
cd PeakStay

# 2. install dependencies
pip install -r requirements.txt

# 3. run the app
streamlit run app.py
```

## Next steps

- [ ] Code review and cleanup
- [ ] Tests for `cleaning.py` and `recommender.py`
- [ ] Document the scoring criteria
- [ ] Update this README with results and examples

## Author

Beatrice Carneri, project for the Python course.
