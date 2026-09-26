import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

from utils.data_loader import load_blockwise, load_districtwise

st.set_page_config(page_title="Wind Rose", page_icon="🌬️", layout="wide")
st.title("🌬️ Wind Rose: Block-Aggregated vs. District File")

st.markdown(
    """
A wind rose shows **which direction the wind blows from, and how strong**,
as a compass-shaped chart. Here we compare two versions for each district:

- **Block-aggregated** — all blocks in the district pooled together
- **District file** — the district-level record directly

If the two roses look different, the district file is smoothing over real
directional wind patterns that vary block to block.
"""
)

block_df = load_blockwise()
dist_df = load_districtwise()

district = st.selectbox("District", sorted(block_df["district"].unique()))

DIR_BINS = list(range(0, 361, 45))
DIR_LABELS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
SPEED_BINS = [0, 5, 10, 15, 20, 100]
SPEED_LABELS = ["0-5", "5-10", "10-15", "15-20", "20+"]


def make_rose_data(df):
    d = df.dropna(subset=["wind_dir", "wind_speed"]).copy()
    d["dir_bin"] = pd.cut(d["wind_dir"] % 360, bins=DIR_BINS, labels=DIR_LABELS, right=False, include_lowest=True)
    d["speed_bin"] = pd.cut(d["wind_speed"], bins=SPEED_BINS, labels=SPEED_LABELS, right=False)
    freq = d.groupby(["dir_bin", "speed_bin"], observed=True).size().reset_index(name="count")
    freq["percent"] = 100 * freq["count"] / freq["count"].sum()
    return freq


b_sub = block_df[block_df["district"] == district]
d_sub = dist_df[dist_df["district"] == district]

col1, col2 = st.columns(2)
with col1:
    st.subheader("Block-aggregated")
    freq_b = make_rose_data(b_sub)
    fig1 = px.bar_polar(
        freq_b, r="percent", theta="dir_bin", color="speed_bin",
        color_discrete_sequence=px.colors.sequential.Plasma_r,
        title=f"{district} — all blocks pooled",
    )
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    st.subheader("District file")
    freq_d = make_rose_data(d_sub)
    fig2 = px.bar_polar(
        freq_d, r="percent", theta="dir_bin", color="speed_bin",
        color_discrete_sequence=px.colors.sequential.Plasma_r,
        title=f"{district} — district-level record",
    )
    st.plotly_chart(fig2, use_container_width=True)

st.caption(
    "Each spoke is a compass direction the wind blows **from**. Bar length = how "
    "often wind came from that direction; color = speed band (km/h)."
)

st.divider()
st.subheader("Per-block wind rose")
block = st.selectbox("Pick one block to inspect", sorted(b_sub["block"].unique()))
freq_one = make_rose_data(b_sub[b_sub["block"] == block])
fig3 = px.bar_polar(
    freq_one, r="percent", theta="dir_bin", color="speed_bin",
    color_discrete_sequence=px.colors.sequential.Plasma_r,
    title=f"{block} ({district})",
)
st.plotly_chart(fig3, use_container_width=True)
