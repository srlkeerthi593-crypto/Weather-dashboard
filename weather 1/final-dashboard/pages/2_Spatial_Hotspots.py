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

st.markdown(f"### 1️⃣ Every block, ranked — {SIMPLE_NAMES[var]}")
st.caption(
    f"For every day, we work out the average {SIMPLE_NAMES[var].split(' ',1)[-1] if ' ' in SIMPLE_NAMES[var] else SIMPLE_NAMES[var]} "
    f"across ALL blocks in a district. Each bar below is one block's typical gap from that number, in {unit or 'its unit'}."
)
fig = px.bar(
    dev, x="block", y=dev_col, color="direction",
    color_discrete_map={"Above district average": BAD_COLOR, "Below district average": "#2563EB"},
    title="How far off is each block from its own district's average, on a typical day?",
    labels={dev_col: f"Difference ({unit})", "block": ""},
)
fig.add_hline(y=0, line_dash="dash", line_color="gray")
fig.update_layout(xaxis_tickangle=-30, height=420)
st.plotly_chart(fig, use_container_width=True)

biggest = dev.iloc[(dev[dev_col]).abs().argsort()[::-1]].head(1).iloc[0]
plain_box(
    f"🔴 <b>Red bars</b> = that block usually reads <b>higher</b> than its own district's average. "
    f"🔵 <b>Blue bars</b> = it usually reads <b>lower</b>. The taller the bar (either direction), the more "
    f"that block's real weather differs from what a single district number would suggest. "
    f"<b>{biggest['block']}</b> ({biggest['district']}) stands out the most — it's usually "
    f"<b>{biggest[dev_col]:+.2f}{unit}</b> away from the rest of its district, every day.",
    icon="📌",
)

with st.expander("📋 See the full table"):
    st.dataframe(
        dev.sort_values(dev_col).rename(columns={"district": "District", "block": "Block", dev_col: f"Gap from district average ({unit})", "direction": "Direction"}),
        use_container_width=True, hide_index=True,
    )

st.divider()
st.markdown("### 2️⃣ How this plays out over time, one block at a time")
pick_district = st.selectbox("Pick a district", sorted(sub["district"].unique()))
d_sub = sub[sub["district"] == pick_district].copy()
d_sub["district_daily_mean"] = d_sub.groupby("date")[var].transform("mean")
d_sub["deviation"] = d_sub[var] - d_sub["district_daily_mean"]
# smooth over a week so the pattern is readable instead of a jagged daily zig-zag
d_sub["deviation_smooth"] = d_sub.groupby("block")["deviation"].transform(lambda s: s.rolling(7, min_periods=1, center=True).mean())

st.caption(
    f"Every block in {pick_district}, shown in its **own separate mini-chart** (not overlapping) so each one is easy to read on its own. "
    "Smoothed over a week to show the real trend, not daily noise. ⚠️ These wiggles are often small on purpose — "
    "the table right below the chart spells out exactly what each panel means in plain words, since the visual "
    "difference between panels can be subtle."
)

# compute per-block summary stats used both for facet subtitles and the plain-word table below
block_stats = d_sub.groupby("block").agg(
    avg_gap=("deviation", "mean"),
    pct_above=("deviation", lambda s: (s > 0).mean() * 100),
).reset_index()

fig2 = px.line(
    d_sub, x="date", y="deviation_smooth", facet_col="block", facet_col_wrap=4,
    labels={"deviation_smooth": f"Diff. ({unit})", "date": ""},
    color_discrete_sequence=["#7C3AED"],
)
# put each block's average gap right in its own panel title, so the number is right there next to the wiggle
avg_lookup = dict(zip(block_stats["block"], block_stats["avg_gap"]))
fig2.for_each_annotation(lambda a: a.update(
    text=f"{a.text.split('=')[-1]} (avg {avg_lookup.get(a.text.split('=')[-1], 0):+.2f}{unit})",
    font_size=12,
))
fig2.add_hline(y=0, line_dash="dash", line_color="gray")
fig2.update_yaxes(matches="y")
fig2.update_xaxes(showticklabels=True)
fig2.update_layout(height=580, showlegend=False, margin=dict(t=40))
st.plotly_chart(fig2, use_container_width=True)

plain_box(
    "A panel that stays consistently <b>above</b> or <b>below</b> the dashed zero line (instead of hovering "
    "right on it) is a block with a steady local pattern — a real hot/cold/wet spot, not just random noise. "
    "The number next to each block's name above is its <b>average gap</b> from the district — the single most "
    "useful number if the wiggly line itself is hard to read."
)

def _classify(row):
    if row["pct_above"] >= 65:
        return f"Usually reads <b>higher</b> than {pick_district}'s daily average ({row['pct_above']:.0f}% of days)"
    elif row["pct_above"] <= 35:
        return f"Usually reads <b>lower</b> than {pick_district}'s daily average ({row['pct_above']:.0f}% of days)"
    else:
        return "No steady pattern — bounces above and below the district average"

block_stats["In plain words"] = block_stats.apply(_classify, axis=1)
block_stats = block_stats.sort_values("avg_gap", ascending=False)
st.markdown("##### 📋 What each panel above means, in one line")
st.dataframe(
    block_stats.rename(columns={"block": "Block", "avg_gap": f"Average gap ({unit})"})[["Block", f"Average gap ({unit})", "In plain words"]],
    use_container_width=True, hide_index=True,
)
