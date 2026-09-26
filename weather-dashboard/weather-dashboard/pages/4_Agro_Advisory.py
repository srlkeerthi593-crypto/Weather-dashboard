import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise
from utils.metrics import agro_indices
from utils.style import inject_css, hero, plain_box, glossary_expander, BLOCK_COLOR

st.set_page_config(page_title="Agro-Advisory Indices", page_icon="🌾", layout="wide")
inject_css()
hero("🌾", "Farming-Relevant Numbers", "Heat-stress days, dry spells, monsoon arrival and growing conditions — area by area, not just district-wide.", gradient=("#16A34A", "#4ADE80"))
plain_box(
    "Farmers plan around local weather, not district averages. This page works out a few simple, "
    "farming-relevant numbers <b>for every block</b> so you can see which areas need a different plan than their neighbours."
)
glossary_expander()
st.caption("⚠️ These are simplified, transparent estimates for comparing blocks — not official agromet advisories.")

block_df = load_blockwise()
year = st.selectbox("Year", sorted(block_df["year"].unique()))
sub = block_df[block_df["year"] == year]

with st.spinner("Working it out..."):
    idx = agro_indices(sub, ["district", "block"])

metric_info = {
    "heat_stress_days": ("🔥 Days too hot for crops", "Days with max temp ≥ 35°C — a common crop heat-stress cutoff."),
    "longest_dry_spell_days": ("🏜️ Longest stretch without real rain", "The longest run of consecutive days with under 2.5mm rainfall."),
    "monsoon_onset_doy": ("🌧️ When the monsoon actually arrived", "Day of year (out of 365) the first sustained wet spell began, roughly."),
    "gdd_proxy": ("🌱 Growing-degree total (warmth for crops)", "A running total of daily warmth above 10°C — higher means crops accumulate growth faster."),
}
metric = st.selectbox("What do you want to see?", list(metric_info.keys()), format_func=lambda k: metric_info[k][0])
title, desc = metric_info[metric]
plain_box(desc)

fig = px.bar(
    idx.sort_values(metric), x="block", y=metric, color="district",
    title=f"{title} — {year}", labels={metric: title, "block": ""},
)
fig.update_layout(xaxis_tickangle=-30, height=420)
st.plotly_chart(fig, use_container_width=True)

with st.expander("📋 Full table, every block"):
    st.dataframe(idx, use_container_width=True, hide_index=True)

st.divider()
st.markdown("### 🚩 Blocks that differ most from their own district")
district_avg = idx.groupby("district")[metric].transform("mean")
idx["gap_vs_district_avg"] = idx[metric] - district_avg
worst = idx.reindex(idx["gap_vs_district_avg"].abs().sort_values(ascending=False).index).head(5)
st.dataframe(worst[["district", "block", metric, "gap_vs_district_avg"]], use_container_width=True, hide_index=True)
plain_box("These blocks are the ones a district-wide farming advisory would be most wrong about — worth a closer look before sending out generic advice.")
