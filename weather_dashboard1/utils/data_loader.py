"""Data loading, merging and verification metrics (block = reference, district = forecast)."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
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
