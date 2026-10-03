"""Which blocks are consistently hotter / colder / wetter / windier?"""
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import LABELS, UNITS, YEARS, SEASON_ORDER, load_geojson
from utils.style import inject_css, hero, plain_box, need_data, DIST_COLOR

st.set_page_config(page_title="Spatial Hotspots", page_icon="🔥", layout="wide")
inject_css()
df = need_data()
gj = load_geojson()
hero("🔥", "Spatial Hotspots",
     "Find the blocks that are quietly always a bit hotter, colder, wetter or windier than the rest.")

c1, c2, c3, c4 = st.columns([1.6, 1.2, 1.2, 1.8])
label = c1.selectbox("Variable", list(LABELS))
years = c2.multiselect("Year(s)", YEARS, default=YEARS)
season = c3.selectbox("Season", ["All year"] + SEASON_ORDER)
ref = c4.radio("Compare each block with…", ["Other blocks in its district", "The district's own number"])
key, unit = LABELS[label], UNITS[LABELS[label]]

d = df[df["Year"].isin(years or YEARS)]
if season != "All year":
    d = d[d["Season"] == season]
ny = max(d["Year"].nunique(), 1)
if key == "Rain":
    g = d.groupby(["District", "Block"]).agg(b=(f"{key}_blk", "sum"), p=(f"{key}_dst", "sum")).reset_index()
    g[["b", "p"]] = g[["b", "p"]] / ny
else:
    g = d.groupby(["District", "Block"]).agg(b=(f"{key}_blk", "mean"), p=(f"{key}_dst", "mean")).reset_index()
if ref.startswith("Other"):
    g["anomaly"] = g["b"] - g.groupby("District")["b"].transform("mean")
else:
    g["anomaly"] = g["b"] - g["p"]
g = g.sort_values("anomaly", ascending=False)
lim = float(g["anomaly"].abs().max()) or 1.0

left, right = st.columns([1.2, 1])
with left:
    m = g.copy()
    gj_f = {"type": "FeatureCollection", "features": gj["features"]}
    mm = m[m["Block"].isin([f["id"] for f in gj["features"]])]
    fig = px.choropleth_map(mm, geojson=gj_f, locations="Block", color="anomaly", map_style="carto-positron",
                            center={"lat": 22.8, "lon": 73.1}, zoom=7.1, opacity=0.7,
                            color_continuous_scale="RdBu_r" if key not in ("Rain", "RH-I", "RH-II") else "BrBG",
                            range_color=[-lim, lim], labels={"anomaly": unit},
                            hover_data={"District": True, "b": ":.2f"})
    fig.update_traces(marker_line_width=1, marker_line_color="#334155")
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Red/brown = higher than reference, blue/teal = lower. Galteshwar and Vaso have no boundary polygon "
               "but appear in the ranking.")
with right:
    fig = px.bar(g, x="anomaly", y="Block", orientation="h", color="District", color_discrete_map=DIST_COLOR,
                 labels={"anomaly": f"Difference ({unit})"})
    fig.update_layout(height=560, yaxis=dict(categoryorder="total ascending"), margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

hi, lo = g.iloc[0], g.iloc[-1]
plain_box(f"<b>Highest:</b> {hi.Block} ({hi.District}) at {hi.anomaly:+.2f} {unit} &nbsp;|&nbsp; "
          f"<b>Lowest:</b> {lo.Block} ({lo.District}) at {lo.anomaly:+.2f} {unit} "
          f"({'vs other blocks in the same district' if ref.startswith('Other') else 'vs the district value'}).")
with st.expander("Table"):
    st.dataframe(g.rename(columns={"b": f"Block value ({unit})", "p": f"District value ({unit})",
                                   "anomaly": f"Difference ({unit})"}).round(2), hide_index=True, use_container_width=True)
