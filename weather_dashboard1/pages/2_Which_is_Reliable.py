"""Simple traffic-light scorecard: how well does the district number match the blocks?"""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import VARIABLES, UNITS, YEARS, scorecard, rain_scores
from utils.style import (inject_css, hero, step, tip, say, plot, table, need_data, verdict, kpi, VAR_ICON, VAR_COLOR,
                         DIST_COLOR)

st.set_page_config(page_title="Which is Reliable?", page_icon="🏆", layout="wide")
inject_css()
df = need_data()
hero("🏆", "Which one is reliable?", "A simple traffic-light check: can the district number stand in for a block?")

step("1️⃣  Choose the area")
area = st.radio("Area", ["All three districts"] + sorted(df["District"].unique()), horizontal=True)
d = df if area.startswith("All") else df[df["District"] == area]

# ── scorecard ──
step("2️⃣  Scorecard – how often is the district number 'close enough'?")
sc = scorecard(d, [])
TOL = {"Rain": "same rain / no-rain call", "Tmax": "within ±2 °C", "Tmin": "within ±2 °C", "RH-I": "within ±10 %",
       "RH-II": "within ±10 %", "Wind": "within ±3 km/h"}
cols = st.columns(6)
for col, (_, r) in zip(cols, sc.iterrows()):
    emoji, word, color = verdict(r["Within"])
    col.markdown(f'<div class="kpi" style="background:{VAR_COLOR[r.Variable]}"><span style="font-size:1.6rem">{VAR_ICON[r.Variable]}</span>'
                 f'<b>{r["Within"]:.0f}%</b>{r.Variable}<br><span style="font-size:.85rem">{emoji} {word}</span></div>',
                 unsafe_allow_html=True)
tip("Each big number = % of days the district value is <b>close enough</b> to the block "
    "(temperature ±2 °C, humidity ±10 %, wind ±3 km/h, rain = same rain / no-rain call). "
    "🟢 85%+ very close · 🟡 65–85% roughly close · 🔴 below 65% often different.")

view = sc[["Variable", "Within", "Corr", "MAE", "Bias"]].copy()
view["Variable"] = [f"{VAR_ICON[v]} {v} ({UNITS[v]})" for v in view["Variable"]]
view["Verdict"] = [verdict(w)[0] + " " + verdict(w)[1] for w in view["Within"]]
view["Bias meaning"] = ["block higher than district" if b > 0.05 else "block lower than district" if b < -0.05 else "no steady gap"
                        for b in view["Bias"]]
view = view.rename(columns={"Within": "Days close enough (%)", "Corr": "Moves together (r)", "MAE": "Typical gap", "Bias": "Average gap"})
view = view[["Variable", "Verdict", "Days close enough (%)", "Moves together (r)", "Typical gap", "Average gap", "Bias meaning"]].round(2)
table(view)
say("<b>Moves together (r)</b> close to 1 means when the block gets hotter/wetter, the district number does too. "
    "<b>Typical gap</b> is the average size of the difference, in the variable's own unit. "
    "<b>Average gap</b> (block − district) shows whether the block is usually above (+) or below (−) the district.")

# ── by block ──
step("3️⃣  Which blocks does the district number describe best and worst?")
bb = scorecard(d, ["District", "Block"])
rank = bb.groupby(["District", "Block"])["Within"].mean().reset_index().sort_values("Within")
fig = px.bar(rank, x="Within", y="Block", orientation="h", color="District", color_discrete_map=DIST_COLOR,
             labels={"Within": "Average % of days close enough (all variables)"})
fig.update_layout(height=max(320, 28 * len(rank)), margin=dict(t=10, b=10), legend=dict(orientation="h", y=1.08, title=None))
plot(fig)
w, b_ = rank.iloc[0], rank.iloc[-1]
say(f"District value fits <b>{b_.Block}</b> best ({b_.Within:.0f}% of days close) and <b>{w.Block}</b> worst ({w.Within:.0f}%). "
    "Blocks at the bottom are where local weather differs most from the district picture.")

# ── by year ──
step("4️⃣  Is it getting better over the years?")
yr = scorecard(d, ["Year"])
yr["Variable"] = [f"{VAR_ICON[v]} {v}" for v in yr["Variable"]]
fy = px.bar(yr, x="Variable", y="Within", color=yr["Year"].astype(str), barmode="group",
            labels={"Within": "Days close enough (%)", "color": "Year"},
            color_discrete_sequence=["#7C3AED", "#06B6D4", "#F97316"])
fy.update_layout(height=340, margin=dict(t=10, b=10), legend=dict(orientation="h", y=1.1, title=None))
plot(fy)

# ── rainfall ──
step("5️⃣  Rain: did the district number catch the rainy days?")
rs = rain_scores(d["Rain_blk"], d["Rain_dst"])
k1, k2, k3, k4 = st.columns(4)
kpi(k1, "Rainy days caught", f"{rs['PoD']*100:.0f}%", "#2563EB")
kpi(k2, "Rainy days missed", f"{rs['Miss']*100:.0f}%", "#EF4444")
kpi(k3, "Dry days wrongly called rainy", f"{rs['POFD']*100:.0f}%", "#F59E0B")
kpi(k4, "Overall skill score (HK)", f"{rs['HK']:.2f}", "#10B981")
tip("Rainy day = 2.5 mm or more. The HK score is 1 for a perfect forecast and 0 for no skill. "
    "The district number rarely misses rain but often shows rain when a block stays dry.")

# ── conclusion ──
step("🏁  Overall conclusion")
best = sc.sort_values("Within").iloc[-1]
worst = sc.sort_values("Within").iloc[0]
say(f"The district number follows the blocks well: correlation is {sc['Corr'].min():.2f}–{sc['Corr'].max():.2f} across variables. "
    f"It is most dependable for <b>{best.Variable}</b> ({best.Within:.0f}% of days close) and least for <b>{worst.Variable}</b> "
    f"({worst.Within:.0f}%). The district value is a smoothed average, so it is <b>stable but hides local differences</b>; "
    "the block data keeps that local detail. For decisions at farm level the block data is the more precise guide.")
