"""
Block vs District Weather Forecast Dashboard
Anand · Kheda · Mahisagar (Gujarat)  |  2021-2023

Data   : data/daily_merged.csv.gz  (built from your three Excel files by prepare_data.py)
Borders: data/blocks.geojson
Charts : assets/results/...        (comparison charts from results_final.zip)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import inspect


def wk(fn):
    """full-width keyword that works on both old and new Streamlit versions"""
    try:
        return {"width": "stretch"} if "width" in inspect.signature(fn).parameters else {"use_container_width": True}
    except Exception:
        return {"use_container_width": True}


st.set_page_config(page_title="Block vs District Weather", page_icon="🌦️", layout="wide")

BASE = Path(__file__).parent
BLOCK_CLR, DIST_CLR = "#2563EB", "#F97316"          # blue = block, orange = district (used everywhere)
DISTRICT_CLR = {"Anand": "#6D28D9", "Kheda": "#0F766E", "Mahisagar": "#BE185D"}
INK, MUTED, GRID = "#0F172A", "#64748B", "#E2E8F0"

# key -> label, unit, results-folder, sequential colour scale, is-rain
VARS = {
    "rain": ("Rainfall", "mm", "Rainfall", "Blues", True),
    "tmax": ("Max temperature", "°C", "Tmax", "Oranges", False),
    "tmin": ("Min temperature", "°C", "Tmin", "Oranges", False),
    "rhi": ("Humidity – morning (RH-I)", "%", "RH-I", "Tealgrn", False),
    "rhii": ("Humidity – afternoon (RH-II)", "%", "RH-II", "Tealgrn", False),
    "wind": ("Wind speed", "km/h", "WindSpeed", "Purples", False),
}
SEASONS = ["Winter", "Summer", "Monsoon", "Post-monsoon"]
SEASON_MONTHS = "Winter = Dec–Feb · Summer = Mar–May · Monsoon = Jun–Sep · Post-monsoon = Oct–Nov"

# ───────────────────────────── styling ─────────────────────────────
st.markdown(
    """
<style>
.stApp{background:linear-gradient(180deg,#F5F3FF 0%,#EFF6FF 45%,#F0FDFA 100%)}
.block-container{padding-top:1.4rem;max-width:1500px}
.stTabs [data-baseweb="tab-list"]{gap:8px}
.stTabs [data-baseweb="tab"]{background:#fff;border-radius:12px;padding:8px 18px;border:1px solid #E2E8F0;font-weight:700}
.stTabs [aria-selected="true"]{background:linear-gradient(110deg,#6D28D9,#2563EB);color:#fff!important}
.stTabs [aria-selected="true"] p{color:#fff!important}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none}
.say{background:#fff;border-left:5px solid #6D28D9;border-radius:8px;padding:8px 14px;margin:4px 0 10px 0;
     color:#334155;font-size:.95rem;box-shadow:0 1px 3px rgba(15,23,42,.06)}
.hot{border-radius:14px;padding:12px 16px;color:#fff;margin-bottom:8px}
.hot b{font-size:1.05rem}
.banner{background:linear-gradient(110deg,#6D28D9 0%,#2563EB 55%,#06B6D4 100%);color:#fff;
        border-radius:18px;padding:26px 34px;margin-bottom:14px}
.banner h1{color:#fff;margin:0;font-size:2.0rem;padding:0}
.banner p{margin:6px 0 0 0;font-size:1.05rem;opacity:.95}
.step{background:#EEF2FF;border-radius:10px;padding:10px 16px;margin:18px 0 8px 0;
      font-weight:700;color:#1E1B4B;font-size:1.05rem}
.step span{background:#4F46E5;color:#fff;border-radius:6px;padding:1px 8px;margin-right:8px;font-size:.9rem}
.card{border-radius:14px;padding:14px 18px;border:1px solid #E2E8F0;background:#fff;height:100%;box-shadow:0 1px 3px rgba(15,23,42,.06)}
.card .tag{font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
.card .nm{font-size:1.35rem;font-weight:800;margin:2px 0 8px 0;color:#0F172A}
.card .row{display:flex;justify-content:space-between;padding:4px 0;border-top:1px solid #F1F5F9;font-size:.93rem}
.card .row b{color:#0F172A}.card .row span{color:#64748B}
.kpi{border-radius:14px;padding:12px 16px;background:#fff;border:1px solid #E2E8F0;border-top:5px solid #6D28D9;text-align:center;box-shadow:0 1px 3px rgba(15,23,42,.06)}
.kpi .v{font-size:1.6rem;font-weight:800;color:#0F172A}.kpi .l{font-size:.8rem;color:#64748B}
.note{background:#FFFBEB;border-left:4px solid #F59E0B;padding:9px 14px;border-radius:6px;
      font-size:.9rem;color:#78350F;margin:6px 0}
.good{background:#ECFDF5;border-left:4px solid #10B981;padding:9px 14px;border-radius:6px;
      font-size:.95rem;color:#064E3B;margin:6px 0}
</style>
""",
    unsafe_allow_html=True,
)


def say(text):
    """one plain-language sentence under a heading (handy when presenting)"""
    st.markdown(f'<div class="say">💬 {text}</div>', unsafe_allow_html=True)


# how far apart (block vs district) still counts as "agreeing": (close, moderate) per variable
TOL = {"rain": (1, 5), "tmax": (1, 2), "tmin": (1, 2), "rhi": (5, 10), "rhii": (5, 10), "wind": (2, 5)}


def donut(labels, values, colors, title, centre=None):
    f = go.Figure(go.Pie(labels=labels, values=values, hole=0.58, sort=False, direction="clockwise",
                         marker=dict(colors=colors, line=dict(color="white", width=3)),
                         textinfo="percent", textfont=dict(size=14, color="white"),
                         hovertemplate="%{label}<br>%{value:,} days (%{percent})<extra></extra>"))
    f.update_layout(title=title, height=360, margin=dict(l=10, r=10, t=50, b=60), paper_bgcolor="white",
                    font=dict(color=INK, size=13), legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"))
    if centre:
        f.add_annotation(text=centre, x=0.5, y=0.5, showarrow=False, font=dict(size=20, color=INK))
    return f


def step(n, text):
    st.markdown(f'<div class="step"><span>{n}</span>{text}</div>', unsafe_allow_html=True)


# ───────────────────────────── data ─────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "data" / "daily_merged.csv.gz", parse_dates=["Date"])
    m = df["Date"].dt.month
    df["Season"] = np.select(
        [m.isin([12, 1, 2]), m.isin([3, 4, 5]), m.isin([6, 7, 8, 9])], ["Winter", "Summer", "Monsoon"], "Post-monsoon"
    )
    df["Month"] = df["Date"].dt.month
    return df


@st.cache_data
def load_geo():
    return json.load(open(BASE / "data" / "blocks.geojson", encoding="utf-8"))


@st.cache_data
def get_subset(year, season, real_only):
    d = load_data()
    if year != "All":
        d = d[d["Year"] == year]
    if season != "All":
        d = d[d["Season"] == season]
    if real_only:
        d = d[d["real"]]
    return d.reset_index(drop=True)


for _f in ["data/daily_merged.csv.gz", "data/blocks.geojson"]:
    if not (BASE / _f).exists():
        st.error(f"Missing file: {_f}. Upload it to the same folder as app.py (keep the folder name 'data').")
        st.stop()
DF = load_data()
GEO = load_geo()
DISTRICTS = sorted(DF["District"].unique())
BLOCKS_OF = {d: sorted(DF.loc[DF["District"] == d, "Block"].unique()) for d in DISTRICTS}
BLOCK_DISTRICT = {b: d for d, bl in BLOCKS_OF.items() for b in bl}
MAPPED = {f["properties"]["Block"] for f in GEO["features"]}


def geo_for(districts):
    return {"type": "FeatureCollection",
            "features": [f for f in GEO["features"] if f["properties"]["District"] in districts]}


# ───────────────────────────── maths ─────────────────────────────
def agree(b, d):
    """Agreement of the district series (d) with the block series (b). Bias = Block − District (as in your verification)."""
    b, d = np.asarray(b, float), np.asarray(d, float)
    if len(b) < 3:
        return dict(corr=np.nan, rmse=np.nan, mae=np.nan, bias=np.nan, n=len(b))
    diff = b - d
    corr = np.corrcoef(b, d)[0, 1] if b.std() > 0 and d.std() > 0 else np.nan
    return dict(corr=corr, rmse=float(np.sqrt(np.mean(diff**2))), mae=float(np.mean(np.abs(diff))),
                bias=float(diff.mean()), n=len(b))


def rating(c):
    if pd.isna(c):
        return "n/a"
    return "Very close" if c >= 0.9 else "Close" if c >= 0.75 else "Moderate" if c >= 0.5 else "Weak"


def skill(b, d, thr):
    """Rain / no-rain scores exactly as in the verification notebook (block = reference)."""
    ob, fc = np.asarray(b) >= thr, np.asarray(d) >= thr
    NN, NY, YN, YY = (~ob & ~fc).sum(), (~ob & fc).sum(), (ob & ~fc).sum(), (ob & fc).sum()
    div = lambda a, c: a / c if c else np.nan
    return dict(
        N=int(len(ob)), **{"Ratio score (%)": 100 * (YY + NN) / max(len(ob), 1)},
        PoD=div(YY, YY + YN), POFD=div(NY, NY + NN), FAR=div(NY, YY + NY), CSI=div(YY, YY + NY + YN),
        HK=div(YY * NN - NY * YN, (YY + YN) * (NN + NY)),
    )


def fmt(x, nd=2):
    return "–" if x is None or pd.isna(x) else f"{x:,.{nd}f}"


# ───────────────────────────── plotly helpers ─────────────────────────────
def style(fig, h=380, legend=True):
    fig.update_layout(
        height=h, margin=dict(l=10, r=10, t=45, b=40), plot_bgcolor="white", paper_bgcolor="white",
        font=dict(color=INK, size=13), hovermode="closest", showlegend=legend,
        legend=dict(orientation="h", y=-0.15, yanchor="top", x=0),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def view_for(feats, height, width=650):
    """Centre + zoom that fits the given polygons (so no external map files are needed)."""
    pts = []
    def walk(c):
        if isinstance(c[0], (int, float)):
            pts.append(c)
        else:
            for x in c:
                walk(x)
    for f in feats:
        walk(f["geometry"]["coordinates"])
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    lon0, lon1, lat0, lat1 = min(xs), max(xs), min(ys), max(ys)
    clat = (lat0 + lat1) / 2
    zx = np.log2(360 * width / (256 * max(lon1 - lon0, 1e-6)))
    zy = np.log2(360 * (height - 60) / (256 * max((lat1 - lat0) / np.cos(np.radians(clat)), 1e-6)))
    return dict(lon=(lon0 + lon1) / 2, lat=clat), float(min(zx, zy) - 1.1)


def choropleth(blocks_df, geo, colorscale, title, unit, zmid=None, selected=None, key_height=520, label_fmt="{:.1f}"):
    """blocks_df: columns Block, z.  Draws boundaries, value colours, names, and a thick outline on `selected`."""
    feats = {f["properties"]["Block"]: f["properties"] for f in geo["features"]}
    # soften the dark ends of the scale so the block names stay readable on top of the colours
    lo, hi = (0.15, 0.85) if zmid is not None else (0.08, 0.70)
    colorscale = [[float(t), c] for t, c in zip(np.linspace(0, 1, 9),
                  px.colors.sample_colorscale(colorscale, list(np.linspace(lo, hi, 9))))]
    d = blocks_df[blocks_df["Block"].isin(feats)].copy()
    fig = go.Figure(go.Choroplethmap(
        geojson=geo, featureidkey="properties.Block", locations=d["Block"], z=d["z"],
        colorscale=colorscale, zmid=zmid, marker_line_color="#334155", marker_line_width=1.4, marker_opacity=0.9,
        selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)),
        customdata=np.stack([d["Block"].map(lambda b: feats[b]["District"])], axis=-1),
        hovertemplate="<b>%{location}</b> (%{customdata[0]})<br>%{z:.2f} " + unit + "<extra></extra>",
        colorbar=dict(orientation="h", y=-0.02, yanchor="top", len=0.75, thickness=12,
                      title=dict(text=title, side="top", font=dict(size=12)), tickfont=dict(size=11)),
    ))
    if selected in feats and selected in set(d["Block"]):
        fig.add_trace(go.Choroplethmap(
            geojson=geo, featureidkey="properties.Block", locations=[selected], z=[0], showscale=False,
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], marker_line_color="#0F172A",
            marker_line_width=4, hoverinfo="skip"))
    fig.add_trace(go.Scattermap(
        lon=[feats[b]["lon"] for b in d["Block"]], lat=[feats[b]["lat"] for b in d["Block"]],
        text=list(d["Block"]),
        mode="text", textfont=dict(size=12, color="#0F172A"), hoverinfo="skip", showlegend=False))
    cen, zoom = view_for([f for f in geo["features"] if f["properties"]["Block"] in set(d["Block"])], key_height)
    fig.update_layout(map=dict(style="white-bg", center=cen, zoom=zoom), height=key_height, margin=dict(l=0, r=0, t=10, b=60), paper_bgcolor="white", dragmode=False,
                      clickmode="event+select")
    return fig


# ───────────────────────────── header + global filters ─────────────────────────────
st.markdown(
    '<div class="banner"><h1>🌦️ Block vs District Weather Forecast</h1>'
    "<p>Anand · Kheda · Mahisagar — how closely does the district-level forecast match the block-level forecast?</p></div>",
    unsafe_allow_html=True,
)

district = st.selectbox("District", DISTRICTS)
f1, f2 = st.columns([1.6, 1.1])
var = f1.selectbox("Weather variable", list(VARS), format_func=lambda k: f"{VARS[k][0]} ({VARS[k][1]})")
season = f2.selectbox("Season", ["All"] + SEASONS, help=SEASON_MONTHS)
with st.expander("More filters (optional)"):
    year = st.selectbox("Year", ["All", 2021, 2022, 2023])
    real_only = st.checkbox(
        "Use only genuine forecast days (skip days that were gap-filled/interpolated in the Excel files)", value=False,
        help="Default OFF so the numbers match your verification results. Switch ON for a stricter check.")

label, unit, folder, scale, is_rain = VARS[var]
SUB = get_subset(year, season, real_only)
B, D = f"{var}_block", f"{var}_dist"
if SUB.empty:
    st.warning("No data for this combination of filters.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(
    ["🗺️ Block vs District", "⚖️ Which is Reliable?", "🔥 Spatial Hotspots", "📊 Result Charts"])

# ═════════════════════════════ TAB 1 : block vs district ═════════════════════════════
with tab1:
    blocks = BLOCKS_OF[district]
    if st.session_state.get("sel_block") not in blocks:
        st.session_state["sel_block"] = blocks[0]

    def on_map_click():
        ev = st.session_state.get(st.session_state.get("_map_key", ""), None)
        try:
            pts = ev.selection.points if ev else []
        except Exception:
            pts = []
        for p in pts:
            loc = p.get("location")
            if loc in BLOCKS_OF.get(st.session_state.get("_map_district"), []):
                st.session_state["sel_block"] = loc
                break

    sd = SUB[SUB["District"] == district]
    dd = sd.drop_duplicates("Date")                      # one district-level row per day

    step(1, f"{district} at a glance")
    say(f"Each block has its own forecast; the district gives one number for all of them. "
        f"Here is how closely the two agree for {label.lower()} in {district}.")
    per_block = [agree(x[B], x[D]) for _, x in sd.groupby("Block")]
    g_corr = np.nanmean([m["corr"] for m in per_block])
    g_rmse, g_bias = np.mean([m["rmse"] for m in per_block]), np.mean([m["bias"] for m in per_block])
    q1, q2, q3, q4 = st.columns(4)
    q1.markdown(f'<div class="kpi"><div class="v">{len(BLOCKS_OF[district])}</div><div class="l">Blocks in {district}<br>'
                '<b>compared with 1 district forecast</b></div></div>', unsafe_allow_html=True)
    q2.markdown(f'<div class="kpi"><div class="v">{fmt(g_corr)}</div><div class="l">Average correlation<br>'
                f'<b>{rating(g_corr)}</b></div></div>', unsafe_allow_html=True)
    q3.markdown(f'<div class="kpi"><div class="v">{fmt(g_rmse)}</div><div class="l">Typical gap, RMSE ({unit})<br>'
                '<b>lower = closer</b></div></div>', unsafe_allow_html=True)
    q4.markdown(f'<div class="kpi"><div class="v">{g_bias:+.2f}</div><div class="l">Average bias ({unit})<br>'
                '<b>Block − District</b></div></div>', unsafe_allow_html=True)

    step(2, f"Click a block on the {district} map")
    say("Colour the map by the block average, or by how far each block is from the district (Block − District). Click any block to compare it with the district.")
    left, right = st.columns([1.05, 1], gap="large")

    with left:
        mode = st.segmented_control("Colour the map by", ["Block average", "Block − District"],
                                    default="Block average", key="map_mode") or "Block average"
        g = sd.groupby("Block").apply(lambda x: pd.Series(
            {"avg": x[B].mean(), "diff": (x[B] - x[D]).mean()}), include_groups=False).reset_index()
        bdf = g.rename(columns={"avg" if mode == "Block average" else "diff": "z"})[["Block", "z"]]
        fig = choropleth(bdf, geo_for([district]), scale if mode == "Block average" else "RdBu_r",
                         f"Block average {label} ({unit})" if mode == "Block average"
                         else f"Block − District ({unit}): red = block higher, blue = block lower", unit,
                         zmid=None if mode == "Block average" else 0, selected=st.session_state["sel_block"])
        mkey = f"map_{district}_{st.session_state['sel_block']}_{mode}"
        st.session_state["_map_key"], st.session_state["_map_district"] = mkey, district
        st.plotly_chart(fig, key=mkey, on_select=on_map_click, selection_mode="points", **wk(st.plotly_chart),
                        config={"displayModeBar": False})
        missing = [b for b in blocks if b not in MAPPED]
        if missing:
            st.markdown(f'<div class="note">📍 <b>{", ".join(missing)}</b> {"is a" if len(missing)==1 else "are"} '
                        "newer block(s) that are not in the 2011 boundary file, so no outline can be drawn. "
                        "Pick them from the list on the right — all numbers still work.</div>", unsafe_allow_html=True)

    with right:
        sel = st.selectbox("Selected block (or click it on the map)", blocks, key="sel_block")
        sb = sd[sd["Block"] == sel].sort_values("Date")
        db = dd.sort_values("Date")
        m_ = agree(sb[B], sb[D])

        def stats(s):
            if is_rain:
                return [("Average per day", f"{s.mean():.2f} mm"), ("Total rain", f"{s.sum():,.0f} mm"),
                        ("Rainy days (≥ 2.5 mm)", f"{int((s >= 2.5).sum())}"), ("Heaviest day", f"{s.max():.1f} mm")]
            return [("Average", f"{s.mean():.1f} {unit}"), ("Highest", f"{s.max():.1f} {unit}"),
                    ("Lowest", f"{s.min():.1f} {unit}"), ("Day-to-day variation (SD)", f"{s.std():.2f} {unit}")]

        def card(tag, name, color, rows):
            body = "".join(f'<div class="row"><span>{a}</span><b>{b}</b></div>' for a, b in rows)
            return (f'<div class="card" style="border-top:5px solid {color}"><div class="tag" style="color:{color}">'
                    f'{tag}</div><div class="nm">{name}</div>{body}</div>')

        k1, k2 = st.columns(2)
        k1.markdown(card("Block-level forecast", sel, BLOCK_CLR, stats(sb[B])), unsafe_allow_html=True)
        k2.markdown(card("District-level forecast", district, DIST_CLR, stats(db[D])), unsafe_allow_html=True)

        st.write("")
        a, b_, c_ = st.columns(3)
        a.markdown(f'<div class="kpi"><div class="v">{fmt(m_["corr"])}</div><div class="l">Correlation<br>'
                   f'<b>{rating(m_["corr"])}</b></div></div>', unsafe_allow_html=True)
        b_.markdown(f'<div class="kpi"><div class="v">{fmt(m_["rmse"])}</div><div class="l">RMSE ({unit})<br>'
                    '<b>typical gap</b></div></div>', unsafe_allow_html=True)
        c_.markdown(f'<div class="kpi"><div class="v">{m_["bias"]:+.2f}</div><div class="l">Bias ({unit})<br>'
                    '<b>Block − District</b></div></div>', unsafe_allow_html=True)
        if pd.notna(m_["bias"]):
            word = "lower" if m_["bias"] > 0 else "higher"
            st.caption(f"On average the district forecast reads **{abs(m_['bias']):.2f} {unit} {word}** than the "
                       f"{sel} block forecast, and the typical day-to-day gap is about {m_['rmse']:.2f} {unit}.")

    step(3, f"Day-by-day: {sel} block vs {district} district")
    say("Blue is the block forecast, orange is the district forecast. Where the lines split apart, the two disagree.")
    ts = go.Figure()
    ts.add_trace(go.Scatter(x=sb["Date"], y=sb[B], name=f"Block: {sel}", line=dict(color=BLOCK_CLR, width=1.8)))
    ts.add_trace(go.Scatter(x=db["Date"], y=db[D], name=f"District: {district}", line=dict(color=DIST_CLR, width=1.8)))
    ts.update_layout(hovermode="x unified", yaxis_title=f"{label} ({unit})")
    st.plotly_chart(style(ts, 360), **wk(st.plotly_chart), config={"displayModeBar": False})

    step(4, "How well do they agree?")
    say("Left: every dot is one day (on the dashed line = identical). Middle: monthly averages. "
        "Right: share of days the two are close, a little apart, or far apart.")
    cc1, cc2, cc3 = st.columns(3)
    with cc3:
        t1, t2 = TOL[var]
        ad = np.abs(sb[B].values - sb[D].values)
        n1, n2 = int((ad <= t1).sum()), int(((ad > t1) & (ad <= t2)).sum())
        n3 = int((ad > t2).sum())
        pf = donut([f"Within {t1} {unit}", f"{t1}–{t2} {unit} apart", f"More than {t2} {unit} apart"], [n1, n2, n3],
                   ["#10B981", "#F59E0B", "#EF4444"], f"Days of agreement — {sel}", centre=f"{100*n1/max(len(ad),1):.0f}%<br>close")
        st.plotly_chart(pf, **wk(st.plotly_chart), config={"displayModeBar": False})
    with cc1:
        sc = go.Figure()
        sc.add_trace(go.Scatter(x=sb[D], y=sb[B], mode="markers", name="Days",
                                marker=dict(color=BLOCK_CLR, size=6, opacity=0.35), showlegend=False,
                                hovertemplate=f"District %{{x}} · Block %{{y}} {unit}<extra></extra>"))
        lo, hi = float(min(sb[D].min(), sb[B].min())), float(max(sb[D].max(), sb[B].max()))
        sc.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", name="Perfect match",
                                line=dict(color="#94A3B8", dash="dash"), hoverinfo="skip"))
        sc.update_layout(title="Day by day: district vs block",
                         xaxis_title=f"District forecast ({unit})", yaxis_title=f"Block forecast ({unit})")
        st.plotly_chart(style(sc, 360), **wk(st.plotly_chart), config={"displayModeBar": False})
    with cc2:
        mm = pd.DataFrame({"Month": sb["Month"], "Block": sb[B].values, "District": sb[D].values}).groupby("Month").mean()
        mn = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        bar = go.Figure()
        bar.add_bar(x=[mn[i - 1] for i in mm.index], y=mm["Block"], name="Block", marker_color=BLOCK_CLR)
        bar.add_bar(x=[mn[i - 1] for i in mm.index], y=mm["District"], name="District", marker_color=DIST_CLR)
        bar.update_layout(barmode="group", bargap=0.25, title="Monthly average", yaxis_title=f"{label} ({unit})")
        st.plotly_chart(style(bar, 360), **wk(st.plotly_chart), config={"displayModeBar": False})

    step(5, f"All blocks of {district} compared with the district forecast")
    say("A quick league table: which blocks follow the district forecast most closely.")
    rows = []
    for bl, x in sd.groupby("Block"):
        mt = agree(x[B], x[D])
        rows.append({"Block": bl, "Correlation": mt["corr"], f"RMSE ({unit})": mt["rmse"],
                     f"Bias Block−District ({unit})": mt["bias"], "Agreement": rating(mt["corr"])})
    tbl = pd.DataFrame(rows).sort_values("Correlation", ascending=False)
    st.dataframe(tbl, hide_index=True, **wk(st.dataframe), column_config={
        "Correlation": st.column_config.ProgressColumn("Correlation", min_value=0, max_value=1, format="%.2f"),
        f"RMSE ({unit})": st.column_config.NumberColumn(format="%.2f"),
        f"Bias Block−District ({unit})": st.column_config.NumberColumn(format="%+.2f")})

# ═════════════════════════════ TAB 2 : reliability ═════════════════════════════
with tab2:
    st.markdown(
        '<div class="note"><b>How to read this tab.</b> Following your verification notebook, the <b>block-level</b> '
        "forecast is used as the reference and the <b>district-level</b> forecast is tested against it. "
        "So “reliable” here means <i>how faithfully the district number reproduces what the block forecasts say</i>. "
        "Your files do not contain ground-truth station observations, so this tab cannot say which forecast is closer "
        "to the real weather.</div>", unsafe_allow_html=True)

    step(1, "Scorecard — all weather variables (all 3 districts, selected year/season)")
    say("Correlation near 1 means the district forecast rises and falls together with the block forecasts. "
        "Lower RMSE and bias closer to 0 mean a smaller gap.")
    rows = []
    for k, (lb, un, _, _, _) in VARS.items():
        mt = agree(SUB[f"{k}_block"], SUB[f"{k}_dist"])
        spread = SUB.groupby(["District", "Date"])[f"{k}_block"].std(ddof=0).mean()
        rows.append({"Variable": f"{lb} ({un})", "Correlation": mt["corr"], "RMSE": mt["rmse"], "MAE": mt["mae"],
                     "Bias (Block−District)": mt["bias"], "Block-to-block spread*": spread, "Agreement": rating(mt["corr"])})
    sc_df = pd.DataFrame(rows)
    st.dataframe(sc_df, hide_index=True, **wk(st.dataframe), column_config={
        "Correlation": st.column_config.ProgressColumn("Correlation", min_value=0, max_value=1, format="%.2f"),
        "RMSE": st.column_config.NumberColumn(format="%.2f"), "MAE": st.column_config.NumberColumn(format="%.2f"),
        "Bias (Block−District)": st.column_config.NumberColumn(format="%+.2f"),
        "Block-to-block spread*": st.column_config.NumberColumn(format="%.2f")})
    st.caption("*Block-to-block spread = how much the blocks inside one district differ from each other on an average "
               "day. The district forecast gives one number for the whole district, so it cannot show this local detail.")
    best, worst = sc_df.loc[sc_df["Correlation"].idxmax()], sc_df.loc[sc_df["Correlation"].idxmin()]
    st.markdown(f'<div class="good">✅ District forecast follows the block forecast <b>best for {best["Variable"]}</b> '
                f'(r = {best["Correlation"]:.2f}) and <b>least for {worst["Variable"]}</b> (r = {worst["Correlation"]:.2f}). '
                "Where agreement is lower, the block-level forecast carries extra local information that the district "
                "average smooths out.</div>", unsafe_allow_html=True)

    step(2, "Where does agreement change? Correlation of every block with its district")
    say("Darker blue = stronger agreement. Rainfall is the hardest to match; temperature and humidity agree well.")
    hm = SUB.groupby("Block").apply(lambda x: pd.Series({VARS[k][0]: agree(x[f"{k}_block"], x[f"{k}_dist"])["corr"]
                                                         for k in VARS}), include_groups=False)
    hm = hm.loc[[b for d in DISTRICTS for b in BLOCKS_OF[d]]]
    hfig = go.Figure(go.Heatmap(
        z=hm.values, x=hm.columns, y=[f"{b} ({BLOCK_DISTRICT[b]})" for b in hm.index],
        colorscale="Blues", zmin=0.5, zmax=1, text=np.round(hm.values, 2), texttemplate="%{text}",
        hovertemplate="%{y}<br>%{x}: r = %{z:.2f}<extra></extra>", colorbar=dict(title="r", thickness=12)))
    hfig.update_yaxes(autorange="reversed", gridcolor="white")
    st.plotly_chart(style(hfig, 640, legend=False), **wk(st.plotly_chart), config={"displayModeBar": False})

    step(3, f"Seasonal error — {label}")
    say("Which season causes most of the error, and in which direction the district reads higher or lower.")
    base = get_subset(year, "All", real_only)
    srows = []
    for s in SEASONS:
        x = base[base["Season"] == s]
        mt = agree(x[B], x[D]) if len(x) else dict(rmse=np.nan, bias=np.nan, corr=np.nan)
        srows.append({"Season": s, "RMSE": mt["rmse"], "Bias": mt["bias"], "Correlation": mt["corr"]})
    sdf = pd.DataFrame(srows)
    e1, e2 = st.columns(2)
    sq = [float(((base[base["Season"] == s_][B] - base[base["Season"] == s_][D]) ** 2).sum()) for s_ in SEASONS]
    f1 = donut(SEASONS, [round(v) for v in sq], ["#3B82F6", "#F59E0B", "#6D28D9", "#14B8A6"],
               "Which season makes most of the error?")
    f1.update_traces(hovertemplate="%{label}: %{percent} of total error<extra></extra>")
    e1.plotly_chart(f1, **wk(st.plotly_chart), config={"displayModeBar": False})
    f2 = go.Figure(go.Bar(x=sdf["Season"], y=sdf["Bias"], marker_color=[DIST_CLR if v < 0 else BLOCK_CLR for v in sdf["Bias"]],
                          hovertemplate="%{x}: %{y:+.2f} " + unit + "<extra></extra>"))
    f2.update_layout(title=f"Bias, Block − District ({unit}) — closer to 0 is better", bargap=0.35)
    f2.add_hline(y=0, line_color="#94A3B8", line_dash="dash")
    e2.plotly_chart(style(f2, 320, legend=False), **wk(st.plotly_chart), config={"displayModeBar": False})
    st.caption("Blue bar: block reads higher than district · Orange bar: block reads lower than district. "
               f"({SEASON_MONTHS})")

    step(4, "Rain / no-rain skill of the district forecast")
    say("A day counts as rainy when at least 2.5 mm falls (the same rule as your verification). "
        "Does the district forecast make the same rain / no-rain call as the blocks?")
    thr = 2.5
    srows = []
    for nm, x in [("All 3 districts", SUB)] + [(d, SUB[SUB["District"] == d]) for d in DISTRICTS]:
        srows.append({"Area": nm, **skill(x["rain_block"], x["rain_dist"], thr)})
    kdf = pd.DataFrame(srows)
    ob_, fc_ = SUB["rain_block"].values >= thr, SUB["rain_dist"].values >= thr
    p1, p2 = st.columns([1, 1.5])
    pie = donut(["Rain on both", "No rain on both", "False alarm (district only)", "Missed (block only)"],
                [int((ob_ & fc_).sum()), int((~ob_ & ~fc_).sum()), int((~ob_ & fc_).sum()), int((ob_ & ~fc_).sum())],
                ["#2563EB", "#10B981", "#F59E0B", "#EF4444"], "Rain call: district vs blocks")
    p1.plotly_chart(pie, **wk(st.plotly_chart), config={"displayModeBar": False})
    p2.dataframe(kdf, hide_index=True, **wk(st.dataframe), column_config={
        "Ratio score (%)": st.column_config.NumberColumn(format="%.1f"),
        **{c: st.column_config.NumberColumn(format="%.2f") for c in ["PoD", "POFD", "FAR", "CSI", "HK"]}})
    st.caption("Ratio score = % of days with the right rain/no-rain call · PoD = share of block-rain days the district "
               "also caught (higher better) · HK = Hanssen-Kuiper skill, 1 is perfect · CSI = threat score (higher better) · "
               "FAR = false-alarm ratio, POFD = false-alarm rate (lower better).")

# ═════════════════════════════ TAB 3 : hotspots ═════════════════════════════
with tab3:
    st.markdown('<div class="banner" style="background:linear-gradient(110deg,#7C3AED,#2563EB 60%,#06B6D4);padding:18px 30px">'
                "<h1 style='font-size:1.6rem'>🔥 Spatial Hotspots</h1>"
                "<p>Which blocks are quietly always a bit higher or lower than the rest?</p></div>", unsafe_allow_html=True)
    step(1, f"Block average of {label} compared with the average of all 24 blocks")
    say("Red blocks are always a bit higher than the rest, blue blocks always a bit lower.")
    bm = SUB.groupby(["District", "Block"])[B].mean().reset_index()
    overall = bm[B].mean()
    bm["z"] = bm[B] - overall
    st.caption(f"Overall average of all blocks: **{overall:.2f} {unit}**. Red = higher than average, blue = lower. "
               "Uses the block-level forecast and the Year / Season filters above.")
    h1, h2 = st.columns([1.1, 1], gap="large")
    with h1:
        hf = choropleth(bm[["Block", "z"]], geo_for(DISTRICTS), "RdBu_r", f"Block − overall average ({unit})", unit,
                        zmid=0, key_height=620, label_fmt="{:+.1f}")
        st.plotly_chart(hf, **wk(st.plotly_chart), config={"displayModeBar": False}, key="hotmap")
        miss = [b for b in bm["Block"] if b not in MAPPED]
        if miss:
            st.caption(f"Not on the map (no boundary in the 2011 file, but ranked on the right): {', '.join(miss)}.")
    with h2:
        rk = bm.sort_values("z", ascending=True)
        bf = px.bar(rk, x="z", y="Block", color="District", orientation="h", color_discrete_map=DISTRICT_CLR,
                    hover_data={"z": ":+.2f", "District": True})
        bf.update_traces(hovertemplate="<b>%{y}</b><br>%{x:+.2f} " + unit + " vs average<extra></extra>")
        bf.update_layout(xaxis_title=f"Difference from overall average ({unit})", yaxis_title=None,
                         legend_title_text="")
        bf.add_vline(x=0, line_color="#94A3B8")
        bf.update_yaxes(categoryorder="array", categoryarray=list(rk["Block"]), dtick=1)
        st.plotly_chart(style(bf, 620), **wk(st.plotly_chart), config={"displayModeBar": False})

    step(2, "Quick summary")
    top = bm.sort_values("z", ascending=False)
    n_hi, n_lo = int((bm["z"] > 0).sum()), int((bm["z"] <= 0).sum())
    s1, s2, s3 = st.columns([1, 1, 1])
    s1.plotly_chart(donut(["Above average", "Below average"], [n_hi, n_lo], ["#EF4444", "#3B82F6"],
                          "How many blocks are above / below average?", centre=f"{len(bm)}<br>blocks")
                    .update_traces(hovertemplate="%{label}: %{value} blocks<extra></extra>"),
                    **wk(st.plotly_chart), config={"displayModeBar": False})
    def hotcards(df_, title, colour):
        html = "".join(f'<div class="hot" style="background:{colour}"><b>{r.Block}</b> ({r.District})<br>'
                       f'{r.z:+.2f} {unit} vs average</div>' for r in df_.itertuples())
        return f"<h4 style='margin:4px 0 8px 0'>{title}</h4>{html}"
    s2.markdown(hotcards(top.head(3), "🔴 Highest 3 blocks", "linear-gradient(110deg,#DC2626,#F97316)"), unsafe_allow_html=True)
    s3.markdown(hotcards(top.tail(3).iloc[::-1], "🔵 Lowest 3 blocks", "linear-gradient(110deg,#1D4ED8,#06B6D4)"), unsafe_allow_html=True)

# ═════════════════════════════ TAB 4 : results charts ═════════════════════════════
with tab4:
    step(1, "Comparison charts from your verification study")
    say(f"These are your original verification charts for **{label}** (change the variable at the top of the page).")
    pvar = var
    scope = st.segmented_control("Show", ["By season", "By district"], default="By season", key="res_scope") or "By season"
    rf = BASE / "results_final" / VARS[pvar][2]
    rf = rf / (f"{VARS[pvar][2]}_by_District" if pvar == "rain" else "by_District") if scope == "By district" else rf
    if scope == "By district" and not rf.exists():
        rf = BASE / "results_final" / VARS[pvar][2] / "by_District"
    pngs = sorted(rf.glob("*.png")) if rf.exists() else []
    if not pngs:
        st.info("No charts found for this selection.")
    cols = st.columns(2)
    for i, p in enumerate(pngs):
        with cols[i % 2]:
            st.image(str(p), caption=p.stem.replace("_", " "), **wk(st.image))
    xl = [f for f in (rf.glob("*summary*.xlsx") if rf.exists() else [])] + \
         ([rf / "Table1_rainfall_verification.xlsx"] if pvar == "rain" and scope == "By season" else [])
    for f in xl:
        if f.exists():
            with st.expander(f"Table: {f.stem.replace('_', ' ')}"):
                try:
                    t = pd.read_excel(f, header=[0, 1], index_col=0)
                    t = t[t.index.notna()]
                    t.columns = [f"{a} {int(float(b))}" if str(b).replace('.', '').isdigit() else f"{a} {b}"
                                 for a, b in t.columns]
                    st.dataframe(t.round(3), **wk(st.dataframe))
                except Exception:
                    st.dataframe(pd.read_excel(f, header=None), **wk(st.dataframe))
    st.caption("Charts are the originals from results_final.zip. Bias = Block (reference) − District. " + SEASON_MONTHS)
