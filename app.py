"""PeakStay: ... ."""

import streamlit as st

st.set_page_config(page_title="PeakStay", page_icon="🏔️", layout="wide")

pages = [
    st.Page("pages/shelters.py", title="Shelters Recommender", icon="🏠", default=True),
    st.Page("pages/insights.py", title="Bivouacs Insights", icon="📊"),
]

st.navigation(pages).run()