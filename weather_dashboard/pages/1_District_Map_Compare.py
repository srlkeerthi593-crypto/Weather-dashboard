"""Pick a district → see block boundaries → click a block → block vs district side by side."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import (LABELS, KEY_TO_LABEL, UNITS, VARIABLES, YEARS, SEASON_ORDER, RAIN_THRESHOLD,
                               load_geojson, block_table, continuous_metrics, rain_scores)
from utils.style import inject_css, hero, plain_box, glossary, need_data, BLOCK_COLOR, DISTRICT_COLOR

st.set_page_config(page_title="District Map & Compare", page_icon="🗺️", layout="wide")
inject_css()
df = need_data()
gj, btab = load_geojson(), block_table()

hero("🗺️", "District map · Block vs District",
     "Choose a district, click any block on the map, and see that block's weather next to the district's weather.")
glossary()

# ───────── filters ─────────
f1, f2, f3, f4 = st.columns([1.2, 1.6, 1.2, 1.2])
district = f1.selectbox("1️⃣ District", sorted(df["District"].unique()))
var_label = f2.selectbox("2️⃣ Variable to colour the map / chart", list(LABELS))
years = f3.multiselect("Year(s)", YEARS, default=YEARS)
season = f4.selectbox("Season", ["All year"] + SEASON_ORDER)
key = LABELS[var_label]
unit = UNITS[key]

d = df[(df["District"] == district) & (df["Year"].isin(years or YEARS))]
if season != "All year":
    d = d[d["Season"] == season]
if d.empty:
    st.warning("No data for this selection.")
    st.stop()
all_blocks = sorted(d["Block"].unique())
mapped = set(btab["block"])

# ───────── per-block summary for the map ─────────
def block_summary(sub):
    agg = "sum" if key == "Rain" else "mean"
    nyears = max(sub["Year"].nunique(), 1)
    val = sub[f"{key}_blk"].sum() / nyears if key == "Rain" else sub[f"{key}_blk"].mean()
    dist_val = (sub[f"{key}_dst"].sum() / nyears) if key == "Rain" else sub[f"{key}_dst"].mean()
    return val, dist_val

rows = []
for b, sub in d.groupby("Block"):
    v, dv = block_summary(sub)
    rows.append({"block": b, "value": v, "diff": v - dv})
msum = pd.DataFrame(rows)
metric_title = f"{var_label} – block " + ("total per year" if key == "Rain" else "average")

# ───────── layout ─────────
map_col, info_col = st.columns([1.05, 1.35], gap="large")

with map_col:
    st.markdown(f"##### 🧭 {district} district – click a block")
    geo = {"type": "FeatureCollection",
           "features": [f for f in gj["features"] if f["properties"]["district"] == district]}
    gdf = msum[msum["block"].isin(mapped)].copy()
    lons = [c[0] for f in geo["features"] for poly in
            (f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]])
            for ring in poly for c in ring]
    lats = [c[1] for f in geo["features"] for poly in
            (f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]])
            for ring in poly for c in ring]
    center = {"lon": (min(lons) + max(lons)) / 2, "lat": (min(lats) + max(lats)) / 2}
    span = max(max(lons) - min(lons), max(lats) - min(lats))
    zoom = float(np.clip(np.log2(422 / (span * 1.35)), 6, 10))

    fig = px.choropleth_map(gdf, geojson=geo, locations="block", color="value",
                            color_continuous_scale="YlOrRd" if key != "RH-I" and key != "RH-II" else "YlGnBu",
                            map_style="carto-positron", center=center, zoom=zoom, opacity=0.65,
                            labels={"value": f"{unit}"}, hover_data={"diff": ":.2f"})
    fig.update_traces(marker_line_width=1.5, marker_line_color="#334155",
                      hovertemplate="<b>%{location}</b><br>" + metric_title + ": %{z:.2f} " + unit
                                    + "<br>Block − district: %{customdata[0]:+.2f}<extra></extra>")
    # labels of the blocks
    lab = btab[btab["district"] == district]
    fig.add_trace(go.Scattermap(lon=lab["lon"], lat=lab["lat"], mode="text", text=lab["block"],
                                textfont=dict(size=11, color="#0f172a"), hoverinfo="skip", showlegend=False))
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=0, b=0),
                      coloraxis_colorbar=dict(title=unit, len=0.6))

    ev = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points",
                         key=f"map_{district}")
    clicked = None
    try:
        pts = ev.selection.points
        if pts:
            clicked = pts[0].get("location")
    except Exception:
        pass
    st.caption(f"Colour = {metric_title.lower()}. Hover for the block-minus-district difference.")
    missing = [b for b in all_blocks if b not in mapped]
    if missing:
        st.caption(f"ℹ️ No boundary polygon available for: {', '.join(missing)} (newer talukas missing from the public "
                   "boundary file). Pick them from the drop-down on the right.")

# keep click and drop-down in sync
skey = f"block_sel_{district}"
if clicked in all_blocks and st.session_state.get(f"last_click_{district}") != clicked:
    st.session_state[skey] = clicked
    st.session_state[f"last_click_{district}"] = clicked
if st.session_state.get(skey) not in all_blocks:
    st.session_state[skey] = all_blocks[0]

with info_col:
    block = st.selectbox("📍 Selected block (click the map or choose here)", all_blocks, key=skey)
    b = d[d["Block"] == block]
    nyears = max(b["Year"].nunique(), 1)

    def summary(frame, sfx):
        out = {}
        for k in VARIABLES.values():
            col = frame[f"{k}_{sfx}"]
            out[k] = col.sum() / nyears if k == "Rain" else col.mean()
        out["RainDays"] = (frame[f"Rain_{sfx}"] >= RAIN_THRESHOLD).sum() / nyears
        return out

    sb, sd = summary(b, "blk"), summary(b, "dst")
    c1, c2 = st.columns(2)
    for col, title, tag, s, colr in [(c1, f"📍 {block} (block)", "tag-b", sb, BLOCK_COLOR),
                                     (c2, f"🏙️ {district} (district)", "tag-d", sd, DISTRICT_COLOR)]:
        with col, st.container(border=True):
            st.markdown(f"<span class='{tag}'>{'LOCAL BLOCK' if tag=='tag-b' else 'WHOLE DISTRICT'}</span>", unsafe_allow_html=True)
            st.markdown(f"**{title}**")
            for k in VARIABLES.values():
                lbl = ("Rain / yr" if k == "Rain" else k)
                delta = None if col is c2 else None
                st.metric(lbl, f"{s[k]:.1f} {UNITS[k]}")
            st.metric("Rainy days / yr (≥2.5 mm)", f"{s['RainDays']:.0f}")

    # difference strip
    diff_txt = " · ".join(f"{('Rain' if k=='Rain' else k)} {sb[k]-sd[k]:+.1f}" for k in VARIABLES.values())
    plain_box(f"<b>Block − District:</b> {diff_txt}. Positive = the block is higher than the district figure.")

# ───────── how well does the district represent this block? ─────────
st.markdown(f"### 📊 How well does the {district} number describe {block}?")
rows = []
for k in VARIABLES.values():
    m = continuous_metrics(b[f"{k}_blk"], b[f"{k}_dst"], k)
    rows.append({"Variable": k, "Unit": UNITS[k], "RMSE": m["RMSE"], "MAE": m["MAE"],
                 "Bias (block − district)": m["Bias"], "Correlation r": m["Corr"],
                 "Within tolerance %": m["Within"]})
mt = pd.DataFrame(rows)
st.dataframe(mt.style.format({c: "{:.2f}" for c in mt.columns if c not in ("Variable", "Unit")})
             .background_gradient(subset=["Correlation r", "Within tolerance %"], cmap="Greens"),
             hide_index=True, use_container_width=True)

rs = rain_scores(b["Rain_blk"], b["Rain_dst"])
r1, r2, r3, r4, r5 = st.columns(5)
r1.metric("Rain ratio score", f"{rs['Ratio']:.1f} %")
r2.metric("Rain HK score", "n/a" if np.isnan(rs["HK"]) else f"{rs['HK']:.2f}")
r3.metric("PoD (rain caught)", "n/a" if np.isnan(rs["PoD"]) else f"{rs['PoD']:.2f}")
r4.metric("POFD (false alarms)", "n/a" if np.isnan(rs["POFD"]) else f"{rs['POFD']:.2f}")
r5.metric("Miss rate", "n/a" if np.isnan(rs["Miss"]) else f"{rs['Miss']:.2f}")

# ───────── charts ─────────
t1, t2, t3 = st.tabs(["📈 Over time", "🎯 Scatter (block vs district)", "🍂 By season"])
with t1:
    mode = st.radio("Time step", ["Monthly", "Daily"], horizontal=True)
    s = b[["Date", f"{key}_blk", f"{key}_dst"]].set_index("Date")
    if mode == "Monthly":
        s = s.resample("MS").sum() if key == "Rain" else s.resample("MS").mean()
    s = s.reset_index().melt("Date", var_name="Source", value_name=var_label)
    s["Source"] = s["Source"].map({f"{key}_blk": f"{block} (block)", f"{key}_dst": f"{district} (district)"})
    fig = px.line(s, x="Date", y=var_label, color="Source",
                  color_discrete_map={f"{block} (block)": BLOCK_COLOR, f"{district} (district)": DISTRICT_COLOR})
    fig.update_layout(height=380, legend=dict(orientation="h", y=1.1), margin=dict(t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)
with t2:
    sc = b[[f"{key}_blk", f"{key}_dst"]].dropna()
    fig = px.scatter(sc, x=f"{key}_dst", y=f"{key}_blk", opacity=0.45, color_discrete_sequence=[BLOCK_COLOR],
                     labels={f"{key}_dst": f"District ({unit})", f"{key}_blk": f"Block ({unit})"})
    lo, hi = float(sc.min().min()), float(sc.max().max())
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", name="Perfect agreement",
                             line=dict(color="#64748b", dash="dash")))
    fig.update_layout(height=400, margin=dict(t=20))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Points on the dashed line = block and district agree exactly.")
with t3:
    srows = []
    for ssn, sub in df[(df["District"] == district) & (df["Block"] == block)].groupby("Season"):
        m = continuous_metrics(sub[f"{key}_blk"], sub[f"{key}_dst"], key)
        srows.append({"Season": ssn, "RMSE": m["RMSE"], "Bias": m["Bias"], "Correlation": m["Corr"]})
    sdf = pd.DataFrame(srows)
    sdf["Season"] = pd.Categorical(sdf["Season"], SEASON_ORDER, ordered=True)
    sdf = sdf.sort_values("Season")
    cc = st.columns(3)
    for col, m in zip(cc, ["RMSE", "Bias", "Correlation"]):
        f = px.bar(sdf, x="Season", y=m, title=m, color_discrete_sequence=[BLOCK_COLOR])
        f.update_layout(height=300, margin=dict(t=40, b=10))
        col.plotly_chart(f, use_container_width=True)
