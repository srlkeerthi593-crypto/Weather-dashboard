import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise, VARIABLES
from utils.metrics import block_deviation_from_district

st.set_page_config(page_title="Spatial Hotspots", page_icon="🗺️", layout="wide")
st.title("🗺️ Spatial Hotspots")

st.markdown(
    """
District averages can hide blocks that are consistently different from
their neighbours. This page finds those blocks.

For every block, we compare its daily value to the **average of all blocks
in its district on that same day** (not the district file — this isolates
purely spatial differences). A block sitting far from zero is a genuine
local hotspot / cold-spot that a district-wide advisory would get wrong.
"""
)

block_df = load_blockwise()
var = st.selectbox("Variable", list(VARIABLES.keys()), format_func=lambda k: VARIABLES[k])
years = st.multiselect("Years", sorted(block_df["year"].unique()), default=sorted(block_df["year"].unique()))
sub = block_df[block_df["year"].isin(years)]

dev = block_deviation_from_district(sub, var)
dev_col = f"avg_deviation_{var}"

fig = px.bar(
    dev, x="block", y=dev_col, color="district",
    title=f"Average deviation from district mean — {VARIABLES[var]}",
    labels={dev_col: f"Deviation ({VARIABLES[var]})"},
)
fig.add_hline(y=0, line_dash="dash", line_color="gray")
fig.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)

biggest = dev.iloc[(dev[dev_col]).abs().argsort()[::-1]].head(1).iloc[0]
st.warning(
    f"📌 Biggest outlier: **{biggest['block']}** ({biggest['district']}) sits "
    f"**{biggest[dev_col]:+.2f}** away from its district's own daily average "
    f"for {VARIABLES[var]}. A district-level advisory would be off by roughly "
    f"this much for that block, every day."
)

st.dataframe(dev.sort_values(dev_col), use_container_width=True, hide_index=True)

st.divider()
st.subheader("How the deviation moves through the year")
pick_district = st.selectbox("District", sorted(sub["district"].unique()))
d_sub = sub[sub["district"] == pick_district].copy()
d_sub["district_daily_mean"] = d_sub.groupby("date")[var].transform("mean")
d_sub["deviation"] = d_sub[var] - d_sub["district_daily_mean"]

fig2 = px.line(
    d_sub, x="date", y="deviation", color="block",
    title=f"{pick_district} — daily deviation from district average, by block",
    labels={"deviation": f"Deviation ({VARIABLES[var]})", "date": "Date"},
)
fig2.add_hline(y=0, line_dash="dash", line_color="gray")
st.plotly_chart(fig2, use_container_width=True)
