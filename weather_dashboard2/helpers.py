"""All shared code: data loading, metrics, map drawing and styling."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ───────────────────────── DATA & METRICS ─────────────────────────
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
YEARS = [2021, 2022, 2023]
SEASON_ORDER = ["Winter", "Pre-monsoon", "Monsoon", "Post-monsoon"]

# column in Excel -> short key
VARIABLES = {
    "Rainfall (mm)": "Rain",
    "Tmax (°C)": "Tmax",
    "Tmin (°C)": "Tmin",
    "RH-I (%)": "RH-I",
    "RH-II (%)": "RH-II",
    "Wind Speed (km/h)": "Wind",
}
LABELS = {  # friendly label -> short key
    "Rainfall (mm)": "Rain", "Max temperature (°C)": "Tmax", "Min temperature (°C)": "Tmin",
    "Morning humidity RH-I (%)": "RH-I", "Afternoon humidity RH-II (%)": "RH-II",
    "Wind speed (km/h)": "Wind",
}
KEY_TO_LABEL = {v: k for k, v in LABELS.items()}
UNITS = {"Rain": "mm", "Tmax": "°C", "Tmin": "°C", "RH-I": "%", "RH-II": "%", "Wind": "km/h"}
# "close enough" tolerance used for the representativeness score
TOLERANCE = {"Tmax": 2.0, "Tmin": 2.0, "RH-I": 10.0, "RH-II": 10.0, "Wind": 3.0}
RAIN_THRESHOLD = 2.5


def season_of(month: int) -> str:
    if month in (3, 4, 5):
        return "Pre-monsoon"
    if month in (6, 7, 8, 9):
        return "Monsoon"
    if month in (10, 11):
        return "Post-monsoon"
    return "Winter"


@st.cache_data(show_spinner="Loading weather data…")
def load_merged() -> pd.DataFrame:
    """One row per block-day with <var>_blk and <var>_dst columns."""
    blocks, dists = [], []
    for y in YEARS:
        f = DATA_DIR / f"Weather_{y}_365days_Complete_Anand_Kheda_Mahisagar.xlsx"
        if not f.exists():
            raise FileNotFoundError(f"Missing {f.name} in the data/ folder.")
        blocks.append(pd.read_excel(f, sheet_name="blockwise"))
        dists.append(pd.read_excel(f, sheet_name="districtwise"))
    b = pd.concat(blocks, ignore_index=True)
    d = pd.concat(dists, ignore_index=True)
    b = b.rename(columns={c: f"{k}_blk" for c, k in VARIABLES.items()})
    d = d.rename(columns={c: f"{k}_dst" for c, k in VARIABLES.items()})
    b = b[["Date", "District", "Block"] + [f"{k}_blk" for k in VARIABLES.values()]]
    d = d[["Date", "District"] + [f"{k}_dst" for k in VARIABLES.values()]]
    df = b.merge(d, on=["Date", "District"], how="left", validate="many_to_one")
    df["Date"] = pd.to_datetime(df["Date"])
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Season"] = df["Month"].map(season_of)
    return df


@st.cache_data
def load_geojson() -> dict:
    with open(DATA_DIR / "blocks.geojson", encoding="utf-8") as f:
        gj = json.load(f)
    for ft in gj["features"]:               # plotly matches on feature id
        ft["id"] = ft["properties"]["block"]
    return gj


@st.cache_data
def block_table() -> pd.DataFrame:
    """block, district, lon, lat for blocks that have a boundary polygon."""
    gj = load_geojson()
    return pd.DataFrame([ft["properties"] for ft in gj["features"]])


# ───────────────────────────── metrics ─────────────────────────────
def continuous_metrics(blk: pd.Series, dst: pd.Series, key: str) -> dict:
    """Block is the reference, district is compared to it. Bias = block − district (O − P)."""
    ok = blk.notna() & dst.notna()
    o, p = blk[ok].to_numpy(float), dst[ok].to_numpy(float)
    if len(o) < 3:
        return dict(N=len(o), RMSE=np.nan, MAE=np.nan, Bias=np.nan, Corr=np.nan, Within=np.nan)
    diff = o - p
    corr = np.corrcoef(o, p)[0, 1] if o.std() > 0 and p.std() > 0 else np.nan
    if key == "Rain":
        within = ((o >= RAIN_THRESHOLD) == (p >= RAIN_THRESHOLD)).mean() * 100
    else:
        within = (np.abs(diff) <= TOLERANCE[key]).mean() * 100
    return dict(N=len(o), RMSE=np.sqrt((diff ** 2).mean()), MAE=np.abs(diff).mean(),
                Bias=diff.mean(), Corr=corr, Within=within)


def rain_scores(blk: pd.Series, dst: pd.Series, thr: float = RAIN_THRESHOLD) -> dict:
    o, p = blk >= thr, dst >= thr
    H, F, M, Z = (o & p).sum(), (~o & p).sum(), (o & ~p).sum(), (~o & ~p).sum()
    n = H + F + M + Z
    div = lambda a, b: a / b if b else np.nan
    pod, pofd = div(H, H + M), div(F, F + Z)
    return dict(Ratio=div(H + Z, n) * 100, PoD=pod, Miss=div(M, H + M), POFD=pofd,
                HK=pod - pofd if not (np.isnan(pod) or np.isnan(pofd)) else np.nan,
                CSI=div(H, H + F + M), FAR=div(F, H + F), Hits=H, FalseAlarms=F, Misses=M, CorrectNeg=Z)


def scorecard(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Continuous metrics for all 5 non-rain variables + rain, grouped by `by`."""
    rows = []
    groups = df.groupby(by) if by else [((), df)]
    for g, sub in groups:
        g = g if isinstance(g, tuple) else (g,)
        for key in VARIABLES.values():
            m = continuous_metrics(sub[f"{key}_blk"], sub[f"{key}_dst"], key)
            rows.append({**dict(zip(by, g)), "Variable": key, **m})
    return pd.DataFrame(rows)

# ───────────────────────── STYLE ─────────────────────────
DIST_COLOR = {"Anand": "#2563EB", "Kheda": "#16A34A", "Mahisagar": "#F97316"}
BLOCK_COLOR = "#7C3AED"      # purple = block (local)
DISTRICT_COLOR = "#0EA5E9"   # sky blue = district (whole area)
GOOD, OK, BAD = "#16A34A", "#F59E0B", "#EF4444"
VAR_ICON = {"Rain": "🌧️", "Tmax": "🔥", "Tmin": "❄️", "RH-I": "💧", "RH-II": "💦", "Wind": "🌬️"}
VAR_COLOR = {"Rain": "#3B82F6", "Tmax": "#EF4444", "Tmin": "#06B6D4", "RH-I": "#8B5CF6", "RH-II": "#EC4899", "Wind": "#10B981"}

CSS = """
<style>
.block-container {padding-top: 1.4rem; max-width: 1300px;}
.hero {background: linear-gradient(120deg,#7c3aed,#2563eb 55%,#06b6d4); color:#fff; padding:1.5rem 1.8rem;
       border-radius:18px; margin-bottom:1rem; box-shadow:0 6px 18px rgba(37,99,235,.25);}
.hero h1 {margin:0; font-size:2rem; color:#fff;}
.hero p {margin:.4rem 0 0; opacity:.95; font-size:1.05rem;}
.tip {background:#fffbeb; border-left:6px solid #f59e0b; padding:.8rem 1rem; border-radius:10px; color:#78350f; margin:.6rem 0;}
.say {background:#ecfdf5; border-left:6px solid #10b981; padding:.8rem 1rem; border-radius:10px; color:#064e3b; margin:.6rem 0;}
.step {background:linear-gradient(90deg,#ede9fe,#e0f2fe); padding:.5rem 1rem; border-radius:10px; font-weight:700;
       color:#312e81; margin:1.1rem 0 .5rem;}
.card {border-radius:16px; padding:1rem 1.1rem; color:#fff; box-shadow:0 4px 12px rgba(0,0,0,.12);}
.card h3 {margin:0 0 .5rem; color:#fff;}
.card table {width:100%; border-collapse:collapse;}
.card td {padding:5px 2px; border-bottom:1px solid rgba(255,255,255,.28); font-size:1rem;}
.card td:last-child {text-align:right; font-weight:700;}
.pill {display:inline-block; padding:2px 10px; border-radius:999px; background:rgba(255,255,255,.25); font-size:.78rem; font-weight:700;}
.kpi {border-radius:14px; padding:.8rem 1rem; color:#fff; text-align:center;}
.kpi b {font-size:1.6rem; display:block;}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(emoji, title, subtitle):
    st.markdown(f'<div class="hero"><h1>{emoji} {title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def step(text):
    st.markdown(f'<div class="step">{text}</div>', unsafe_allow_html=True)


def tip(html):
    st.markdown(f'<div class="tip">💡 {html}</div>', unsafe_allow_html=True)


def say(html):
    st.markdown(f'<div class="say">📝 {html}</div>', unsafe_allow_html=True)


def kpi(col, label, value, color):
    col.markdown(f'<div class="kpi" style="background:{color}"><b>{value}</b>{label}</div>', unsafe_allow_html=True)


def plot(fig, key=None, select=False):
    """Show a plotly figure. Works on old and new Streamlit. Returns selection event (or None)."""
    attempts = []
    if select:
        attempts += [dict(on_select="rerun", width="stretch"), dict(on_select="rerun", use_container_width=True)]
    attempts += [dict(width="stretch"), dict(use_container_width=True), dict()]
    for kw in attempts:
        try:
            return st.plotly_chart(fig, key=key, **kw)
        except TypeError:
            continue


def table(df, **kw):
    try:
        st.dataframe(df, hide_index=True, width="stretch", **kw)
    except TypeError:
        st.dataframe(df, hide_index=True, use_container_width=True, **kw)


def image(path):
    try:
        st.image(str(path), width="stretch")
    except TypeError:
        st.image(str(path), use_container_width=True)


def need_data():
    try:
        return load_merged()
    except FileNotFoundError as e:
        st.error(str(e))
        st.info("Put the 3 yearly Excel files in the `data/` folder and reload.")
        st.stop()


def verdict(match_pct):
    """Traffic-light wording from '% of days the district value is close enough to the block'."""
    if match_pct >= 85:
        return "🟢", "very close", GOOD
    if match_pct >= 65:
        return "🟡", "roughly close", OK
    return "🔴", "often different", BAD

# ───────────────────────── MAPS ─────────────────────────
def make_map(district, values, colorscale, zmin, zmax, unit, title, selected=None, hover=None, height=470):
    """values: {block: number}. district=None -> draw all districts."""
    gj = load_geojson()
    feats = [f for f in gj["features"] if district is None or f["properties"]["district"] == district]
    feats = [f for f in feats if f["properties"]["block"] in values]
    geo = {"type": "FeatureCollection", "features": feats}
    blocks = [f["properties"]["block"] for f in feats]
    z = [values[b] for b in blocks]
    text = [(hover or {}).get(b, f"{values[b]:.1f} {unit}") for b in blocks]
    fig = go.Figure(go.Choropleth(
        geojson=geo, locations=blocks, z=z, featureidkey="properties.block", colorscale=colorscale,
        zmin=zmin, zmax=zmax, marker_line_color="white", marker_line_width=2, text=text,
        hovertemplate="<b>%{location}</b><br>%{text}<extra></extra>",
        colorbar=dict(title=unit, thickness=14, len=0.8)))
    if selected in blocks:   # dark outline on chosen block
        fig.add_trace(go.Choropleth(geojson=geo, locations=[selected], z=[0], featureidkey="properties.block",
                                    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
                                    marker_line_color="#111827", marker_line_width=4, hoverinfo="skip"))
    pts = [(f["properties"]["lon"], f["properties"]["lat"], f["properties"]["block"]) for f in feats]
    fig.add_trace(go.Scattergeo(lon=[p[0] for p in pts], lat=[p[1] for p in pts], text=[p[2] for p in pts],
                                mode="text", textfont=dict(size=11, color="#111827"), hoverinfo="skip", showlegend=False))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(title=dict(text=title, x=0.5, font=dict(size=16)), height=height,
                      margin=dict(l=0, r=0, t=45, b=0), paper_bgcolor="rgba(0,0,0,0)", dragmode=False)
    return fig


def clicked_block(event):
    try:
        pts = event.selection.points
        if pts:
            return pts[0].get("location")
    except Exception:
        pass
    return None
