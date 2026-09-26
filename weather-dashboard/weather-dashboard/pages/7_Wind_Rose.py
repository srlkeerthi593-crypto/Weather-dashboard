import streamlit as st
import plotly.express as px
import pandas as pd

from utils.data_loader import load_blockwise, load_districtwise
from utils.style import inject_css, hero, plain_box, glossary_expander

st.set_page_config(page_title="Wind Rose", page_icon="🌬️", layout="wide")
inject_css()
hero("🌬️", "Which Way Does the Wind Blow?", "A compass-style chart showing wind direction and speed, block-level vs district file.", gradient=("#0891B2", "#67E8F9"))
plain_box(
    "Each spoke on the chart is a compass direction. A longer bar means wind blew from that "
    "direction more often. Color shows how strong the wind was."
)
glossary_expander()

block_df = load_blockwise()
dist_df = load_districtwise()
district = st.selectbox("Pick a district", sorted(block_df["district"].unique()))

DIR_BINS = list(range(0, 361, 45))
DIR_LABELS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
SPEED_BINS = [0, 5, 10, 15, 20, 100]
SPEED_LABELS = ["0-5 km/h (calm)", "5-10 km/h", "10-15 km/h", "15-20 km/h", "20+ km/h (strong)"]


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
    st.markdown("#### 📍 All this district's blocks, combined")
    freq_b = make_rose_data(b_sub)
    fig1 = px.bar_polar(freq_b, r="percent", theta="dir_bin", color="speed_bin", color_discrete_sequence=px.colors.sequential.Blues_r)
    fig1.update_layout(height=440, legend_title_text="Wind speed")
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    st.markdown("#### 🏙️ The district file's own record")
    freq_d = make_rose_data(d_sub)
    fig2 = px.bar_polar(freq_d, r="percent", theta="dir_bin", color="speed_bin", color_discrete_sequence=px.colors.sequential.Oranges_r)
    fig2.update_layout(height=440, legend_title_text="Wind speed")
    st.plotly_chart(fig2, use_container_width=True)

plain_box("If the two shapes look different, the district file is smoothing over real wind patterns that vary from block to block.")

st.divider()
st.markdown("### 🔎 Zoom into one specific block")
block = st.selectbox("Pick a block", sorted(b_sub["block"].unique()))
freq_one = make_rose_data(b_sub[b_sub["block"] == block])
fig3 = px.bar_polar(freq_one, r="percent", theta="dir_bin", color="speed_bin", color_discrete_sequence=px.colors.sequential.Blues_r, title=f"{block} ({district})")
fig3.update_layout(height=440, legend_title_text="Wind speed")
st.plotly_chart(fig3, use_container_width=True)
