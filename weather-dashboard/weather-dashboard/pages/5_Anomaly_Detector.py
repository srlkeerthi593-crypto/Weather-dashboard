import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise, VARIABLES
from utils.metrics import detect_anomalies
from utils.style import inject_css, hero, plain_box, glossary_expander, SIMPLE_NAMES

st.set_page_config(page_title="Anomaly Detector", page_icon="🚨", layout="wide")
inject_css()
hero("🚨", "Data Quality Check", "Automatically finds readings that look suspicious rather than truly weather-related.", gradient=("#B91C1C", "#EF4444"))

col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.markdown("#### ❄️ Frozen values")
        st.write("The exact same reading repeated for several days — often means a value was copied forward instead of measured.")
with col2:
    with st.container(border=True):
        st.markdown("#### ⚡ Sudden jumps")
        st.write("A day-to-day change way bigger than normal for that area — could be a typo or sensor glitch.")
with col3:
    with st.container(border=True):
        st.markdown("#### 🌧️ Rain with no clouds")
        st.write("Rain recorded on a day with zero cloud cover — physically doesn't make sense.")

glossary_expander()

block_df = load_blockwise()
var = st.selectbox("Check this variable for frozen values / jumps", list(VARIABLES.keys()), format_func=lambda k: SIMPLE_NAMES[k])
c1, c2 = st.columns(2)
freeze_run = c1.slider("🥶 Flag as 'frozen' after this many identical days in a row", 3, 10, 4)
jump_z = c2.slider("⚡ Flag jumps this unusual (higher = stricter)", 2.0, 6.0, 4.0, step=0.5)

with st.spinner("Scanning..."):
    anomalies = detect_anomalies(block_df, var, freeze_run=freeze_run, jump_zscore=jump_z)

if anomalies.empty:
    st.success("✅ No anomalies found with the current settings.")
else:
    counts = anomalies["type"].value_counts()
    c1, c2, c3 = st.columns(3)
    c1.metric("❄️ Frozen-value flags", int(counts.get("frozen_value", 0)))
    c2.metric("⚡ Sudden-jump flags", int(counts.get("sudden_jump", 0)))
    c3.metric("🌧️ Rain-no-cloud flags", int(counts.get("rain_no_cloud", 0)))

    tab1, tab2 = st.tabs(["📅 When do they happen?", "📍 Which blocks?"])
    with tab1:
        fig = px.histogram(anomalies, x="date", color="type", nbins=52, title="Flagged records over time")
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        by_block = anomalies.groupby(["district", "block", "type"]).size().reset_index(name="count")
        fig2 = px.bar(by_block, x="block", y="count", color="type", title="Flags per block")
        fig2.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 📋 Every flagged record")
    type_filter = st.multiselect("Filter by type", anomalies["type"].unique(), default=list(anomalies["type"].unique()))
    st.dataframe(anomalies[anomalies["type"].isin(type_filter)], use_container_width=True, hide_index=True)
    plain_box("A flag here doesn't automatically mean the data is wrong — it's a 'worth double-checking' signal, not a verdict.")
