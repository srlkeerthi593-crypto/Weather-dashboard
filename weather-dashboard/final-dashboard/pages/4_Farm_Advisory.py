import datetime
import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise
from utils.metrics import agro_indices
from utils.style import inject_css, hero, plain_box, glossary_expander, BLOCK_COLOR

st.set_page_config(page_title="Farm Advisory", page_icon="🌾", layout="wide")
inject_css()
hero("🌾", "Farm Advisory Numbers", "A few simple, farming-relevant numbers — worked out separately for every local area, not just one number for the whole district.", gradient=("#16A34A", "#4ADE80"))
plain_box(
    "Farmers plan around <b>local</b> weather, not a district-wide average. This page works out 4 simple, "
    "farming-relevant numbers <b>for every block</b>, so you can see which areas need different advice than their neighbours."
)
glossary_expander()
st.caption("⚠️ These are simplified, transparent estimates for comparing blocks side by side — not an official government agromet advisory.")

block_df = load_blockwise()
year = st.selectbox("📅 Pick a year", sorted(block_df["year"].unique()))
sub = block_df[block_df["year"] == year]

with st.spinner("Working it out..."):
    idx = agro_indices(sub, ["district", "block"])

def _doy_to_date(doy, year):
    if pd_isna(doy):
        return "No clear monsoon start found"
    try:
        return (datetime.date(int(year), 1, 1) + datetime.timedelta(days=int(doy) - 1)).strftime("%d %B")
    except Exception:
        return "No clear monsoon start found"

def pd_isna(v):
    import pandas as pd
    return pd.isna(v)

idx_display = idx.copy()
idx_display["monsoon_onset_date"] = idx_display["monsoon_onset_doy"].apply(lambda d: _doy_to_date(d, year))

metric_info = {
    "heat_stress_days": ("🔥 Days too hot for crops", "Number of days where the max temperature was 35°C or higher — a common cutoff where many crops start suffering heat stress."),
    "longest_dry_spell_days": ("🏜️ Longest stretch without real rain", "The longest run of back-to-back days with almost no rain (under 2.5mm) — useful for planning irrigation."),
    "monsoon_onset_doy": ("🌧️ When the monsoon actually arrived", "The approximate date the first proper, sustained wet spell began that year."),
    "gdd_proxy": ("🌱 Total warmth crops received", "A running total of how much warm weather (above 10°C) built up over the year — more warmth generally means faster crop growth."),
}
metric = st.selectbox("What do you want to see?", list(metric_info.keys()), format_func=lambda k: metric_info[k][0])
title, desc = metric_info[metric]
plain_box(desc)

if metric == "monsoon_onset_doy":
    st.markdown(f"### {title} — {year}")
    st.dataframe(
        idx_display[["district", "block", "monsoon_onset_date"]].rename(
            columns={"district": "District", "block": "Block", "monsoon_onset_date": "Approx. monsoon start date"}
        ),
        use_container_width=True, hide_index=True,
    )
else:
    fig = px.bar(
        idx.sort_values(metric), x="block", y=metric, color="district",
        title=f"{title} — {year}", labels={metric: title, "block": ""},
    )
    fig.update_layout(xaxis_tickangle=-30, height=420)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("📋 See every block's full set of numbers"):
    st.dataframe(
        idx_display[["district", "block", "heat_stress_days", "longest_dry_spell_days", "monsoon_onset_date", "gdd_proxy"]].rename(
            columns={
                "district": "District", "block": "Block",
                "heat_stress_days": "Heat-stress days", "longest_dry_spell_days": "Longest dry spell (days)",
                "monsoon_onset_date": "Monsoon started around", "gdd_proxy": "Total crop warmth",
            }
        ),
        use_container_width=True, hide_index=True,
    )

st.divider()
st.markdown("### 🚩 Blocks that differ most from their own district")
st.caption("These are the local areas where a one-size-fits-all district advisory would be the most wrong.")
district_avg = idx.groupby("district")[metric].transform("mean")
idx["gap_vs_district_avg"] = idx[metric] - district_avg
worst = idx.reindex(idx["gap_vs_district_avg"].abs().sort_values(ascending=False).index).head(5)
st.dataframe(
    worst[["district", "block", metric, "gap_vs_district_avg"]].rename(
        columns={"district": "District", "block": "Block", metric: title, "gap_vs_district_avg": "Gap vs. district average"}
    ),
    use_container_width=True, hide_index=True,
)
plain_box("A local officer using only the district-wide number would give the wrong advice to these blocks — worth a closer look before sending out generic advice.")
