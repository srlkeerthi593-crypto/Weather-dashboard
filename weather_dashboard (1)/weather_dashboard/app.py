"""
Weather Forecast Verification Dashboard
Anand · Kheda · Mahisagar  |  2021 – 2023
Observed = blockwise data   |   Forecast = districtwise data
"""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ───────────────────────── Page setup ─────────────────────────
st.set_page_config(page_title="Weather Forecast Verification", page_icon="🌦️", layout="wide")

BASE = Path(__file__).parent / "results_final"
YEARS = [2021, 2022, 2023]
SEASONS = ["Winter", "Summer", "Monsoon", "Post-monsoon"]

# parameter → (folder, file prefix, unit, icon)
PARAMS = {
    "Max Temperature":  dict(folder="Tmax",      prefix="Tmax",      unit="°C",   icon="🌡️"),
    "Min Temperature":  dict(folder="Tmin",      prefix="Tmin",      unit="°C",   icon="❄️"),
    "Humidity (RH-I)":  dict(folder="RH-I",      prefix="RHI",       unit="%",    icon="💧"),
    "Humidity (RH-II)": dict(folder="RH-II",     prefix="RHII",      unit="%",    icon="💦"),
    "Wind Speed":       dict(folder="WindSpeed", prefix="WindSpeed", unit="km/h", icon="🌬️"),
}

# colour palette (used in CSS + pies)
TEAL, AMBER, CORAL, INDIGO, SKY, NAVY, GREEN = "#0E9F9A", "#F59E0B", "#EF4444", "#6366F1", "#38BDF8", "#0B2545", "#22C55E"

# ───────────────────────── Theme / CSS ─────────────────────────
st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(180deg,#EAF4FB 0%,#F7FAFC 40%); }}
.block-container {{ padding-top: 1.4rem; max-width: 1250px; }}

/* sidebar */
[data-testid="stSidebar"] {{ background: linear-gradient(180deg,{NAVY} 0%,#13406B 100%); }}
[data-testid="stSidebar"] * {{ color: #EAF4FB !important; }}
[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.18); }}

/* hero banner */
.hero {{ background: linear-gradient(120deg,{NAVY} 0%,#146C94 55%,{TEAL} 100%);
         border-radius: 20px; padding: 26px 32px; color: white; margin-bottom: 18px;
         box-shadow: 0 8px 24px rgba(11,37,69,.25); }}
.hero h1 {{ margin: 0; font-size: 2rem; color: white; }}
.hero p  {{ margin: 6px 0 0 0; opacity: .92; font-size: 1.02rem; }}

/* KPI cards */
.kpi {{ background: white; border-radius: 16px; padding: 16px 18px; height: 100%;
        box-shadow: 0 4px 14px rgba(11,37,69,.08); border-top: 5px solid var(--c); }}
.kpi .lab {{ font-size: .82rem; color: #5B6B7B; text-transform: uppercase; letter-spacing: .04em; }}
.kpi .val {{ font-size: 2rem; font-weight: 800; color: var(--c); line-height: 1.2; }}
.kpi .sub {{ font-size: .82rem; color: #5B6B7B; }}

/* takeaway + info boxes */
.take {{ background: linear-gradient(90deg,#FFF7E0,#FFFBF0); border-left: 6px solid {AMBER};
         border-radius: 12px; padding: 14px 18px; margin: 10px 0 16px 0; color:#4A3A0A; }}
.info {{ background: #E8F7F6; border-left: 6px solid {TEAL}; border-radius: 12px;
         padding: 12px 18px; margin: 6px 0 14px 0; color:#0B4F4C; }}

h2, h3 {{ color: {NAVY}; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ background: white; border-radius: 16px; }}
.bar-row {{ display:flex; align-items:center; margin:8px 0; font-size:.92rem; }}
.bar-row .n {{ width: 150px; color:#12263A; }}
.bar-row .b {{ flex:1; background:#E3ECF3; border-radius:8px; height:16px; overflow:hidden; }}
.bar-row .b > div {{ height:100%; border-radius:8px; background: linear-gradient(90deg,{TEAL},{SKY}); }}
.bar-row .v {{ width: 60px; text-align:right; font-weight:700; color:{NAVY}; }}
</style>
""", unsafe_allow_html=True)


# ───────────────────────── Data loaders ─────────────────────────
@st.cache_data
def load_param(key):
    p = PARAMS[key]
    f = BASE / p["folder"] / f"{p['prefix']}_long_format.xlsx"
    return pd.read_excel(f)

@st.cache_data
def load_param_district(key):
    p = PARAMS[key]
    f = BASE / p["folder"] / "by_District" / f"{p['folder']}_by_District_long.xlsx"
    return pd.read_excel(f)

@st.cache_data
def load_rain_district():
    d = pd.read_excel(BASE / "Rainfall" / "Rainfall_by_District" / "Rainfall_by_District_long.xlsx")
    d["Year"] = d["Year"].astype(str)
    return d

@st.cache_data
def load_rain_table():
    """Season table (Table 1) → tidy dataframe."""
    raw = pd.read_excel(BASE / "Rainfall" / "Table1_rainfall_verification.xlsx", header=[0, 1], index_col=0)
    raw.columns = pd.MultiIndex.from_tuples([(a, int(float(b))) for a, b in raw.columns])
    rows = []
    for season in raw.index:
        for (metric, yr) in raw.columns:
            rows.append(dict(Season=season, Metric=metric, Year=yr, Value=raw.loc[season, (metric, yr)]))
    return pd.DataFrame(rows).dropna(subset=["Season"])


def img(path, caption=None):
    path = BASE / path
    if path.exists():
        st.image(str(path), width="stretch", caption=caption)
    else:
        st.warning(f"Chart not found: {path.name}")


def kpi(col, label, value, sub, color):
    col.markdown(f'<div class="kpi" style="--c:{color}"><div class="lab">{label}</div>'
                 f'<div class="val">{value}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)


def pie(labels, values, colors, title, hole=0.5, center=None):
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=hole, sort=False,
                           marker=dict(colors=colors, line=dict(color="white", width=3)),
                           textinfo="percent", textfont=dict(size=15, color="white"),
                           hovertemplate="%{label}<br>%{value:,} (%{percent})<extra></extra>"))
    fig.update_layout(title=dict(text=title, font=dict(size=16, color=NAVY), x=0.5),
                      height=370, margin=dict(t=60, b=10, l=10, r=10),
                      legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"),
                      paper_bgcolor="rgba(0,0,0,0)")
    if center:
        fig.add_annotation(text=center, x=0.5, y=0.5, showarrow=False, font=dict(size=22, color=NAVY))
    return fig


def quality_label(r):
    return "Strong (r ≥ 0.80)" if r >= 0.8 else ("Moderate (0.60–0.80)" if r >= 0.6 else "Weak (r < 0.60)")

QUAL_COLORS = {"Strong (r ≥ 0.80)": GREEN, "Moderate (0.60–0.80)": AMBER, "Weak (r < 0.60)": CORAL}


def quality_counts(df):
    d = df[df["Season"] != "Annual"]
    return d["Correlation"].apply(quality_label).value_counts().reindex(list(QUAL_COLORS), fill_value=0)


def hero(title, subtitle):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)



# ───────────────────────── Map helpers ─────────────────────────
import json

MAP_PARAMS = {   # label → key, unit, colour scale, label format
    "🌧️ Rainfall":     dict(key="Rainfall", unit="mm",   fmt="{:.0f}", scale=["#EFF6FF", "#93C5FD", "#3B82F6", "#1E3A8A"]),
    "🌡️ Max Temp":     dict(key="Tmax",     unit="°C",   fmt="{:.1f}", scale=["#FEF9C3", "#FDBA74", "#F97316", "#B91C1C"]),
    "❄️ Min Temp":     dict(key="Tmin",     unit="°C",   fmt="{:.1f}", scale=["#ECFEFF", "#67E8F9", "#0EA5E9", "#312E81"]),
    "💧 Humidity I":   dict(key="RH-I",     unit="%",    fmt="{:.1f}", scale=["#F0FDFA", "#5EEAD4", "#14B8A6", "#115E59"]),
    "💦 Humidity II":  dict(key="RH-II",    unit="%",    fmt="{:.1f}", scale=["#F0FDFA", "#5EEAD4", "#14B8A6", "#115E59"]),
    "🌬️ Wind Speed":   dict(key="Wind",     unit="km/h", fmt="{:.1f}", scale=["#FAF5FF", "#D8B4FE", "#A855F7", "#581C87"]),
}
# "close to block data" tolerance used in the hotspot pie (rain = relative %, others absolute)
TOL = {"Rainfall": ("rel", 10), "Tmax": ("abs", 0.5), "Tmin": ("abs", 0.5), "RH-I": ("abs", 2), "RH-II": ("abs", 2), "Wind": ("abs", 1)}
DIVERGING = [[0, "#2563EB"], [0.5, "#F8FAFC"], [1, "#DC2626"]]   # blue = forecast lower · red = forecast higher


def _centroid(feature):
    """Area-weighted centroid of the largest polygon ring (no shapely needed)."""
    g = feature["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    best, best_a = None, -1
    for poly in polys:
        ring = poly[0]; a = cx = cy = 0.0
        for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
            c = x0 * y1 - x1 * y0; a += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c
        if abs(a) > best_a and a != 0:
            best_a, best = abs(a), (cx / (3 * a), cy / (3 * a))
    return best


@st.cache_data
def load_geo():
    root = Path(__file__).parent / "boundaries"
    blocks = json.load(open(root / "blocks.geojson", encoding="utf-8"))
    dists = json.load(open(root / "districts.geojson", encoding="utf-8"))
    cb = {f["properties"]["block"]: _centroid(f) for f in blocks["features"]}
    cd = {f["properties"]["district"]: _centroid(f) for f in dists["features"]}
    b2d = {f["properties"]["block"]: f["properties"]["district"] for f in blocks["features"]}
    xs = [x for f in blocks["features"] for poly in (f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]]) for x, y in poly[0]]
    ys = [y for f in blocks["features"] for poly in (f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]]) for x, y in poly[0]]
    center = dict(lon=(min(xs) + max(xs)) / 2, lat=(min(ys) + max(ys)) / 2)
    return blocks, dists, cb, cd, b2d, center


@st.cache_data
def load_map_stats():
    base = Path(__file__).parent / "data"
    return pd.read_csv(base / "block_stats.csv"), pd.read_csv(base / "district_stats.csv")


def _selected(key, locs):
    """Location clicked on a Plotly map (read from session state, so it is available before redraw)."""
    try:
        pts = st.session_state[key]["selection"]["points"]
    except Exception:
        return None
    if not pts:
        return None
    p = pts[0]
    return p.get("location") or (locs[p["point_index"]] if "point_index" in p else None)


def make_map(geojson, id_prop, locs, vals, labels, cents, scale, zmin, zmax, unit, center,
             outline=(), outline2=(), zoom=8.1, label_size=11, colorbar_title=None, height=520):
    """Choropleth + value labels. `outline` = selected polygons (navy), `outline2` = hotspots (black)."""
    fig = go.Figure(go.Choroplethmap(
        geojson=geojson, locations=locs, z=vals, featureidkey=f"properties.{id_prop}",
        colorscale=scale, zmin=zmin, zmax=zmax, marker_opacity=0.88, marker_line_width=1.3, marker_line_color="white",
        selected=dict(marker=dict(opacity=0.88)), unselected=dict(marker=dict(opacity=0.88)),
        hovertemplate="<b>%{location}</b><br>%{z:.2f} " + unit + "<extra></extra>",
        colorbar=dict(title=dict(text=colorbar_title or unit, side="right"), thickness=12, len=0.75, x=1.0)))
    for locset, color, w in ((outline2, "#111827", 3), (outline, NAVY, 5)):
        if len(locset):
            fig.add_trace(go.Choroplethmap(
                geojson=geojson, locations=list(locset), z=[0] * len(locset), featureidkey=f"properties.{id_prop}",
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False, hoverinfo="skip",
                marker_line_width=w, marker_line_color=color))
    # value labels – dark text on light fills, white text on dark fills
    span = (zmax - zmin) or 1
    for dark in (False, True):
        pick = [l for l, v in zip(locs, vals) if ((v - zmin) / span > 0.62) == dark]
        if pick:
            fig.add_trace(go.Scattermap(
                lon=[cents[l][0] for l in pick], lat=[cents[l][1] for l in pick], mode="text",
                text=[labels[l] for l in pick], textfont=dict(size=label_size, color="white" if dark else NAVY),
                hoverinfo="skip", showlegend=False))
    fig.update_layout(map=dict(style="carto-positron", center=center, zoom=zoom),
                      margin=dict(t=0, b=0, l=0, r=0), height=height, clickmode="event+select",
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


# ───────────────────────── Sidebar ─────────────────────────
with st.sidebar:
    st.markdown("## 🌦️ Forecast Verification")
    st.caption("Anand · Kheda · Mahisagar  \n2021 – 2023")
    page = st.radio("Go to", ["🏠 Overview", "🗺️ Map Comparison", "🌧️ Rainfall", "🌡️ Temperature, Humidity & Wind",
                              "📍 District Comparison", "🔧 Bias Correction"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**How the data is used**")
    st.caption("**Observed** → block-wise data  \n**Forecast** → district-wise data  \n"
               "Seasons: Winter · Summer · Monsoon · Post-monsoon")


# ═════════════════════════ 1. OVERVIEW ═════════════════════════
if page == "🏠 Overview":
    hero("How good are our weather forecasts?",
         "Forecast vs. observed weather for 3 districts over 3 years — in one glance.")

    rd = load_rain_district()
    yr = rd[rd["Year"].isin(["2021", "2022", "2023"])]
    tot = yr[["NN", "NY", "YN", "YY", "N"]].sum()
    ratio = (tot.YY + tot.NN) / tot.N * 100
    pod = tot.YY / (tot.YY + tot.YN) * 100

    tmax = load_param("Max Temperature"); tmax_a = tmax[tmax.Season == "Annual"]

    c = st.columns(4)
    kpi(c[0], "Rainfall accuracy", f"{ratio:.1f}%", "days correctly forecast (rain / no rain)", TEAL)
    kpi(c[1], "Rain events caught", f"{pod:.1f}%", "of actual rainy days were forecast", INDIGO)
    kpi(c[2], "Max-temp error", f"{tmax_a.RMSE.mean():.2f} °C", "average RMSE over 3 years", AMBER)
    kpi(c[3], "Max-temp match", f"{tmax_a.Correlation.mean():.2f}", "correlation (1.0 = perfect)", CORAL)
    st.write("")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.plotly_chart(pie(["Rain forecast & rain happened (Hit)", "No rain forecast & none happened",
                                 "Rain forecast but none (False alarm)", "Rain happened but not forecast (Miss)"],
                                [tot.YY, tot.NN, tot.NY, tot.YN], [GREEN, SKY, AMBER, CORAL],
                                "Rainfall forecast outcomes (rain ≥ 2.5 mm, all districts, 2021–23)",
                                center=f"{ratio:.0f}%<br><span style='font-size:12px'>correct</span>"),
                            width="stretch")
    with right:
        with st.container(border=True):
            tot_q = sum(quality_counts(load_param(k)) for k in PARAMS)
            st.plotly_chart(pie(list(tot_q.index), list(tot_q.values), [QUAL_COLORS[i] for i in tot_q.index],
                                "Temperature, humidity & wind — forecast quality",
                                center=f"{int(tot_q.sum())}<br><span style='font-size:12px'>checks</span>"),
                            width="stretch")
            st.caption("Each check = one parameter × one season × one year, rated by correlation with observations.")

    with st.container(border=True):
        st.markdown("#### 🏆 Which parameter is forecast best? (average correlation, 2021–23)")
        rows = []
        for k in PARAMS:
            d = load_param(k); rows.append((k, d[d.Season == "Annual"].Correlation.mean()))
        rows.sort(key=lambda t: -t[1])
        html = "".join(f'<div class="bar-row"><div class="n">{PARAMS[k]["icon"]} {k}</div>'
                       f'<div class="b"><div style="width:{v*100:.0f}%"></div></div><div class="v">{v:.2f}</div></div>'
                       for k, v in rows)
        st.markdown(html, unsafe_allow_html=True)

    mon = load_rain_table(); mon = mon[(mon.Season == "Monsoon") & (mon.Metric == "Ratio score (%)")].Value.mean()
    ann = load_rain_table(); ann = ann[(ann.Season == "Annual") & (ann.Metric == "Ratio score (%)")].Value.mean()
    st.markdown(f'<div class="take">💡 <b>Key message:</b> Rainfall is correctly forecast on about <b>{ann:.0f}%</b> of days '
                f'over the year, but accuracy drops to about <b>{mon:.0f}%</b> in the monsoon — the hardest season to forecast. '
                f'Best-matched parameter: <b>{rows[0][0]}</b>.</div>', unsafe_allow_html=True)



# ═════════════════════════ MAP COMPARISON ═════════════════════════
elif page == "🗺️ Map Comparison":
    hero("🗺️ Block vs District — Map Comparison",
         "Left: block-wise values (observed).  Right: district-wise values (forecast).  Click an area to compare.")

    blocks_gj, dists_gj, cent_b, cent_d, b2d, center = load_geo()
    bst, dst_ = load_map_stats()

    # ---- shared controls
    c1, c2, c3 = st.columns([3, 2, 3])
    plabel = c1.segmented_control("Parameter", list(MAP_PARAMS), default="🌡️ Max Temp", key="mp_param") or "🌡️ Max Temp"
    ylabel = c2.segmented_control("Year", ["All years", "2021", "2022", "2023"], default="All years", key="mp_year") or "All years"
    slabel = c3.segmented_control("Season", ["All seasons", "Winter", "Summer", "Monsoon", "Post-monsoon"],
                                  default="All seasons", key="mp_season") or "All seasons"
    P = MAP_PARAMS[plabel]; u = P["unit"]; fmt = P["fmt"]
    yk = "All" if ylabel == "All years" else ylabel
    sk = "All" if slabel == "All seasons" else slabel
    period = f"{ylabel} · {slabel}"

    B = bst[(bst.Param == P["key"]) & (bst.Year == yk) & (bst.Season == sk)].set_index("Block")
    D = dst_[(dst_.Param == P["key"]) & (dst_.Year == yk) & (dst_.Season == sk)].set_index("District")
    block_locs, dist_locs = list(B.index), list(D.index)
    rain_note = " (total over the period; averaged per year when 'All years')" if P["key"] == "Rainfall" else " (average)"

    # ---- click handling (map click → shared selection)
    ss = st.session_state
    bc, dc = _selected("blockmap", block_locs), _selected("distmap", dist_locs)
    if bc is None: ss["last_b"] = None
    elif bc != ss.get("last_b"):
        ss["last_b"] = bc; ss["sel_block_box"] = bc; ss["sel_dist"] = None
    if dc is None: ss["last_d"] = None
    elif dc != ss.get("last_d"):
        ss["last_d"] = dc; ss["sel_block_box"] = "(none)"; ss["sel_dist"] = dc
    sel_block = ss.get("sel_block_box", "(none)")
    sel_block = None if sel_block == "(none)" or sel_block not in b2d else sel_block
    sel_dist = b2d[sel_block] if sel_block else ss.get("sel_dist")

    # ---- Part A: side-by-side maps
    st.markdown(f"### Side-by-side comparison — {plabel.split(' ',1)[1]}{rain_note}")
    top = st.container()
    zmin = float(min(B.Observed.min(), D.Forecast.min())); zmax = float(max(B.Observed.max(), D.Forecast.max()))
    if zmax - zmin < 1e-9: zmax = zmin + 1
    out_left = [sel_block] if sel_block else ([b for b in block_locs if b2d[b] == sel_dist] if sel_dist else [])
    out_right = [sel_dist] if sel_dist else []

    L, R = st.columns(2)
    with L:
        with st.container(border=True):
            st.markdown("**🟦 Block-wise — Observed** (24 blocks)")
            fig = make_map(blocks_gj, "block", block_locs, B.Observed.tolist(), {b: fmt.format(B.Observed[b]) for b in block_locs},
                           cent_b, P["scale"], zmin, zmax, u, center, outline=out_left, label_size=10)
            st.plotly_chart(fig, key="blockmap", on_select="rerun", selection_mode="points", width="stretch",
                            config={"displayModeBar": False, "scrollZoom": False})
    with R:
        with st.container(border=True):
            st.markdown("**🟧 District-wise — Forecast** (3 districts)")
            fig = make_map(dists_gj, "district", dist_locs, D.Forecast.tolist(),
                           {d: f"{d}<br>{fmt.format(D.Forecast[d])}" for d in dist_locs},
                           cent_d, P["scale"], zmin, zmax, u, center, outline=out_right, label_size=13)
            st.plotly_chart(fig, key="distmap", on_select="rerun", selection_mode="points", width="stretch",
                            config={"displayModeBar": False, "scrollZoom": False})
    st.caption(f"Both maps use the same colour scale so colours can be compared directly · Period: {period}")

    with top:
        pick = st.selectbox("🔎 Click a block / district on the maps — or choose a block here",
                            ["(none)"] + sorted(block_locs), key="sel_block_box")

    # ---- click result panel
    if sel_block:
        o, f_ = float(B.Observed[sel_block]), float(D.Forecast[b2d[sel_block]]); dd = f_ - o
        pct = f" ({dd / o * 100:+.1f}%)" if o else ""
        c = st.columns(3)
        kpi(c[0], f"Block · {sel_block}", f"{fmt.format(o)} {u}", f"observed · {b2d[sel_block]} district", TEAL)
        kpi(c[1], f"District · {b2d[sel_block]}", f"{fmt.format(f_)} {u}", "forecast (district-wise)", AMBER)
        kpi(c[2], "Forecast − Block", f"{dd:+.2f} {u}", f"forecast is {'HIGHER' if dd > 0 else 'LOWER'} than block data{pct}", CORAL if dd > 0 else INDIGO)
    elif sel_dist:
        mem = B[B.District == sel_dist]; o = float(mem.Observed.mean()); f_ = float(D.Forecast[sel_dist]); dd = f_ - o
        c = st.columns(3)
        kpi(c[0], f"District · {sel_dist}", f"{fmt.format(f_)} {u}", "forecast (district-wise)", AMBER)
        kpi(c[1], f"Its {len(mem)} blocks (average)", f"{fmt.format(o)} {u}", f"range {fmt.format(mem.Observed.min())} – {fmt.format(mem.Observed.max())} {u}", TEAL)
        kpi(c[2], "Forecast − Blocks", f"{dd:+.2f} {u}", f"forecast is {'HIGHER' if dd > 0 else 'LOWER'} than the block average", CORAL if dd > 0 else INDIGO)
    else:
        st.markdown('<div class="info">👆 <b>Click any block</b> on the left map to see its observed value next to its district forecast, '
                    'or <b>click a district</b> on the right map to compare it with all its blocks.</div>', unsafe_allow_html=True)

    # ---- Part B: spatial hotspots
    st.markdown("---")
    st.markdown("### 🔥 Spatial hotspots — where is the forecast higher or lower than the block data?")
    diff = B["Diff"]                       # Forecast − Block
    sd = diff.std(); z = (diff - diff.mean()) / (sd if sd else 1)
    hot = [b for b in block_locs if abs(z[b]) >= 1]
    lim = float(max(abs(diff.min()), abs(diff.max()), 1e-6))
    mode, tol = TOL[P["key"]]
    thr = (B.Observed.abs() * tol / 100) if mode == "rel" else pd.Series(tol, index=B.index)
    higher = int((diff > thr).sum()); lower = int((diff < -thr).sum()); close = len(diff) - higher - lower

    hl, hr = st.columns([3, 2])
    with hl:
        with st.container(border=True):
            st.markdown(f"**Forecast − Block difference ({u})** · ★ = hotspot")
            dl = {b: f"{'★ ' if b in hot else ''}{diff[b]:+.1f}" if P["key"] != "Rainfall" else f"{'★ ' if b in hot else ''}{diff[b]:+.0f}" for b in block_locs}
            fig = make_map(blocks_gj, "block", block_locs, diff.tolist(), dl, cent_b, DIVERGING, -lim, lim, u, center,
                           outline2=hot, label_size=10, colorbar_title=f"{u}", height=500)
            fig.update_layout(clickmode="none")
            st.plotly_chart(fig, key="hotmap", width="stretch", config={"displayModeBar": False, "scrollZoom": False})
            st.caption("🔴 red = forecast higher than block data · 🔵 blue = forecast lower · black outline = hotspot")
    with hr:
        with st.container(border=True):
            st.plotly_chart(pie(["Forecast higher", "Close to block data", "Forecast lower"], [higher, close, lower],
                                [CORAL, GREEN, INDIGO], "How many blocks?", center=f"{len(diff)}<br><span style='font-size:12px'>blocks</span>"),
                            width="stretch")
            st.caption("“Close” = within ±" + (f"{tol}% of the block value" if mode == "rel" else f"{tol} {u}") + ".")
        with st.container(border=True):
            st.markdown("**Top hotspots (largest gap)**")
            top5 = diff.reindex(diff.abs().sort_values(ascending=False).index).head(5)
            mx = float(top5.abs().max()) or 1
            html = "".join(
                f'<div class="bar-row"><div class="n">{b} <small style="color:#6B7B8B">({b2d[b][:3]}.)</small></div>'
                f'<div class="b"><div style="width:{abs(v)/mx*100:.0f}%;background:{CORAL if v > 0 else INDIGO}"></div></div>'
                f'<div class="v" style="width:80px">{v:+.{0 if P["key"]=="Rainfall" else 2}f}</div></div>' for b, v in top5.items())
            st.markdown(html, unsafe_allow_html=True)
    hi, lo = diff.idxmax(), diff.idxmin()
    under_txt = (f"largest under-forecast: <b>{lo}</b> ({diff[lo]:+.2f} {u})" if diff[lo] < 0
                 else f"smallest gap: <b>{diff.abs().idxmin()}</b> ({diff[diff.abs().idxmin()]:+.2f} {u}) — no block is under-forecast")
    st.markdown(f'<div class="take">💡 <b>Key message ({period}):</b> the forecast is higher than block data in <b>{higher}</b> of {len(diff)} blocks, '
                f'lower in <b>{lower}</b>, and close in <b>{close}</b>. Largest over-forecast: <b>{hi}</b> ({diff[hi]:+.2f} {u}); '
                f'{under_txt}.<br>'
                f'<small>Hotspot = a block whose gap differs from the average gap of all 24 blocks by more than 1 standard deviation. '
                f'Note: here difference = <b>Forecast − Block</b> (the Bias page uses Observed − Forecast, so signs are reversed).</small></div>',
                unsafe_allow_html=True)


# ═════════════════════════ 2. RAINFALL ═════════════════════════
elif page == "🌧️ Rainfall":
    hero("🌧️ Rainfall Forecast Verification", "Did the forecast say 'rain' when it rained, and 'no rain' when it didn't?")

    rd = load_rain_district()
    choice = st.segmented_control("Year", ["All years"] + [str(y) for y in YEARS], default="All years") or "All years"
    sel = rd[rd["Year"].isin(["2021", "2022", "2023"])] if choice == "All years" else rd[rd["Year"] == choice]
    t = sel[["NN", "NY", "YN", "YY", "N"]].sum()
    ratio = (t.YY + t.NN) / t.N * 100
    pod = t.YY / (t.YY + t.YN) * 100
    hk = (t.YY * t.NN - t.NY * t.YN) / ((t.YY + t.YN) * (t.NN + t.NY))

    c = st.columns(3)
    kpi(c[0], "Ratio score", f"{ratio:.1f}%", "days correct out of all days", TEAL)
    kpi(c[1], "Probability of Detection", f"{pod:.1f}%", "rainy days that were forecast", INDIGO)
    kpi(c[2], "HK score", f"{hk:.2f}", "overall skill (1 = perfect, 0 = no skill)", AMBER)
    st.write("")

    p1, p2 = st.columns(2)
    with p1:
        with st.container(border=True):
            st.plotly_chart(pie(["Hit", "Correct 'no rain'", "False alarm", "Miss"],
                                [t.YY, t.NN, t.NY, t.YN], [GREEN, SKY, AMBER, CORAL],
                                f"Forecast outcomes — {choice}"), width="stretch")
    with p2:
        with st.container(border=True):
            st.plotly_chart(pie(["Correct forecasts", "Wrong forecasts"], [t.YY + t.NN, t.NY + t.YN],
                                [TEAL, CORAL], f"Right vs wrong — {choice}",
                                center=f"{ratio:.0f}%"), width="stretch")
    st.markdown('<div class="info"><b>Hit</b> = rain forecast and it rained · <b>Miss</b> = it rained but no forecast · '
                '<b>False alarm</b> = rain forecast but dry · Rain day = ≥ 2.5 mm</div>', unsafe_allow_html=True)

    st.markdown("### Season-wise results")
    chart = st.segmented_control("Choose a chart",
                                 ["Ratio score", "HK score", "Rain detected (PoD)", "Forecast error (RMSE)"],
                                 default="Ratio score") or "Ratio score"
    files = {"Ratio score": "chart1_ratio_score.png", "HK score": "chart2_hk_score_labeled.png",
             "Rain detected (PoD)": "chart4_Rainfall_PoD.png", "Forecast error (RMSE)": "chart3_rmse_trend.png"}
    notes = {"Ratio score": "Share of days the forecast got right. Higher = better.",
             "HK score": "Balances catching rain against false alarms. Higher = better.",
             "Rain detected (PoD)": "Of the days it really rained, how many were forecast. Higher = better.",
             "Forecast error (RMSE)": "Typical size of rainfall error in mm. Lower = better."}
    with st.container(border=True):
        img(f"Rainfall/{files[chart]}")
        st.caption(notes[chart])

    with st.expander("📊 More scores (Miss rate, False alarms, CSI, FAR)"):
        a, b = st.columns(2)
        with a: img("Rainfall/chart4a_MissRate.png"); img("Rainfall/chart4c_CSI.png")
        with b: img("Rainfall/chart4b_POFD.png"); img("Rainfall/chart4d_FAR.png")

    tb = load_rain_table(); r = tb[(tb.Metric == "Ratio score (%)") & (tb.Season != "Annual")].groupby("Season").Value.mean()
    st.markdown(f'<div class="take">💡 <b>Key message:</b> Forecasts are most reliable in <b>{r.idxmax()}</b> '
                f'(~{r.max():.0f}% correct) and weakest in <b>{r.idxmin()}</b> (~{r.min():.0f}%), the season with the most rainfall. '
                f'<br><small>Dry seasons show "N/A" HK scores when no rain ≥ 2.5 mm occurred.</small></div>', unsafe_allow_html=True)


# ═════════════════════════ 3. TEMPERATURE / HUMIDITY / WIND ═════════════════════════
elif page == "🌡️ Temperature, Humidity & Wind":
    hero("🌡️ Temperature, Humidity & Wind", "How close is the forecast to what was actually measured?")

    names = list(PARAMS)
    param = st.segmented_control("Parameter", names, default=names[0]) or names[0]
    P = PARAMS[param]; u = P["unit"]
    d = load_param(param); ann = d[d.Season == "Annual"]

    c = st.columns(3)
    kpi(c[0], "Average error (RMSE)", f"{ann.RMSE.mean():.2f} {u}", "lower is better", AMBER)
    kpi(c[1], "Correlation", f"{ann.Correlation.mean():.2f}", "closer to 1 is better", TEAL)
    b = ann["Mean_Bias (O-P)"].mean()
    kpi(c[2], "Average bias", f"{b:+.2f} {u}", "forecast too high" if b < 0 else "forecast too low", INDIGO)
    st.write("")

    left, right = st.columns([3, 2])
    with left:
        metric = st.segmented_control("Show", ["Error (RMSE)", "Correlation", "Bias"], default="Error (RMSE)") or "Error (RMSE)"
        idx = {"Error (RMSE)": 1, "Correlation": 2, "Bias": 3}[metric]
        fname = sorted((BASE / P["folder"]).glob(f"chart{idx}_*.png"))[0].name
        with st.container(border=True):
            img(f"{P['folder']}/{fname}")
        st.caption({1: "Typical size of the forecast error — lower is better.",
                    2: "How well forecast and observed move together — higher is better.",
                    3: "Observed − Forecast. Below 0 means the forecast ran too high; above 0 means too low."}[idx])
    with right:
        with st.container(border=True):
            q = quality_counts(d)
            st.plotly_chart(pie(list(q.index), list(q.values), [QUAL_COLORS[i] for i in q.index],
                                f"{param}: forecast quality", center=f"{int(q.sum())}<br><span style='font-size:12px'>checks</span>"),
                            width="stretch")
            st.caption("Each check = one season × one year.")

    s = d[d.Season != "Annual"].groupby("Season").Correlation.mean()
    st.markdown(f'<div class="take">💡 <b>Key message:</b> {param} matches observations best in <b>{s.idxmax()}</b> '
                f'(r ≈ {s.max():.2f}) and least in <b>{s.idxmin()}</b> (r ≈ {s.min():.2f}).</div>', unsafe_allow_html=True)


# ═════════════════════════ 4. DISTRICT COMPARISON ═════════════════════════
elif page == "📍 District Comparison":
    hero("📍 District Comparison", "Anand vs Kheda vs Mahisagar — which district is forecast best?")

    opts = ["🌧️ Rainfall"] + [f"{v['icon']} {k}" for k, v in PARAMS.items()]
    sel = st.segmented_control("Parameter", opts, default=opts[0]) or opts[0]

    if sel.startswith("🌧️"):
        rd = load_rain_district(); pooled = rd[rd.Year == "2021-23 Pooled"].set_index("District")
        c = st.columns(3)
        for col, (dist, color) in zip(c, zip(pooled.index, [TEAL, INDIGO, AMBER])):
            kpi(col, dist, f"{pooled.loc[dist, 'Ratio_score']*100:.1f}%",
                f"rainfall accuracy · HK {pooled.loc[dist, 'HK_score']:.2f}", color)
        st.write("")
        p1, p2 = st.columns([2, 3])
        with p1:
            with st.container(border=True):
                st.plotly_chart(pie(list(pooled.index), list(pooled.YY), [TEAL, INDIGO, AMBER],
                                    "Share of rain events caught (hits)", center="Hits"), width="stretch")
        with p2:
            m = st.segmented_control("Show", ["Ratio score", "HK score", "Rain detected (PoD)"], default="Ratio score") or "Ratio score"
            f = {"Ratio score": "chart1_District_RatioScore.png", "HK score": "chart2_District_HK.png",
                 "Rain detected (PoD)": "chart3_District_PoD.png"}[m]
            with st.container(border=True):
                img(f"Rainfall/Rainfall_by_District/{f}")
        best = pooled.Ratio_score.idxmax()
        st.markdown(f'<div class="take">💡 <b>Key message:</b> <b>{best}</b> has the highest rainfall accuracy '
                    f'({pooled.Ratio_score.max()*100:.1f}%). Differences between districts are small, so forecast quality is fairly uniform across the region.</div>',
                    unsafe_allow_html=True)
    else:
        param = sel.split(" ", 1)[1]; P = PARAMS[param]; u = P["unit"]
        dd = load_param_district(param)
        avg = dd.groupby("District")[["RMSE", "Correlation", "Mean_Bias (O-P)"]].mean()
        c = st.columns(3)
        for col, (dist, color) in zip(c, zip(avg.index, [TEAL, INDIGO, AMBER])):
            kpi(col, dist, f"{avg.loc[dist, 'RMSE']:.2f} {u}", f"avg error (RMSE) · r = {avg.loc[dist, 'Correlation']:.2f}", color)
        st.write("")
        p1, p2 = st.columns([2, 3])
        with p1:
            with st.container(border=True):
                inv = 1 / avg["RMSE"]   # larger slice = smaller error = better
                st.plotly_chart(pie(list(avg.index), list(inv.values), [TEAL, INDIGO, AMBER],
                                    "Forecast reliability share (larger = lower error)", center="Reliability"),
                                width="stretch")
        with p2:
            m = st.segmented_control("Show", ["Error (RMSE)", "Correlation", "Bias"], default="Error (RMSE)") or "Error (RMSE)"
            f = {"Error (RMSE)": "chart1_RMSE_by_District.png", "Correlation": "chart2_Correlation_by_District.png",
                 "Bias": "chart3_Bias_by_District.png"}[m]
            with st.container(border=True):
                img(f"{P['folder']}/by_District/{f}")
        best = avg.RMSE.idxmin()
        st.markdown(f'<div class="take">💡 <b>Key message:</b> For {param.lower()}, <b>{best}</b> has the lowest error '
                    f'({avg.RMSE.min():.2f} {u}); <b>{avg.RMSE.idxmax()}</b> has the highest ({avg.RMSE.max():.2f} {u}).</div>',
                    unsafe_allow_html=True)


# ═════════════════════════ 5. BIAS CORRECTION ═════════════════════════
else:
    hero("🔧 Bias Correction", "Forecasts that run consistently high or low can be corrected — here is where it matters most.")

    st.markdown("### Current bias in the raw forecast (Observed − Forecast, annual)")
    rows = []
    for k, P in PARAMS.items():
        d = load_param(k); a = d[d.Season == "Annual"].set_index("Year")["Mean_Bias (O-P)"]
        rows.append({"Parameter": f"{P['icon']} {k}", "Unit": P["unit"], **{str(y): round(a.get(y, float('nan')), 2) for y in YEARS}})
    tb = pd.DataFrame(rows)
    st.dataframe(tb.style.background_gradient(cmap="RdYlGn_r", subset=[str(y) for y in YEARS], vmin=-3, vmax=3)
                 .format({str(y): "{:+.2f}" for y in YEARS}), width="stretch", hide_index=True)
    st.caption("Negative = forecast too high · Positive = forecast too low · Values near 0 = little correction needed.")

    st.markdown('<div class="info">🛠️ <b>Bias-correction results are not in the dashboard yet.</b> '
                'Send the bias-correction code/results and they will be added here as a Before-vs-After view.</div>',
                unsafe_allow_html=True)
