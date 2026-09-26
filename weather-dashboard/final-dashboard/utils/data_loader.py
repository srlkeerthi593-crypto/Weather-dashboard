"""
data_loader.py
---------------
Everything to do with reading the raw Excel files and turning them into
clean, analysis-ready pandas DataFrames.

Why this file exists on its own:
  - Keeps the messy "read Excel, rename columns, add Year/Season" logic
    in ONE place instead of copy-pasted on every dashboard page.
  - Every page just calls load_blockwise() / load_districtwise() and
    gets back a tidy DataFrame.
"""

import glob
import os
import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------
# Where the raw yearly Excel files live. Put your 3 files in /data
# (any filename containing "20XX" works, the loader finds them itself).
# ----------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# Rename the long human-readable Excel column names to short, code-friendly ones.
BLOCKWISE_RENAME = {
    "Date": "date",
    "District": "district",
    "Block": "block",
    "Rainfall (mm)": "rainfall",
    "Tmax (°C)": "tmax",
    "Tmin (°C)": "tmin",
    "RH-I (%)": "rh1",
    "RH-II (%)": "rh2",
    "Wind Speed (km/h)": "wind_speed",
    "Wind Direction (°)": "wind_dir",
    "Cloud Cover (octa)": "cloud_cover",
    "Source": "source",
}

DISTRICTWISE_RENAME = {
    "Date": "date",
    "District": "district",
    "Rainfall (mm)": "rainfall",
    "Tmax (°C)": "tmax",
    "Tmin (°C)": "tmin",
    "RH-I (%)": "rh1",
    "RH-II (%)": "rh2",
    "Wind Speed (km/h)": "wind_speed",
    "Wind Direction (°)": "wind_dir",
    "Cloud Cover (octa)": "cloud_cover",
    "Source": "source",
}

NUMERIC_COLS = ["rainfall", "tmax", "tmin", "rh1", "rh2", "wind_speed", "wind_dir", "cloud_cover"]


def _find_year_files():
    """Find every yearly weather Excel file sitting in /data, whatever it's named."""
    files = glob.glob(os.path.join(DATA_DIR, "*.xlsx"))
    files = [f for f in files if "result" not in os.path.basename(f).lower()]
    if not files:
        raise FileNotFoundError(
            f"No .xlsx weather files found in {DATA_DIR}. "
            "Copy your 3 yearly files (2021, 2022, 2023) into the /data folder."
        )
    return sorted(files)


def add_season(df: pd.DataFrame) -> pd.DataFrame:
    """Add an India-met-department style Season column based on the month."""
    month = df["date"].dt.month
    season = pd.Series("Winter", index=df.index)
    season[month.isin([3, 4, 5])] = "Pre-monsoon"
    season[month.isin([6, 7, 8, 9])] = "Monsoon"
    season[month.isin([10, 11])] = "Post-monsoon"
    # Dec, Jan, Feb stay "Winter" (default)
    df["season"] = season
    return df


def _load_sheet(files, sheet_name, rename_map):
    frames = []
    for f in files:
        df = pd.read_excel(f, sheet_name=sheet_name)
        df = df.rename(columns=rename_map)
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"])
    out["year"] = out["date"].dt.year
    for c in NUMERIC_COLS:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    out = add_season(out)
    return out.sort_values(["district", "block", "date"] if "block" in out.columns else ["district", "date"]).reset_index(drop=True)


@st.cache_data(show_spinner="Loading block-level weather data...")
def load_blockwise() -> pd.DataFrame:
    """All 3 years of block-level daily weather data, tidied up."""
    files = _find_year_files()
    return _load_sheet(files, "blockwise", BLOCKWISE_RENAME)


@st.cache_data(show_spinner="Loading district-level weather data...")
def load_districtwise() -> pd.DataFrame:
    """All 3 years of district-level daily weather data, tidied up."""
    files = _find_year_files()
    return _load_sheet(files, "districtwise", DISTRICTWISE_RENAME)


def merged_block_district(block_df: pd.DataFrame, dist_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join block rows to their matching district row on (date, district),
    so every block-day sits next to the district-level value for the same day.
    District columns get a '_dist' suffix so nothing clashes.
    """
    dist_small = dist_df[["date", "district"] + NUMERIC_COLS].copy()
    dist_small = dist_small.rename(columns={c: f"{c}_dist" for c in NUMERIC_COLS})
    merged = block_df.merge(dist_small, on=["date", "district"], how="left")
    return merged


VARIABLES = {
    "tmax": "Max Temperature (°C)",
    "tmin": "Min Temperature (°C)",
    "rainfall": "Rainfall (mm)",
    "rh1": "Relative Humidity - I (%)",
    "rh2": "Relative Humidity - II (%)",
    "wind_speed": "Wind Speed (km/h)",
}
