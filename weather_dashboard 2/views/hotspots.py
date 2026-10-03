"""Which blocks are always hotter / colder / wetter / windier than their neighbours?"""
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import LABELS, UNITS, YEARS
from utils.maps import make_map
from utils.style import inject_css, hero, step, tip, say, plot, need_data, DIST_COLOR

inject_css()
df = need_data()
hero("🔥", "Spatial Hotspots", "Which blocks are quietly always a bit higher or lower than the rest?")

step("1️⃣  Choose what to look at")
label = st.selectbox("Weather variable", list(LABELS))
key, unit = LABELS[label], UNITS[LABELS[label]]
d = df
ny = max(d["Year"].nunique(), 1)
agg = d.groupby(["District", "Block"])[f"{key}_blk"].agg("sum" if key == "Rain" else "mean").reset_index(name="v")
if key == "Rain":
    agg["v"] = agg["v"] / ny
agg["gap"] = agg["v"] - agg["v"].mean()          # compared with the average of all 24 blocks
lim = float(agg["gap"].abs().max()) or 1.0

step("2️⃣  Map and ranking (red = higher than average, blue = lower)")
c1, c2 = st.columns([1.2, 1])
with c1:
    vals = dict(zip(agg["Block"], agg["gap"]))
    hov = {r.Block: f"{r.District}<br>Value: {r.v:.1f} {unit}<br>Vs average: {r.gap:+.1f} {unit}" for r in agg.itertuples()}
    fig = make_map(None, vals, "RdBu_r" if key not in ("Rain", "RH-I", "RH-II") else "BrBG", -lim, lim, unit,
                   f"{label}: block vs overall average", hover=hov, height=520)
    plot(fig)
with c2:
    g = agg.sort_values("gap")
    fb = px.bar(g, x="gap", y="Block", orientation="h", color="District", color_discrete_map=DIST_COLOR,
                labels={"gap": f"Gap vs average ({unit})"})
    fb.update_layout(height=520, margin=dict(t=10, b=10), legend=dict(orientation="h", y=1.06, title=None))
    plot(fb)

hi, lo = agg.sort_values("gap").iloc[-1], agg.sort_values("gap").iloc[0]
say(f"<b>Highest:</b> {hi.Block} ({hi.District}) is {hi.gap:+.1f} {unit} above the average block. "
    f"<b>Lowest:</b> {lo.Block} ({lo.District}) is {lo.gap:+.1f} {unit} below it.")
tip("Galteshwar and Vaso have no boundary on the map but appear in the ranking.")
