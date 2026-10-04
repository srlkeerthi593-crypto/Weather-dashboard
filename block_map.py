"""Block Map page: pick a district, click a block, compare block vs district.
Uses the same CSS classes (hero / kpi / take / info) already defined in app.py."""
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "block_data.json"
TEAL, AMBER, CORAL, INDIGO, SKY, NAVY, GREEN = "#0E9F9A", "#F59E0B", "#EF4444", "#6366F1", "#38BDF8", "#0B2545", "#22C55E"
UNITS = {"Rainfall": "mm", "Max Temperature": "°C", "Min Temperature": "°C",
         "Humidity (RH-I)": "%", "Humidity (RH-II)": "%", "Wind Speed": "km/h"}
# approximate block centres (lat, lon order handled below as lon, lat)
XY = {"Anand|Anand":(72.95,22.56),"Anand|Anklav":(72.99,22.38),"Anand|Borsad":(72.90,22.41),"Anand|Khambhat":(72.62,22.31),"Anand|Petlad":(72.80,22.48),"Anand|Sojitra":(72.78,22.55),"Anand|Tarapur":(72.67,22.40),"Anand|Umreth":(73.10,22.70),
      "Kheda|Galteshwar":(73.13,22.93),"Kheda|Kapadvanj":(73.07,23.02),"Kheda|Kathlal":(72.95,22.87),"Kheda|Kheda":(72.68,22.75),"Kheda|Mahudha":(72.92,22.82),"Kheda|Matar":(72.64,22.69),"Kheda|Mehmedabad":(72.76,22.82),"Kheda|Nadiad":(72.86,22.69),"Kheda|Thasra":(73.20,22.83),"Kheda|Vaso":(72.78,22.72),
      "Mahisagar|Balasinor":(73.34,22.95),"Mahisagar|Kadana":(73.78,23.30),"Mahisagar|Khanpur":(73.50,23.35),"Mahisagar|Lunawada":(73.61,23.13),"Mahisagar|Santrampur":(73.84,23.17),"Mahisagar|Virpur":(73.55,22.91)}


@st.cache_data
def _load():
    return json.load(open(DATA, encoding="utf-8"))


def _kpi(col, label, value, sub, color):
    col.markdown(f'<div class="kpi" style="--c:{color}"><div class="lab">{label}</div>'
                 f'<div class="val">{value}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)


def render_block_map():
    st.markdown('<div class="hero"><h1>🗺️ Block Map — Block vs District</h1>'
                '<p>Choose a district, then click a block on the map to compare it with the district.</p></div>',
                unsafe_allow_html=True)
    if not DATA.exists():
        st.error(f"block_data.json not found at {DATA}. Upload it next to app.py.")
        return
    D = _load()

    c1, c2, c3, c4 = st.columns(4)
    dist = c1.selectbox("District", ["Anand", "Kheda", "Mahisagar"])
    param = c2.selectbox("Parameter", list(UNITS))
    year = c3.selectbox("Year", ["All years", "2021", "2022", "2023"])
    season = c4.selectbox("Season", ["Annual", "Winter", "Summer", "Monsoon", "Post-monsoon"])
    u = UNITS[param]

    R = D[f"{param}|{year}|{season}"]
    dm = R["districts"][dist]            # [observed, forecast, bias, rmse, corr]
    df = pd.DataFrame([{"Block": k.split("|")[1], "lon": XY[k][0], "lat": XY[k][1],
                        "Observed": a[0], "Forecast": a[1], "Bias": a[2], "RMSE": a[3], "Corr": a[4]}
                       for k, a in R["blocks"].items() if k.startswith(dist + "|")]).reset_index(drop=True)

    left, right = st.columns([3, 2])
    with left:
        show = st.segmented_control("Colour blocks by", ["Observed value", "Error (RMSE)", "Bias"],
                                    default="Error (RMSE)") or "Error (RMSE)"
        col = {"Observed value": "Observed", "Error (RMSE)": "RMSE", "Bias": "Bias"}[show]
        fn = getattr(px, "scatter_map", None)
        style = dict(map_style="carto-positron") if fn else dict(mapbox_style="carto-positron")
        fn = fn or px.scatter_mapbox
        fig = fn(df, lat="lat", lon="lon", color=col, text="Block", hover_name="Block",
                 hover_data={"lat": False, "lon": False, "Observed": True, "Forecast": True, "Bias": True, "RMSE": True},
                 color_continuous_scale="RdBu_r" if col == "Bias" else "YlOrRd", zoom=9.3, height=480,
                 center=dict(lat=df.lat.mean(), lon=df.lon.mean()), **style)
        fig.update_traces(marker=dict(size=28), textposition="top center", textfont=dict(color=NAVY, size=12))
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)",
                          coloraxis_colorbar=dict(title=f"{col}<br>({u})"))
        st.caption("👆 Click a block circle to compare it with the district")
        picked = None
        try:
            ev = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points",
                                 key=f"bm_{dist}_{param}_{year}_{season}_{col}")
            if ev and ev.selection.points:
                picked = df.Block[ev.selection.points[0]["point_index"]]
        except (TypeError, AttributeError, KeyError, IndexError):
            st.plotly_chart(fig, width="stretch")
    names = list(df.Block)
    with right:
        blk = st.selectbox("Selected block (or choose here)", names,
                           index=names.index(picked) if picked in names else 0,
                           key=f"bsel_{dist}_{param}_{year}_{season}_{picked}")
        r = df[df.Block == blk].iloc[0]
        k = st.columns(2)
        _kpi(k[0], "Observed (block)", f"{r.Observed} {u}", f"district avg {dm[0]} {u}", TEAL)
        _kpi(k[1], "Forecast (district)", f"{r.Forecast} {u}", "same forecast for the whole district", INDIGO)
        st.write("")
        k = st.columns(2)
        _kpi(k[0], "Block error (RMSE)", f"{r.RMSE} {u}", f"district RMSE {dm[3]} {u}", AMBER)
        _kpi(k[1], "Block bias", f"{r.Bias:+.2f} {u}", f"district bias {dm[2]:+.2f} {u}", CORAL)

    better = r.RMSE < dm[3]
    st.markdown(f'<div class="take">💡 <b>{blk}</b> observed <b>{r.Observed} {u}</b> vs district average <b>{dm[0]} {u}</b> '
                f'({r.Observed - dm[0]:+.2f}). Its forecast error is <b>{r.RMSE} {u}</b> against <b>{dm[3]} {u}</b> for {dist} — '
                f'<b>{"better" if better else "worse"}</b> than the district average.</div>', unsafe_allow_html=True)

    a, b, c = st.columns(3)
    with a, st.container(border=True):
        f1 = go.Figure(go.Bar(x=[f"{blk} observed", f"{dist} observed (avg)", f"{dist} forecast"],
                              y=[r.Observed, dm[0], dm[1]], marker_color=[AMBER, TEAL, INDIGO],
                              text=[r.Observed, dm[0], dm[1]], textposition="outside"))
        f1.update_layout(title=dict(text="Block vs district value", x=0.5), height=360, yaxis_title=u,
                         margin=dict(t=60, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(f1, width="stretch")
    with b, st.container(border=True):
        s = df.sort_values("RMSE")
        f2 = go.Figure(go.Bar(x=s.Block, y=s.RMSE, marker_color=[AMBER if x == blk else TEAL for x in s.Block]))
        f2.add_hline(y=dm[3], line_dash="dash", line_color=CORAL, annotation_text=f"{dist} RMSE {dm[3]}")
        f2.update_layout(title=dict(text="Forecast error by block", x=0.5), height=360, yaxis_title=f"RMSE ({u})",
                         margin=dict(t=60, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(f2, width="stretch")
    with c, st.container(border=True):
        inv = 1 / (df.RMSE + 1e-6)
        f3 = go.Figure(go.Pie(labels=df.Block, values=inv, hole=0.5, sort=False,
                              pull=[0.14 if x == blk else 0 for x in df.Block],
                              marker=dict(line=dict(color="white", width=2)), textinfo="percent"))
        f3.update_layout(title=dict(text=f"Reliability share in {dist}", x=0.5), height=360,
                         margin=dict(t=60, b=10), paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(f3, width="stretch")
        st.caption("Bigger slice = lower error (more reliable block).")

    st.markdown('<div class="info"><b>Observed</b> = block-wise data · <b>Forecast</b> = district-wise data · '
                '<b>Bias</b> = Observed − Forecast · Map positions are approximate block centres.</div>', unsafe_allow_html=True)
    with st.expander("📋 All blocks in this district"):
        t = df[["Block", "Observed", "Forecast", "Bias", "RMSE", "Corr"]].copy()
        t.loc[len(t)] = [f"{dist} (district)", dm[0], dm[1], dm[2], dm[3], dm[4]]
        st.dataframe(t, hide_index=True, width="stretch")
