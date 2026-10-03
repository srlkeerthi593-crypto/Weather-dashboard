"""Entry point.  Run:  streamlit run app.py
The first page (Block vs District) opens by default; there is no separate home page."""
import streamlit as st

st.set_page_config(page_title="Block vs District Weather", page_icon="🌦️", layout="wide")

pages = [
    st.Page("views/block_vs_district.py", title="Block vs District", icon="🗺️", default=True),
    st.Page("views/reliable.py", title="Which is Reliable?", icon="🏆"),
    st.Page("views/hotspots.py", title="Spatial Hotspots", icon="🔥"),
    st.Page("views/charts.py", title="Result Charts", icon="🖼️"),
]
st.navigation(pages).run()
