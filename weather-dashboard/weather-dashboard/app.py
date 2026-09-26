"""
Home page of the Weather Dashboard.
Run locally with:   streamlit run app.py
"""
import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise, load_districtwise, VARIABLES
from utils.style import inject_css, hero, plain_box, glossary_expander, BLOCK_COLOR, DISTRICT_COLOR, SIMPLE_NAMES

st.set_page_config(
    page_title="Weather Dashboard | Anand · Kheda · Mahisagar",
    page_icon="🌦️",
    layout="wide",
)
inject_css()

hero(
    "🌦️", "Weather Dashboard",
    "A simple way to see the difference between <b>your local area's weather</b> (block) "
    "and <b>your whole district's weather</b> (district) — 2021, 2022 and 2023.",
)

plain_box(
    "Think of <b>district</b> data like a weather forecast for your whole city, and "
    "<b>block</b> data like the weather right outside your own house. They're usually "
    "close — but not always! This dashboard shows you exactly where and when they differ."
)
glossary_expander()

try:
    block_df = load_blockwise()
    dist_df = load_districtwise()
except FileNotFoundError as e:
    st.error(str(e))
    st.info("Add your 3 yearly Excel files to the `data/` folder, then reload this page.")
    st.stop()

st.write("")
c1, c2, c3, c4 = st.columns(4)
c1.metric("📅 Years covered", f"{block_df['year'].min()}–{block_df['year'].max()}")
c2.metric("🏙️ Districts", block_df["district"].nunique())
c3.metric("📍 Blocks (local areas)", block_df["block"].nunique())
c4.metric("📊 Daily records", f"{len(block_df):,}")

st.write("")
st.markdown("## 🧭 Where do you want to go?")
st.caption("Click a page in the sidebar ⬅️, or read what each one does below.")

pages_info = [
    ("🔍", "Block vs District", "See your area's real weather **next to** your district's average, side by side — not squished into one confusing line.", "1_Block_vs_District"),
    ("🗺️", "Spatial Hotspots", "Find which local areas are always a bit hotter, colder, or wetter than the rest of their district.", "2_Spatial_Hotspots"),
    ("🌡️", "Extreme Events", "Count heatwaves, heavy rain days and cold nights — and see what the district data might be missing.", "3_Extreme_Events"),
    ("🌾", "Agro-Advisory", "Farming-relevant numbers like dry spells and heat-stress days, area by area.", "4_Agro_Advisory"),
    ("🚨", "Anomaly Detector", "Automatically spots weird or suspicious-looking data, like a temperature that never changes.", "5_Anomaly_Detector"),
    ("🧩", "Block Clustering", "Groups local areas by how similar their weather is — do the results match the official district map?", "6_Block_Clustering"),
    ("🌬️", "Wind Rose", "A compass-style chart showing which direction the wind usually blows from.", "7_Wind_Rose"),
    ("📈", "Seasonal Skill", "Checks whether the block/district gap gets bigger in the monsoon.", "8_Seasonal_Skill"),
    ("🤖", "Data Fusion Forecast", "Tests whether mixing block + district data gives a better guess than either alone.", "9_Data_Fusion_Forecast"),
]

for row_start in range(0, len(pages_info), 3):
    cols = st.columns(3)
    for col, (emoji, title, desc, target) in zip(cols, pages_info[row_start:row_start + 3]):
        with col:
            with st.container(border=True):
                st.markdown(f"### {emoji} {title}")
                st.write(desc)
                try:
                    st.page_link(f"pages/{target}.py", label="Open this page →")
                except Exception:
                    pass

st.divider()
st.markdown("## 🔎 Quick peek: pick something to see right now")
var = st.selectbox("What weather variable do you want to see?", list(VARIABLES.keys()), format_func=lambda k: SIMPLE_NAMES[k])

agg = block_df.groupby(["date", "district"])[var].mean().reset_index()
fig = px.line(
    agg, x="date", y=var, color="district",
    title=f"{SIMPLE_NAMES[var]} — daily average per district (all its blocks combined)",
    labels={var: f"{SIMPLE_NAMES[var]}", "date": "Date"},
)
fig.update_layout(legend_title_text="District", hovermode="x unified", height=420)
st.plotly_chart(fig, use_container_width=True)
plain_box("This chart mixes all blocks together per district, just to give you the big picture. Head to <b>🔍 Block vs District</b> to see one specific local area clearly.")
