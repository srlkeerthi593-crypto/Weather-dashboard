"""Home page.  Run locally:  streamlit run app.py"""
import plotly.express as px
import streamlit as st

from utils.data_loader import LABELS, YEARS
from utils.style import inject_css, hero, plain_box, glossary, need_data, DIST_COLOR

st.set_page_config(page_title="Block vs District Weather | Anand · Kheda · Mahisagar",
                   page_icon="🌦️", layout="wide")
inject_css()

hero("🌦️", "Block vs District Weather Dashboard",
     "Comparing <b>block-level</b> (local) and <b>district-level</b> (wide-area) weather data for "
     "Anand, Kheda and Mahisagar, 2021–2023 — how close are they, where do they differ, and which one can you trust?")
plain_box("Think of <b>district</b> data as one weather number for a whole city, and <b>block</b> data as the weather "
          "right outside your own house. We treat the block data as the closer-to-ground <i>reference</i> and test how "
          "well the district number matches it.")
glossary()

df = need_data()
c1, c2, c3, c4 = st.columns(4)
c1.metric("📅 Years", f"{min(YEARS)}–{max(YEARS)}")
c2.metric("🏙️ Districts", df["District"].nunique())
c3.metric("📍 Blocks", df["Block"].nunique())
c4.metric("📊 Block-day records", f"{len(df):,}")

st.markdown("## 🧭 Explore")
pages = [
    ("🗺️", "District Map & Compare", "Pick a district, click a block on the map, and see block info beside district info.", "pages/1_District_Map_Compare.py"),
    ("🎯", "Accuracy & Reliability", "Scorecard for all variables: errors, correlation, bias, and which source is more trustworthy.", "pages/2_Accuracy_and_Reliability.py"),
    ("🔥", "Spatial Hotspots", "Which blocks are always hotter, colder, wetter or windier than their district?", "pages/3_Spatial_Hotspots.py"),
    ("🖼️", "Verification Charts", "Your published comparison graphs from the results folder.", "pages/4_Verification_Charts.py"),
    ("🛠️", "Bias Correction", "How a simple seasonal correction shrinks the block–district gap.", "pages/5_Bias_Correction.py"),
]
cols = st.columns(len(pages))
for col, (emo, title, desc, target) in zip(cols, pages):
    with col, st.container(border=True):
        st.markdown(f"#### {emo}")
        st.markdown(f"**{title}**")
        st.caption(desc)
        st.page_link(target, label="Open →")

st.divider()
st.markdown("## 🔎 Quick peek")
label = st.selectbox("Variable", list(LABELS))
key = LABELS[label]
agg = df.groupby(["Date", "District"])[[f"{key}_blk", f"{key}_dst"]].mean().reset_index()
cols = st.columns(3)
for col, dist in zip(cols, sorted(agg["District"].unique())):
    one = agg[agg["District"] == dist].melt(["Date", "District"], var_name="Source", value_name=label)
    one["Source"] = one["Source"].map({f"{key}_blk": "Block average", f"{key}_dst": "District"})
    fig = px.line(one, x="Date", y=label, color="Source", title=f"🏙️ {dist}",
                  color_discrete_map={"Block average": "#7C3AED", "District": DIST_COLOR[dist]})
    fig.update_layout(height=300, legend=dict(orientation="h", y=-0.25), margin=dict(t=40, b=10, l=10, r=10),
                      xaxis_title=None)
    col.plotly_chart(fig, use_container_width=True)
st.caption("Block average = mean of all blocks in the district, drawn against the district's own value.")
