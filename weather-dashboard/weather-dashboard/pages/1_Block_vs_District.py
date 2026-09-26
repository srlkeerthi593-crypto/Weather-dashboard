import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import load_blockwise, load_districtwise, merged_block_district, VARIABLES
from utils.metrics import block_vs_district_by_group, accuracy_metrics
from utils.style import (
    inject_css, hero, plain_box, glossary_expander,
    BLOCK_COLOR, DISTRICT_COLOR, SIMPLE_NAMES, UNITS,
    match_rating, correlation_sentence, bias_sentence,
)

st.set_page_config(page_title="Block vs District", page_icon="🔍", layout="wide")
inject_css()
hero("🔍", "Block vs. District", "Pick your local area (block) and see its real weather right next to your district's average — as two separate, clearly-labeled charts.", gradient=(BLOCK_COLOR, "#60A5FA"))
plain_box("<b><span style='color:#2563EB'>Blue = Block</span></b> (your local area, the real reading) · "
          "<b><span style='color:#F97316'>Orange = District</span></b> (the bigger area's average). "
          "Same colors are used on every page.")
glossary_expander()

block_df = load_blockwise()
dist_df = load_districtwise()
merged = merged_block_district(block_df, dist_df)

# ---- Friendly pickers -------------------------------------------------
st.markdown("### 1️⃣ Choose what to look at")
c1, c2, c3 = st.columns([1.2, 1, 1])
with c1:
    var = st.selectbox("Weather variable", list(VARIABLES.keys()), format_func=lambda k: SIMPLE_NAMES[k])
with c2:
    district = st.selectbox("District (bigger area)", sorted(merged["district"].unique()))
with c3:
    block = st.selectbox("Block (your local area)", sorted(merged[merged["district"] == district]["block"].unique()))

years = st.multiselect("Years to include", sorted(merged["year"].unique()), default=sorted(merged["year"].unique()))
unit = UNITS.get(var, "")

one = merged[(merged["district"] == district) & (merged["block"] == block) & (merged["year"].isin(years))].sort_values("date")

if one.empty:
    st.warning("No data for this combination — try different filters.")
    st.stop()

m = accuracy_metrics(one[var], one[f"{var}_dist"])

st.divider()
st.markdown(f"### 2️⃣ How well does **{district}** district data represent **{block}**?")

rc1, rc2, rc3 = st.columns(3)
emoji, label, color, sent = match_rating(var, m["RMSE"])
with rc1:
    with st.container(border=True):
        st.markdown(f"#### {emoji} Overall match: {label}")
        st.write(sent)

emoji2, pct, sent2 = correlation_sentence(m["Correlation"])
with rc2:
    with st.container(border=True):
        st.markdown(f"#### {emoji2} Move together: {pct}")
        st.write(sent2)

with rc3:
    with st.container(border=True):
        st.markdown("#### ⚖️ Who reads higher?")
        st.write(bias_sentence(var, m["Mean_Bias"]))

with st.expander("🔢 Show me the raw technical numbers"):
    st.dataframe(
        {"RMSE (avg daily error)": [m["RMSE"]], "Correlation": [m["Correlation"]], "Mean Bias": [m["Mean_Bias"]], "Days compared": [m["N"]]},
        hide_index=True,
    )

st.divider()
st.markdown(f"### 3️⃣ See them side by side — {SIMPLE_NAMES[var]}")
st.caption("Two separate charts on purpose: one is the real local reading, the other is the zoomed-out district average. Compare their shape, not just the numbers.")

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    fig_b = px.area(
        one, x="date", y=var,
        title=f"📍 {block} — actual local reading",
        labels={var: f"{SIMPLE_NAMES[var]} ({unit})", "date": ""},
    )
    fig_b.update_traces(line_color=BLOCK_COLOR, fillcolor="rgba(37,99,235,0.15)")
    fig_b.update_layout(height=380, showlegend=False)
    st.plotly_chart(fig_b, use_container_width=True)
with chart_col2:
    fig_d = px.area(
        one, x="date", y=f"{var}_dist",
        title=f"🏙️ {district} — district-wide average",
        labels={f"{var}_dist": f"{SIMPLE_NAMES[var]} ({unit})", "date": ""},
    )
    fig_d.update_traces(line_color=DISTRICT_COLOR, fillcolor="rgba(249,115,22,0.15)")
    fig_d.update_layout(height=380, showlegend=False)
    st.plotly_chart(fig_d, use_container_width=True)

st.markdown("#### 📏 The daily gap between them")
one = one.copy()
one["gap"] = one[var] - one[f"{var}_dist"]
fig_gap = go.Figure()
fig_gap.add_trace(go.Bar(
    x=one["date"], y=one["gap"],
    marker_color=[BLOCK_COLOR if v >= 0 else DISTRICT_COLOR for v in one["gap"]],
    name="Block − District",
))
fig_gap.update_layout(
    height=260, title=f"Block reading minus District reading, each day ({unit})",
    yaxis_title=f"Difference ({unit})", showlegend=False,
)
fig_gap.add_hline(y=0, line_color="gray")
st.plotly_chart(fig_gap, use_container_width=True)
plain_box("Bars <b><span style='color:#2563EB'>above zero</span></b> = the block was actually higher than the district said. "
          "Bars <b><span style='color:#F97316'>below zero</span></b> = the block was actually lower.")

with st.expander("👀 Prefer to see both lines on ONE chart instead?"):
    fig_combo = px.line(
        one, x="date", y=[var, f"{var}_dist"],
        color_discrete_map={var: BLOCK_COLOR, f"{var}_dist": DISTRICT_COLOR},
        labels={"value": f"{SIMPLE_NAMES[var]} ({unit})", "date": "Date", "variable": "Source"},
    )
    fig_combo.for_each_trace(lambda t: t.update(name={var: f"📍 {block} (block)", f"{var}_dist": f"🏙️ {district} (district)"}.get(t.name, t.name)))
    fig_combo.update_layout(height=380, hovermode="x unified")
    st.plotly_chart(fig_combo, use_container_width=True)

st.divider()
st.markdown("### 4️⃣ How does EVERY block in this district compare?")
table = block_vs_district_by_group(merged[merged["district"] == district], var, ["block"]).sort_values("RMSE", ascending=False)
table["Match"] = table["RMSE"].apply(lambda r: match_rating(var, r)[0] + " " + match_rating(var, r)[1])
fig_all = px.bar(
    table, x="block", y="RMSE", color="Match",
    color_discrete_map={"🟢 Good match": "#16A34A", "🟡 Okay, but not perfect": "#F59E0B", "🔴 Poor match": "#DC2626"},
    title=f"How reliable is {district}'s district data for each of its blocks?",
    labels={"RMSE": f"Avg. daily error ({unit})", "block": ""},
)
fig_all.update_layout(xaxis_tickangle=-30, height=380)
st.plotly_chart(fig_all, use_container_width=True)
st.dataframe(table[["block", "Match", "RMSE", "Correlation", "Mean_Bias"]], use_container_width=True, hide_index=True)
