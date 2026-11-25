"""PeakStay: find CAI shelters by region and municipality."""

import streamlit as st

st.set_page_config(page_title="PeakStay", page_icon="🏔️", layout="wide")

pages = [
    st.Page("pages/recommender.py", title="Recommender", icon="🏠", default=True),
    st.Page("pages/insights.py", title="Insights", icon="📊"),
]

st.navigation(pages).run()