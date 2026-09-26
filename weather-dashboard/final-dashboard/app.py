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
    "close — but not always! This dashboard shows you exactly where and when they differ, "
    "using 5 simple, easy-to-read pages."
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
st.markdown("## 🧭 5 things you can explore")
st.caption("Click a card below, or use the sidebar ⬅️ any time. Each page explains itself in plain words as you go.")

pages_info = [
    ("1️⃣", "🔍", "Block vs District", "Pick your own local area and see it placed side-by-side with your district's average — is the district number a good stand-in for your area, or not?", "1_Block_vs_District"),
    ("2️⃣", "🗺️", "Spatial Hotspots", "Find which local areas are quietly always a bit hotter, colder, or wetter than the rest of their district.", "2_Spatial_Hotspots"),
    ("3️⃣", "🌡️", "Extreme Events", "Count real heatwave days, heavy-rain days and cold nights — and see the exact dates, plus what a district-only view would miss.", "3_Extreme_Events"),
    ("4️⃣", "🌾", "Farm Advisory", "Simple, farming-relevant numbers — heat-stress days, dry spells, when the monsoon started — area by area.", "4_Farm_Advisory"),
]

cols = st.columns(4)
for col, (num, emoji, title, desc, target) in zip(cols, pages_info):
    with col:
        with st.container(border=True):
            st.markdown(f"#### {num} {emoji}")
            st.markdown(f"**{title}**")
            st.caption(desc)
            try:
                st.page_link(f"pages/{target}.py", label="Open →")
            except Exception:
                pass

st.divider()
st.markdown("## 🔎 Quick peek: pick something to see right now")
var = st.selectbox("What weather variable do you want to see?", list(VARIABLES.keys()), format_func=lambda k: SIMPLE_NAMES[k])

agg = block_df.groupby(["date", "district"])[var].mean().reset_index()
st.caption(f"{SIMPLE_NAMES[var]} — daily average, one chart per district so they're never mixed together.")

# Same y-axis range on all 3 so they're fairly comparable at a glance
y_min, y_max = agg[var].min(), agg[var].max()
pad = (y_max - y_min) * 0.06 if y_max > y_min else 1
district_colors = {"Anand": "#2563EB", "Kheda": "#16A34A", "Mahisagar": "#F97316"}

d_cols = st.columns(3)
for col, district in zip(d_cols, sorted(agg["district"].unique())):
    with col:
        one = agg[agg["district"] == district]
        fig = px.area(one, x="date", y=var, title=f"🏙️ {district}")
        fig.update_traces(line_color=district_colors.get(district, BLOCK_COLOR), fillcolor="rgba(37,99,235,0.12)")
        fig.update_layout(height=300, showlegend=False, yaxis_range=[y_min - pad, y_max + pad],
                           yaxis_title=None, xaxis_title=None, margin=dict(t=40, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

plain_box("This mixes all blocks together per district, just to give you the big picture — one clear panel per district, all on the same scale so they're easy to compare. Head to <b>🔍 Block vs District</b> (page 1) to zoom into one specific local area.")
