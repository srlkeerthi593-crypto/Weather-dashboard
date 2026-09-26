"""
Home page of the Anand-Kheda-Mahisagar Weather Dashboard.

Run locally with:   streamlit run app.py
"""
import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise, load_districtwise, VARIABLES

st.set_page_config(
    page_title="Weather Dashboard | Anand · Kheda · Mahisagar",
    page_icon="🌦️",
    layout="wide",
)

st.title("🌦️ Anand · Kheda · Mahisagar Weather Dashboard")
st.caption("Block-level vs. district-level weather data, 2021–2023")

st.markdown(
    """
Welcome! This dashboard compares **block-level** weather records (24 blocks)
against **district-level** records (3 districts: Anand, Kheda, Mahisagar) for
three years — 2021, 2022 and 2023.

**Why this matters:** district-level data is what most people can easily get,
but it hides local differences. If a district's average temperature is used
for every block inside it, some blocks will get a misleading picture of
their real weather. This dashboard measures exactly how big that gap is,
and where it matters most.

👈 **Use the sidebar** to move between sections. Each page explains, in
plain language, what it shows and why it's useful.
"""
)

try:
    block_df = load_blockwise()
    dist_df = load_districtwise()
except FileNotFoundError as e:
    st.error(str(e))
    st.info("Add your 3 yearly Excel files to the `data/` folder, then reload this page.")
    st.stop()

st.divider()

# ---- Top-line numbers ----------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Years covered", f"{block_df['year'].min()}–{block_df['year'].max()}")
c2.metric("Districts", block_df["district"].nunique())
c3.metric("Blocks", block_df["block"].nunique())
c4.metric("Block-days of data", f"{len(block_df):,}")

st.divider()

# ---- Simple explorer: pick a variable, see the trend ----------------------
st.subheader("Quick look: pick a variable")
var = st.selectbox(
    "Variable",
    list(VARIABLES.keys()),
    format_func=lambda k: VARIABLES[k],
)

agg = (
    block_df.groupby(["date", "district"])[var]
    .mean()
    .reset_index()
)
fig = px.line(
    agg, x="date", y=var, color="district",
    title=f"District-average {VARIABLES[var]} — daily, all blocks averaged per district",
    labels={var: VARIABLES[var], "date": "Date"},
)
fig.update_layout(legend_title_text="District", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

st.markdown(
    """
---
### What's in this dashboard

| Page | What it tells you |
|---|---|
| 🔍 Block vs District | How closely each block's data matches its district's data (RMSE, correlation, bias) |
| 🗺️ Spatial Hotspots | Which blocks are consistently hotter/cooler/wetter than their district average |
| 🌡️ Extreme Events | Heatwave days, heavy-rain days and cold nights — block-level vs district-level counts |
| 🌾 Agro-Advisory | Heat-stress days, dry spells, monsoon onset and growing-degree-days per block |
| 🚨 Anomaly Detector | Suspicious data — frozen values, sudden jumps, rain with no clouds |
| 🧩 Block Clustering | Groups blocks by weather behaviour — does it match district boundaries? |
| 🌬️ Wind Rose | Wind direction/speed patterns, block-aggregated vs district file |
| 📈 Seasonal Skill | Does block-vs-district disagreement grow in monsoon and shrink in winter? |
"""
)
