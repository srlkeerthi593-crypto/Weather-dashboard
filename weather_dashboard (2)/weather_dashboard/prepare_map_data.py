"""Pre-computes block-vs-district statistics used by the Map Comparison page.
Observed = 'blockwise' sheet, Forecast = 'districtwise' sheet (same convention as comparision.ipynb).
Run:  python prepare_map_data.py      (reads data/*.xlsx, writes data/block_stats.csv + data/district_stats.csv)"""
import numpy as np, pandas as pd
from pathlib import Path

D = Path(__file__).parent / "data"
YEARS = [2021, 2022, 2023]
PARAMS = {"Rainfall": "Rainfall (mm)", "Tmax": "Tmax (°C)", "Tmin": "Tmin (°C)",
          "RH-I": "RH-I (%)", "RH-II": "RH-II (%)", "Wind": "Wind Speed (km/h)"}

def season(m):
    return "Winter" if m in (12, 1, 2) else "Summer" if m in (3, 4, 5) else "Monsoon" if m in (6, 7, 8, 9) else "Post-monsoon"

blk, dst = [], []
for y in YEARS:
    f = D / f"Weather_{y}_365days_Complete_Anand_Kheda_Mahisagar.xlsx"
    b = pd.read_excel(f, "blockwise"); b["Year"] = y
    d = pd.read_excel(f, "districtwise"); d["Year"] = y
    blk.append(b); dst.append(d)
blk, dst = pd.concat(blk), pd.concat(dst)
df = blk.merge(dst.drop(columns=["Year", "Source"]), on=["Date", "District"], suffixes=("_obs", "_fc"))
df["Season"] = pd.to_datetime(df["Date"]).dt.month.map(season)

SEASONS = ["Winter", "Summer", "Monsoon", "Post-monsoon"]
periods = [(str(y), None) for y in YEARS] + [("All", None)]
rows_b, rows_d = [], []
for yl in ["2021", "2022", "2023", "All"]:
    for sl in ["All"] + SEASONS:
        s = df
        if yl != "All": s = s[s.Year == int(yl)]
        if sl != "All": s = s[s.Season == sl]
        n_years = s.Year.nunique()
        for key, col in PARAMS.items():
            o, f_ = f"{col}_obs", f"{col}_fc"
            for (dist, blkname), g in s.groupby(["District", "Block"]):
                if key == "Rainfall":                       # average yearly total (mm) for the selected period
                    obs, fc = g[o].sum() / n_years, g[f_].sum() / n_years
                else:
                    obs, fc = g[o].mean(), g[f_].mean()
                rows_b.append(dict(Year=yl, Season=sl, Param=key, District=dist, Block=blkname,
                                   Observed=obs, Forecast=fc, Diff=fc - obs,
                                   RMSE=float(np.sqrt(((g[f_] - g[o]) ** 2).mean())),
                                   Corr=g[o].corr(g[f_]) if g[o].std() > 0 and g[f_].std() > 0 else np.nan))
bs = pd.DataFrame(rows_b)
# district table: forecast (districtwise) and mean of its blocks' observed values
ds = (bs.groupby(["Year", "Season", "Param", "District"])
        .agg(Forecast=("Forecast", "first"), Observed_blockmean=("Observed", "mean"),
             n_blocks=("Block", "nunique")).reset_index())
ds["Diff"] = ds["Forecast"] - ds["Observed_blockmean"]
# monthly table (for the "how values vary" chart)
df["Month"] = pd.to_datetime(df["Date"]).dt.month
rows_m = []
for key, col in PARAMS.items():
    agg = "sum" if key == "Rainfall" else "mean"
    m = df.groupby(["Year", "Month", "District", "Block"]).agg(Observed=(f"{col}_obs", agg), Forecast=(f"{col}_fc", agg)).reset_index()
    m.insert(0, "Param", key); rows_m.append(m)
pd.concat(rows_m).round(3).to_csv(D / "monthly_stats.csv", index=False)
bs.round(4).to_csv(D / "block_stats.csv", index=False)
ds.round(4).to_csv(D / "district_stats.csv", index=False)
print(bs.shape, ds.shape)
