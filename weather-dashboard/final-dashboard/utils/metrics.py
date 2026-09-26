"""
metrics.py
----------
Reusable calculations used across dashboard pages:
  - accuracy metrics (RMSE, correlation, bias)
  - extreme-event counts
  - agro-advisory indices
  - anomaly flags
All functions take/return plain pandas objects so they're easy to test
outside Streamlit too.
"""

import numpy as np
import pandas as pd


# ----------------------------------------------------------------------
# 1. Basic accuracy metrics (block value vs. district value for same day)
# ----------------------------------------------------------------------
def accuracy_metrics(observed: pd.Series, predicted: pd.Series) -> dict:
    """RMSE, correlation and mean bias between two aligned series."""
    obs = pd.to_numeric(observed, errors="coerce")
    pred = pd.to_numeric(predicted, errors="coerce")
    mask = obs.notna() & pred.notna()
    obs, pred = obs[mask], pred[mask]
    if len(obs) < 2:
        return {"RMSE": np.nan, "Correlation": np.nan, "Mean_Bias": np.nan, "N": len(obs)}
    rmse = float(np.sqrt(np.mean((obs - pred) ** 2)))
    corr = float(obs.corr(pred))
    bias = float((obs - pred).mean())
    return {"RMSE": round(rmse, 3), "Correlation": round(corr, 3), "Mean_Bias": round(bias, 3), "N": len(obs)}


def block_vs_district_by_group(merged_df: pd.DataFrame, var: str, group_cols) -> pd.DataFrame:
    """
    merged_df must have columns var (block) and f"{var}_dist" (district).
    Returns one row of accuracy metrics per group (e.g. per block, or per block+season).
    """
    rows = []
    for keys, g in merged_df.groupby(group_cols):
        m = accuracy_metrics(g[var], g[f"{var}_dist"])
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols if isinstance(group_cols, list) else [group_cols], keys))
        row.update(m)
        rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 2. Spatial hotspots — how far does each block sit from its district avg?
# ----------------------------------------------------------------------
def block_deviation_from_district(block_df: pd.DataFrame, var: str) -> pd.DataFrame:
    """
    For each block, average value minus the average of ALL blocks in its
    district (i.e. the true district mean built from the blocks themselves).
    A large deviation means district-level data would mislead that block.
    """
    district_mean = block_df.groupby(["district", "date"])[var].transform("mean")
    tmp = block_df.copy()
    tmp["_district_daily_mean"] = district_mean
    tmp["_deviation"] = tmp[var] - tmp["_district_daily_mean"]
    out = (
        tmp.groupby(["district", "block"])["_deviation"]
        .mean()
        .reset_index()
        .rename(columns={"_deviation": f"avg_deviation_{var}"})
        .sort_values(f"avg_deviation_{var}")
    )
    return out


# ----------------------------------------------------------------------
# 3. Extreme-event day counts
# ----------------------------------------------------------------------
def extreme_event_counts(df: pd.DataFrame, group_cols, heatwave_thresh=40, heavy_rain_thresh=64.5, cold_night_thresh=10) -> pd.DataFrame:
    """
    Count, per group (e.g. per block or per district), the number of:
      - heatwave days:  tmax >= heatwave_thresh (°C)
      - heavy rain days: rainfall >= heavy_rain_thresh (mm, IMD 'heavy rain' cutoff)
      - cold nights:    tmin <= cold_night_thresh (°C)
    """
    d = df.copy()
    d["is_heatwave"] = d["tmax"] >= heatwave_thresh
    d["is_heavy_rain"] = d["rainfall"] >= heavy_rain_thresh
    d["is_cold_night"] = d["tmin"] <= cold_night_thresh
    out = d.groupby(group_cols)[["is_heatwave", "is_heavy_rain", "is_cold_night"]].sum().reset_index()
    out = out.rename(columns={
        "is_heatwave": "heatwave_days",
        "is_heavy_rain": "heavy_rain_days",
        "is_cold_night": "cold_nights",
    })
    return out


# ----------------------------------------------------------------------
# 4. Agro-advisory indices
# ----------------------------------------------------------------------
def agro_indices(df: pd.DataFrame, group_cols, gdd_base=10) -> pd.DataFrame:
    """
    Per group, compute:
      - heat_stress_days: tmax >= 35°C (commonly used crop heat-stress cutoff)
      - longest_dry_spell: longest run of consecutive days with rainfall < 2.5mm
      - monsoon_onset_doy: first day-of-year where a 3-day rolling rainfall
        total crosses 15mm AND stays wet for the following 2 days (simple
        onset proxy, not the official IMD algorithm)
      - gdd_proxy: sum of max(((tmax+tmin)/2 - gdd_base), 0) across the year
        (growing-degree-day proxy; base temp default 10°C)
    """
    rows = []
    for keys, g in df.sort_values("date").groupby(group_cols):
        g = g.reset_index(drop=True)
        heat_stress_days = int((g["tmax"] >= 35).sum())

        # longest dry spell
        is_dry = (g["rainfall"].fillna(0) < 2.5).astype(int)
        longest_dry = (is_dry * (is_dry.groupby((is_dry != is_dry.shift()).cumsum()).cumcount() + 1)).max()
        longest_dry = int(longest_dry) if pd.notna(longest_dry) else 0

        # monsoon onset (first year only, kept simple: first date in Apr-Jul window)
        onset_doy = np.nan
        window = g[(g["date"].dt.month >= 4) & (g["date"].dt.month <= 7)].reset_index(drop=True)
        if len(window) > 4:
            roll3 = window["rainfall"].fillna(0).rolling(3).sum()
            for i in range(2, len(window) - 2):
                if roll3.iloc[i] >= 15 and window["rainfall"].iloc[i + 1] > 0 and window["rainfall"].iloc[i + 2] > 0:
                    onset_doy = window["date"].iloc[i].dayofyear
                    break

        gdd_proxy = float((((g["tmax"] + g["tmin"]) / 2) - gdd_base).clip(lower=0).sum())

        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols if isinstance(group_cols, list) else [group_cols], keys))
        row.update({
            "heat_stress_days": heat_stress_days,
            "longest_dry_spell_days": longest_dry,
            "monsoon_onset_doy": onset_doy,
            "gdd_proxy": round(gdd_proxy, 1),
        })
        rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 5. Anomaly / data-forensics detector
# ----------------------------------------------------------------------
def detect_anomalies(df: pd.DataFrame, var="tmax", freeze_run=4, jump_zscore=4) -> pd.DataFrame:
    """
    Flags three kinds of suspicious stretches per (district, block):
      - frozen: the SAME value repeated for >= freeze_run consecutive days
      - jump: a day-to-day change more than `jump_zscore` standard
        deviations away from that block's normal day-to-day change
      - rain_no_cloud: rainfall > 1mm recorded on a day with 0 octa cloud cover
    Returns a tidy DataFrame of flagged rows, one per anomaly found.
    """
    flags = []
    group_cols = ["district", "block"] if "block" in df.columns else ["district"]
    for keys, g in df.sort_values("date").groupby(group_cols):
        g = g.reset_index(drop=True)
        keys = keys if isinstance(keys, tuple) else (keys,)
        key_dict = dict(zip(group_cols, keys))

        # frozen values
        same_as_prev = g[var] == g[var].shift()
        run_id = (~same_as_prev).cumsum()
        run_len = same_as_prev.groupby(run_id).cumsum() + 1
        frozen_idx = g.index[run_len >= freeze_run]
        for i in frozen_idx:
            flags.append({**key_dict, "date": g["date"].iloc[i], "type": "frozen_value",
                          "detail": f"{var}={g[var].iloc[i]} repeated {int(run_len.iloc[i])} days running"})

        # sudden jumps
        diff = g[var].diff()
        std = diff.std()
        if std and std > 0:
            z = (diff - diff.mean()) / std
            jump_idx = g.index[z.abs() >= jump_zscore]
            for i in jump_idx:
                flags.append({**key_dict, "date": g["date"].iloc[i], "type": "sudden_jump",
                              "detail": f"{var} changed by {diff.iloc[i]:.1f} in one day (z={z.iloc[i]:.1f})"})

        # rain with no cloud cover
        if "rainfall" in g.columns and "cloud_cover" in g.columns:
            bad = g[(g["rainfall"] > 1) & (g["cloud_cover"] == 0)]
            for i in bad.index:
                flags.append({**key_dict, "date": g["date"].iloc[i], "type": "rain_no_cloud",
                              "detail": f"rainfall={g['rainfall'].iloc[i]}mm but cloud_cover=0"})

    out = pd.DataFrame(flags)
    if not out.empty:
        out = out.sort_values("date").reset_index(drop=True)
    return out


# ----------------------------------------------------------------------
# 6. Feature table for clustering blocks by weather behaviour
# ----------------------------------------------------------------------
def block_feature_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    One row per block: average weather 'fingerprint' used to group blocks
    that behave similarly, regardless of which district they're in.
    """
    agg = df.groupby(["district", "block"]).agg(
        tmax_mean=("tmax", "mean"),
        tmin_mean=("tmin", "mean"),
        rainfall_total=("rainfall", "sum"),
        rh1_mean=("rh1", "mean"),
        rh2_mean=("rh2", "mean"),
        wind_speed_mean=("wind_speed", "mean"),
    ).reset_index()
    # normalise rainfall total to a yearly-equivalent average across the years present
    n_years = df["year"].nunique()
    agg["rainfall_total"] = agg["rainfall_total"] / max(n_years, 1)
    return agg
