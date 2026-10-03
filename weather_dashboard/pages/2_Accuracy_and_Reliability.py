"""Scorecard: how close are district and block data, and which is more reliable?"""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import (VARIABLES, UNITS, YEARS, SEASON_ORDER, TOLERANCE, continuous_metrics,
                               rain_scores, scorecard)
from utils.style import inject_css, hero, plain_box, glossary, need_data

st.set_page_config(page_title="Accuracy & Reliability", page_icon="🎯", layout="wide")
inject_css()
df = need_data()
hero("🎯", "Accuracy & Reliability",
     "Block data is the reference. How closely does the district data follow it – and when can you trust it?")
glossary()

c1, c2, c3 = st.columns(3)
dsel = c1.multiselect("Districts", sorted(df["District"].unique()), default=sorted(df["District"].unique()))
ysel = c2.multiselect("Years", YEARS, default=YEARS)
ssel = c3.selectbox("Season", ["All year"] + SEASON_ORDER)
d = df[df["District"].isin(dsel) & df["Year"].isin(ysel)]
if ssel != "All year":
    d = d[d["Season"] == ssel]
if d.empty:
    st.warning("No data for this selection.")
    st.stop()

# ───────── 1. overall scorecard ─────────
st.markdown("### 1️⃣ Overall scorecard")
sc = scorecard(d, [])
sc["Unit"] = sc["Variable"].map(UNITS)
show = sc[["Variable", "Unit", "RMSE", "MAE", "Bias", "Corr", "Within", "N"]].rename(
    columns={"Bias": "Bias (block − district)", "Corr": "Correlation r", "Within": "Within tolerance %"})
st.dataframe(show.style.format({c: "{:.2f}" for c in show.columns if c not in ("Variable", "Unit", "N")})
             .background_gradient(subset=["Correlation r", "Within tolerance %"], cmap="Greens"),
             hide_index=True, use_container_width=True)

# ───────── 2. verdict ─────────
def verdict(r, w):
    if np.isnan(r):
        return "n/a"
    if r >= 0.90 and w >= 80:
        return "✅ Reliable"
    if r >= 0.75 and w >= 60:
        return "🟡 Use with care"
    return "🔴 Weak"

bb = scorecard(d, ["Block"])
worst = bb.loc[bb.groupby("Variable")["Within"].idxmin()].set_index("Variable")
ver = sc.set_index("Variable")
vt = pd.DataFrame({"Correlation r": ver["Corr"], "Within tolerance %": ver["Within"],
                   "Least-matched block": worst["Block"], "…matches only %": worst["Within"]})
vt["District data is…"] = [verdict(r, w) for r, w in zip(vt["Correlation r"], vt["Within tolerance %"])]
st.markdown("### 2️⃣ Can the district number stand in for a block?")
st.dataframe(vt.style.format({"Correlation r": "{:.2f}", "Within tolerance %": "{:.1f}", "…matches only %": "{:.1f}"}),
             use_container_width=True)
plain_box("<b>Rule of thumb used for the verdict:</b> ✅ correlation ≥ 0.90 <i>and</i> district within tolerance on ≥ 80 % of days; "
          "🟡 ≥ 0.75 and ≥ 60 %; 🔴 otherwise. Tolerance = ±2 °C temperature, ±10 % humidity, ±3 km/h wind, "
          "same rain/no-rain call (≥ 2.5 mm). These cut-offs are our own choice – adjust them to your needs.")

# ───────── 3. which blocks are least represented ─────────
st.markdown("### 3️⃣ Where does the district number fit worst? (block × variable)")
metric = st.radio("Show", ["Within tolerance %", "Correlation", "RMSE"], horizontal=True)
colname = {"Within tolerance %": "Within", "Correlation": "Corr", "RMSE": "RMSE"}[metric]
heat = bb.pivot(index="Block", columns="Variable", values=colname)[list(VARIABLES.values())]
heat = heat.loc[sorted(heat.index, key=lambda b: (d[d.Block == b].District.iloc[0], b))]
fig = px.imshow(heat, aspect="auto", text_auto=".2f",
                color_continuous_scale="RdYlGn" if metric != "RMSE" else "YlOrRd")
fig.update_layout(height=620, margin=dict(t=10))
st.plotly_chart(fig, use_container_width=True)
if metric == "RMSE":
    st.caption("RMSE is in each variable's own unit, so compare down a column, not across.")

# ───────── 4. year / season trend ─────────
st.markdown("### 4️⃣ Is the match improving or getting worse?")
v = st.selectbox("Variable", list(VARIABLES.values()))
base = df[df["District"].isin(dsel)]
tr = scorecard(base, ["Year", "Season"])
tr = tr[tr["Variable"] == v]
tr["Season"] = pd.Categorical(tr["Season"], SEASON_ORDER, ordered=True)
tabs = st.tabs(["RMSE", "Correlation", "Bias", "Within tolerance %"])
for tab, (m, lab) in zip(tabs, [("RMSE", "RMSE"), ("Corr", "Correlation"), ("Bias", "Bias"), ("Within", "Within tolerance %")]):
    f = px.bar(tr.sort_values("Season"), x="Season", y=m, color=tr["Year"].astype(str), barmode="group",
               labels={m: lab, "color": "Year"})
    f.update_layout(height=340, margin=dict(t=10))
    tab.plotly_chart(f, use_container_width=True)

# ───────── 5. rainfall categorical ─────────
st.markdown("### 5️⃣ Rainfall: rain / no-rain skill (threshold ≥ 2.5 mm)")
rows = []
for (y, s), sub in base.groupby(["Year", "Season"]):
    rows.append({"Year": y, "Season": s, **rain_scores(sub["Rain_blk"], sub["Rain_dst"])})
for y, sub in base.groupby("Year"):
    rows.append({"Year": y, "Season": "Annual", **rain_scores(sub["Rain_blk"], sub["Rain_dst"])})
rt = pd.DataFrame(rows)
rt["Season"] = pd.Categorical(rt["Season"], SEASON_ORDER + ["Annual"], ordered=True)
rt = rt.sort_values(["Season", "Year"])
rm = st.selectbox("Rain score", ["Ratio", "HK", "PoD", "POFD", "Miss", "CSI", "FAR"],
                  format_func=lambda s: {"Ratio": "Ratio score (%)", "HK": "Hanssen–Kuipers", "PoD": "Probability of detection",
                                         "POFD": "False-alarm rate (POFD)", "Miss": "Miss rate", "CSI": "CSI", "FAR": "False-alarm ratio"}[s])
f = px.bar(rt, x="Season", y=rm, color=rt["Year"].astype(str), barmode="group", labels={"color": "Year"})
f.update_layout(height=340, margin=dict(t=10))
st.plotly_chart(f, use_container_width=True)
st.caption("Scores are undefined (blank) when no rain ≥ 2.5 mm occurred in that season.")
with st.expander("Show the full rain table"):
    st.dataframe(rt.round(3), hide_index=True, use_container_width=True)

# ───────── 6. representativeness ─────────
st.markdown("### 6️⃣ Reliability check: how much do blocks differ *inside* a district?")
st.write("If blocks in one district disagree strongly with each other, a single district number cannot be right for all of them.")
rows = []
for k in VARIABLES.values():
    spread = base.groupby(["Date", "District"])[f"{k}_blk"].std().mean()          # avg day-to-day spread among blocks
    dm = base.groupby(["Date", "District"]).agg(b=(f"{k}_blk", "mean"), p=(f"{k}_dst", "first")).reset_index()
    rmse_avg = np.sqrt(((dm["b"] - dm["p"]) ** 2).mean())                          # district vs block average
    rmse_ind = scorecard(base, [])
    rmse_ind = rmse_ind[rmse_ind.Variable == k]["RMSE"].iloc[0]                    # district vs individual blocks
    rows.append({"Variable": k, "Unit": UNITS[k], "Spread among blocks (avg std)": spread,
                 "RMSE: district vs block-average": rmse_avg, "RMSE: district vs individual blocks": rmse_ind})
rp = pd.DataFrame(rows)
st.dataframe(rp.style.format({c: "{:.2f}" for c in rp.columns if c not in ("Variable", "Unit")}),
             hide_index=True, use_container_width=True)
plain_box("If <b>district vs individual blocks</b> is clearly larger than <b>district vs block-average</b>, "
          "the district number tracks the district as a whole but misses local differences – "
          "exactly the resolution gap this project studies.")
