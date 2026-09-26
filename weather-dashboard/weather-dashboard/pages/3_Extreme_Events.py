import streamlit as st
import plotly.express as px
import pandas as pd

from utils.data_loader import load_blockwise, load_districtwise
from utils.metrics import extreme_event_counts

st.set_page_config(page_title="Extreme Events", page_icon="🌡️", layout="wide")
st.title("🌡️ Extreme-Event Skill: Block vs District")

st.markdown(
    """
Averages can look fine even when a dataset completely misses extreme days.
This page counts how many **heatwave days**, **heavy-rain days** and
**cold nights** each block recorded, and compares that to what the
district-level file alone would have told you.

Default thresholds (adjustable below):
- 🔥 Heatwave day: max temperature ≥ **40°C**
- 🌧️ Heavy rain day: rainfall ≥ **64.5 mm** (IMD "heavy rainfall" cutoff)
- 🥶 Cold night: min temperature ≤ **10°C**
"""
)

c1, c2, c3 = st.columns(3)
hw = c1.number_input("Heatwave threshold (°C)", value=40.0, step=0.5)
hr = c2.number_input("Heavy rain threshold (mm)", value=64.5, step=0.5)
cn = c3.number_input("Cold night threshold (°C)", value=10.0, step=0.5)

block_df = load_blockwise()
dist_df = load_districtwise()

years = st.multiselect("Years", sorted(block_df["year"].unique()), default=sorted(block_df["year"].unique()))
b_sub = block_df[block_df["year"].isin(years)]
d_sub = dist_df[dist_df["year"].isin(years)]

block_counts = extreme_event_counts(b_sub, ["district", "block"], hw, hr, cn)
dist_counts = extreme_event_counts(d_sub, ["district"], hw, hr, cn).rename(
    columns={"heatwave_days": "district_heatwave_days",
             "heavy_rain_days": "district_heavy_rain_days",
             "cold_nights": "district_cold_nights"}
)

merged = block_counts.merge(dist_counts, on="district", how="left")

metric = st.selectbox(
    "Event type",
    ["heatwave_days", "heavy_rain_days", "cold_nights"],
    format_func=lambda x: {"heatwave_days": "🔥 Heatwave days", "heavy_rain_days": "🌧️ Heavy rain days", "cold_nights": "🥶 Cold nights"}[x],
)
dist_metric = f"district_{metric}"

fig = px.bar(
    merged, x="block", y=metric, color="district",
    title="Event count per block (bars) vs. district-file count (line)",
)
fig.update_layout(xaxis_tickangle=-45)
# overlay district-level reference as a horizontal marker per district using a second trace
for d in merged["district"].unique():
    val = merged[merged["district"] == d][dist_metric].iloc[0]
    fig.add_hline(y=val, line_dash="dot", annotation_text=f"{d} district file = {val}",
                  annotation_position="top left")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    merged[["district", "block", metric, dist_metric]].sort_values(metric, ascending=False),
    use_container_width=True, hide_index=True,
)

under = merged[merged[metric] > merged[dist_metric]]
if len(under):
    worst = under.sort_values(metric, ascending=False).iloc[0]
    st.error(
        f"📌 **{worst['block']}** ({worst['district']}) actually had **{int(worst[metric])}** "
        f"such days, but the district file only shows **{int(worst[dist_metric])}** — "
        f"an advisory based on district data alone would have under-counted this risk."
    )
