"""Home page.  Run:  streamlit run app.py"""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import LABELS, YEARS, scorecard
from utils.style import (inject_css, hero, step, tip, kpi, plot, need_data, DIST_COLOR, VAR_ICON)

st.set_page_config(page_title="Block vs District Weather", page_icon="🌦️", layout="wide")
inject_css()
df = need_data()

hero("🌦️", "Block vs District Weather",
     "Is the weather number for a whole <b>district</b> good enough for a small local <b>block</b>? "
     "Anand · Kheda · Mahisagar, 2021–2023.")
tip("<b>In one line:</b> a <b>district</b> value is one number for a big area. A <b>block</b> is a small local area inside it. "
    "We use the block as the closer-to-ground <i>reference</i> and check how well the district number matches it.")

c1, c2, c3, c4 = st.columns(4)
kpi(c1, "Years", f"{min(YEARS)}–{max(YEARS)}", "#7C3AED")
kpi(c2, "Districts", df["District"].nunique(), "#2563EB")
kpi(c3, "Blocks", df["Block"].nunique(), "#06B6D4")
kpi(c4, "Daily records", f"{len(df):,}", "#F97316")

step("🧭 Where to go (use the left sidebar)")
cards = [("🗺️", "Block vs District", "Pick a district, click a block on the map, compare.", "pages/1_Block_vs_District.py", "#7C3AED"),
         ("🏆", "Which is reliable?", "Simple traffic-light scorecard.", "pages/2_Which_is_Reliable.py", "#2563EB"),
         ("🔥", "Spatial Hotspots", "Blocks that run hotter, wetter, windier.", "pages/3_Spatial_Hotspots.py", "#F97316"),
         ("🖼️", "Result Charts", "Your published graphs.", "pages/4_Result_Charts.py", "#10B981"),
         ("🛠️", "Fixing the gap", "Simple bias correction.", "pages/5_Bias_Correction.py", "#EC4899")]
for col, (e, t, d, target, color) in zip(st.columns(5), cards):
    with col:
        st.markdown(f'<div class="card" style="background:{color}"><h3>{e}</h3><b>{t}</b><br>'
                    f'<span style="font-size:.88rem">{d}</span></div>', unsafe_allow_html=True)
        try:
            st.page_link(target, label="Open →")
        except Exception:
            pass
