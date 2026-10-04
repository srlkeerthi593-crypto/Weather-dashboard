"""
Run ONCE on your computer (or whenever the Excel data changes):
    python prepare_data.py
It reads the three yearly Excel files in raw_data/ and writes the two small files the dashboard uses:
    data/daily_merged.csv.gz   -> block-level + district-level forecast, matched day by day
    data/blocks.geojson        -> block (taluka) boundaries of Anand, Kheda, Mahisagar
"""
from pathlib import Path
import urllib.request, json
import pandas as pd

RAW = Path("raw_data"); OUT = Path("data"); OUT.mkdir(exist_ok=True)
YEARS = [2021, 2022, 2023]
VARS = ["Rainfall (mm)", "Tmax (°C)", "Tmin (°C)", "RH-I (%)", "RH-II (%)", "Wind Speed (km/h)"]
SHORT = {"Rainfall (mm)": "rain", "Tmax (°C)": "tmax", "Tmin (°C)": "tmin",
         "RH-I (%)": "rhi", "RH-II (%)": "rhii", "Wind Speed (km/h)": "wind"}

def load(sheet):
    parts = []
    for y in YEARS:
        f = RAW / f"Weather_{y}_365days_Complete_Anand_Kheda_Mahisagar.xlsx"
        d = pd.read_excel(f, sheet_name=sheet); d["Year"] = y; parts.append(d)
    return pd.concat(parts, ignore_index=True)

block, dist = load("blockwise"), load("districtwise")
b = block[["Date", "District", "Block", "Year", "Source"] + VARS].rename(
    columns={**{v: SHORT[v] + "_block" for v in VARS}, "Source": "src_block"})
d = dist[["Date", "District", "Source"] + VARS].rename(
    columns={**{v: SHORT[v] + "_dist" for v in VARS}, "Source": "src_dist"})
df = b.merge(d, on=["Date", "District"], how="left", validate="many_to_one")
assert df.isna().sum().sum() == 0, "unmatched rows"
# 'real' = both sides are genuine forecasts (not gap-filled / interpolated)
df["real"] = (df.src_block == "Forecast") & (df.src_dist == "Forecast")
df = df.drop(columns=["src_block", "src_dist"])
df["Date"] = pd.to_datetime(df["Date"]).dt.date
df.to_csv(OUT / "daily_merged.csv.gz", index=False)
print("daily_merged:", df.shape)

# ---- boundaries (Census-2011 sub-district polygons, public GitHub file) ----
URL = "https://raw.githubusercontent.com/datta07/INDIAN-SHAPEFILES/master/STATES/GUJARAT/GUJARAT_SUBDISTRICTS.geojson"
try:
    import geopandas as gpd
    g = gpd.read_file(URL)
    g = g[g.dtname.str.lower().isin(["anand", "kheda", "mahisagar"])].copy()
    g = g.rename(columns={"sdtname": "Block", "dtname": "District"})[["Block", "District", "geometry"]]
    g["geometry"] = g.geometry.simplify(0.002, preserve_topology=True)
    pts = g.geometry.representative_point()
    g["lon"], g["lat"] = pts.x.round(4), pts.y.round(4)      # where the block name is drawn on the map
    g.to_file(OUT / "blocks.geojson", driver="GeoJSON")
    print("blocks.geojson:", len(g), "polygons")
except Exception as e:
    print("Boundary download skipped:", e)
