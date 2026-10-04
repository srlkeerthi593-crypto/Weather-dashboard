"""Choose district -> two maps (block values vs district value) -> click a block -> compare."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import LABELS, UNITS, VARIABLES, YEARS, RAIN_THRESHOLD, TOLERANCE, load_geojson, continuous_metrics
from utils.maps import make_map, clicked_block
from utils.style import (inject_css, hero, step, tip, say, plot, table, need_data, verdict, VAR_ICON,
                         BLOCK_COLOR, DISTRICT_COLOR, GOOD, BAD)

st.set_page_config(page_title="Block vs District", page_icon="🗺️", layout="wide")
inject_css()
df = need_data()
mapped = {f["properties"]["block"] for f in load_geojson()["features"]}

hero("🗺️", "Block vs District", "Pick a district, then click any block on the map to compare it with the district.")

# ── Step 1 ──
step("1️⃣  Choose a district and what to look at")
a, b, c = st.columns([1.6, 1.6, 1.2])
district = a.radio("District", sorted(df["District"].unique()), horizontal=True)
var_label = b.selectbox("Weather variable", list(LABELS))
year = c.selectbox("Year", ["All years"] + YEARS)
key, unit = LABELS[var_label], UNITS[LABELS[var_label]]

d = df[df["District"] == district]
if year != "All years":
    d = d[d["Year"] == year]
ny = max(d["Year"].nunique(), 1)

def agg_value(x):
    return x.sum() / ny if key == "Rain" else x.mean()

blocks = sorted(d["Block"].unique())
bval = {bl: agg_value(d[d.Block == bl][f"{key}_blk"]) for bl in blocks}
dval = agg_value(d[f"{key}_dst"].groupby(d["Date"]).first())     # one district value per day
diff = {bl: bval[bl] - dval for bl in blocks}
what = "total per year" if key == "Rain" else "average"

# keep selected block in session
skey = f"sel_{district}"
if st.session_state.get(skey) not in blocks:
    st.session_state[skey] = blocks[0]

# ── Step 2: two maps ──
step("2️⃣  Compare the maps – left: each block's own value, right: the one district value")
allv = list(bval.values()) + [dval]
zmin, zmax = min(allv), max(allv)
if zmin == zmax:
    zmax = zmin + 1
scale = {"Rain": "Blues", "Tmax": "YlOrRd", "Tmin": "PuBu", "RH-I": "Purples", "RH-II": "RdPu", "Wind": "Greens"}[key]
m1, m2 = st.columns(2)
with m1:
    fig1 = make_map(district, bval, scale, zmin, zmax, unit, f"📍 Blocks – {var_label} ({what})",
                    selected=st.session_state[skey],
                    hover={bl: f"Block value: {bval[bl]:.1f} {unit}<br>Gap vs district: {diff[bl]:+.1f} {unit}" for bl in blocks})
    ev = plot(fig1, key=f"map_{district}_{key}", select=True)
with m2:
    flat = {bl: dval for bl in bval}
    fig2 = make_map(district, flat, scale, zmin, zmax, unit, f"🏙️ District – {var_label} ({what})",
                    hover={bl: f"District value: {dval:.1f} {unit}" for bl in blocks})
    plot(fig2, key=f"map2_{district}_{key}")
tip("Same colour scale on both maps. If a block on the left is darker or lighter than the flat district map on the right, "
    "that block differs from the district. <b>Click a block on the left map</b> to select it.")
miss = [bl for bl in blocks if bl not in mapped]
if miss:
    st.caption(f"ℹ️ No boundary available for {', '.join(miss)} (very new talukas) – pick them from the list below.")

click = clicked_block(ev)
if click in blocks and st.session_state.get(f"lc_{district}") != click:
    st.session_state[skey] = click
    st.session_state[f"lc_{district}"] = click
    st.rerun()

# ── gap bar chart ──
gap = pd.DataFrame({"Block": list(diff), "Gap": list(diff.values())}).sort_values("Gap")
gap["Direction"] = np.where(gap["Gap"] >= 0, "Block higher than district", "Block lower than district")
fg = px.bar(gap, x="Gap", y="Block", orientation="h", color="Direction",
            color_discrete_map={"Block higher than district": "#F97316", "Block lower than district": "#2563EB"},
            labels={"Gap": f"Block − district ({unit})"}, title=f"How far is each block from the {district} value?")
fg.update_layout(height=max(260, 32 * len(gap)), margin=dict(t=45, b=10), legend=dict(orientation="h", y=-0.2, title=None))
plot(fg)

# ── Step 3: side-by-side cards ──
block = st.selectbox("3️⃣  Selected block (click the map or choose here)", blocks, key=skey)
step(f"3️⃣  {block} (block)  vs  {district} (district)")
bd = d[d.Block == block]

def rows(sfx):
    out = []
    for k in VARIABLES.values():
        col = bd[f"{k}_{sfx}"]
        v = col.sum() / ny if k == "Rain" else col.mean()
        out.append((k, v))
    return dict(out)

sb, sd = rows("blk"), rows("dst")

def card(title, tag, color, vals, other=None):
    trs = ""
    for k in VARIABLES.values():
        name = "Rain / year" if k == "Rain" else {"Tmax": "Max temp", "Tmin": "Min temp", "RH-I": "Morning humidity",
                                                  "RH-II": "Afternoon humidity", "Wind": "Wind speed"}[k]
        gap_txt = "" if other is None else f" <span style='opacity:.8;font-weight:400'>({vals[k]-other[k]:+.1f})</span>"
        trs += f"<tr><td>{VAR_ICON[k]} {name}</td><td>{vals[k]:.1f} {UNITS[k]}{gap_txt}</td></tr>"
    return (f'<div class="card" style="background:{color}"><span class="pill">{tag}</span><h3>{title}</h3>'
            f'<table>{trs}</table></div>')

c1, c2 = st.columns(2)
c1.markdown(card(f"📍 {block}", "LOCAL BLOCK (gap vs district in brackets)", "linear-gradient(135deg,#7c3aed,#c026d3)", sb, sd),
            unsafe_allow_html=True)
c2.markdown(card(f"🏙️ {district}", "WHOLE DISTRICT", "linear-gradient(135deg,#0284c7,#06b6d4)", sd), unsafe_allow_html=True)

# ── plain-language verdicts ──
step("🗣️  What does this mean in plain words?")
tol_txt = {"Tmax": "±2 °C", "Tmin": "±2 °C", "RH-I": "±10 %", "RH-II": "±10 %", "Wind": "±3 km/h", "Rain": "same rain / no-rain call"}
lines = []
for k in VARIABLES.values():
    m = continuous_metrics(bd[f"{k}_blk"], bd[f"{k}_dst"], k)
    emoji, word, _ = verdict(m["Within"])
    direction = "" if abs(m["Bias"]) < 0.05 else (" The block is usually a bit <b>higher</b>." if m["Bias"] > 0 else " The block is usually a bit <b>lower</b>.")
    lines.append(f"{emoji} <b>{VAR_ICON[k]} {k}</b>: district is <b>{word}</b> – on {m['Within']:.0f}% of days it is within "
                 f"{tol_txt[k]} of the block (r = {m['Corr']:.2f}).{direction}")
say("<br>".join(lines))

# ── chart over time ──
step("📈  Block and district over time")
mode = st.radio("Show", ["Monthly", "Daily"], horizontal=True)
s = bd[["Date", f"{key}_blk", f"{key}_dst"]].set_index("Date")
s = (s.resample("MS").sum() if key == "Rain" else s.resample("MS").mean()) if mode == "Monthly" else s
s = s.reset_index().melt("Date", var_name="Source", value_name=f"{var_label}")
nb, nd = f"{block} (block)", f"{district} (district)"
s["Source"] = s["Source"].map({f"{key}_blk": nb, f"{key}_dst": nd})
ft = px.line(s, x="Date", y=var_label, color="Source", color_discrete_map={nb: BLOCK_COLOR, nd: DISTRICT_COLOR})
ft.update_layout(height=380, legend=dict(orientation="h", y=1.12, title=None), margin=dict(t=30, b=10))
plot(ft)
