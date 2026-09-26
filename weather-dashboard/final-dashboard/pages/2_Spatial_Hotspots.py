import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise, VARIABLES
from utils.metrics import block_deviation_from_district
from utils.style import inject_css, hero, plain_box, glossary_expander, SIMPLE_NAMES, UNITS, GOOD_COLOR, BAD_COLOR

st.set_page_config(page_title="Spatial Hotspots", page_icon="🗺️", layout="wide")
inject_css()
hero("🗺️", "Spatial Hotspots", "Which local areas are quietly always hotter, colder or wetter than the rest of their district?", gradient=("#7C3AED", "#C084FC"))
plain_box(
    "A district's 'average' can hide the fact that one block is always a bit different from its neighbours. "
    "This page compares each block to <b>the average of its own district's blocks that day</b> — "
    "so we can spot true local hot/cold spots."
)
glossary_expander()

block_df = load_blockwise()
c1, c2 = st.columns(2)
with c1:
    var = st.selectbox("What to check", list(VARIABLES.keys()), format_func=lambda k: SIMPLE_NAMES[k])
with c2:
    years = st.multiselect("Years", sorted(block_df["year"].unique()), default=sorted(block_df["year"].unique()))
sub = block_df[block_df["year"].isin(years)]
unit = UNITS.get(var, "")

dev = block_deviation_from_district(sub, var)
dev_col = f"avg_deviation_{var}"
dev["direction"] = dev[dev_col].apply(lambda v: "Above district average" if v >= 0 else "Below district average")

st.markdown(f"### Every block, ranked — {SIMPLE_NAMES[var]}")
fig = px.bar(
    dev, x="block", y=dev_col, color="direction",
    color_discrete_map={"Above district average": BAD_COLOR, "Below district average": "#2563EB"},
    title=f"How far off is each block from its district's own average?",
    labels={dev_col: f"Difference ({unit})", "block": ""},
)
fig.add_hline(y=0, line_dash="dash", line_color="gray")
fig.update_layout(xaxis_tickangle=-30, height=420)
st.plotly_chart(fig, use_container_width=True)

biggest = dev.iloc[(dev[dev_col]).abs().argsort()[::-1]].head(1).iloc[0]
plain_box(
    f"<b>{biggest['block']}</b> ({biggest['district']}) stands out the most — it's usually "
    f"<b>{biggest[dev_col]:+.2f}{unit}</b> away from what the rest of its district is doing. "
    f"A single district-wide number would be misleading for this block, every day.",
    icon="📌",
)

with st.expander("📋 See the full table"):
    st.dataframe(dev.sort_values(dev_col), use_container_width=True, hide_index=True)

st.divider()
st.markdown("### 📈 How this plays out over the year, one district at a time")
pick_district = st.selectbox("Pick a district", sorted(sub["district"].unique()))
d_sub = sub[sub["district"] == pick_district].copy()
d_sub["district_daily_mean"] = d_sub.groupby("date")[var].transform("mean")
d_sub["deviation"] = d_sub[var] - d_sub["district_daily_mean"]

fig2 = px.line(
    d_sub, x="date", y="deviation", color="block",
    title=f"{pick_district} — each block's daily gap from its district's average",
    labels={"deviation": f"Difference ({unit})", "date": ""},
)
fig2.add_hline(y=0, line_dash="dash", line_color="gray")
fig2.update_layout(height=420, hovermode="x unified")
st.plotly_chart(fig2, use_container_width=True)
plain_box("Lines that stay consistently above or below the zero line (instead of crossing back and forth) are blocks with a steady local pattern — not just random noise.")
