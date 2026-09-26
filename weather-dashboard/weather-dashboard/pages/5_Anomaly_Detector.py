import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise, VARIABLES
from utils.metrics import detect_anomalies

st.set_page_config(page_title="Anomaly Detector", page_icon="🚨", layout="wide")
st.title("🚨 Anomaly & Data-Forensics Detector")

st.markdown(
    """
Automatically scans the data for stretches that look **suspicious rather
than genuinely weather-related**:

- ❄️ **Frozen values** — the same reading repeated for several days in a row
  (often a sign a sensor/forecast value was copy-forwarded, not measured)
- ⚡ **Sudden jumps** — a day-to-day change far outside that block's normal
  pattern (possible data entry error)
- 🌧️ **Rain with no clouds** — rainfall recorded on a day with 0 octa cloud
  cover, which is physically inconsistent
"""
)

block_df = load_blockwise()
var = st.selectbox(
    "Variable to check for frozen values / jumps",
    list(VARIABLES.keys()),
    format_func=lambda k: VARIABLES[k],
)
c1, c2 = st.columns(2)
freeze_run = c1.slider("Flag as 'frozen' after this many identical days in a row", 3, 10, 4)
jump_z = c2.slider("Flag jumps beyond this many standard deviations", 2.0, 6.0, 4.0, step=0.5)

with st.spinner("Scanning..."):
    anomalies = detect_anomalies(block_df, var, freeze_run=freeze_run, jump_zscore=jump_z)

if anomalies.empty:
    st.success("No anomalies found with the current settings.")
else:
    c1, c2, c3 = st.columns(3)
    counts = anomalies["type"].value_counts()
    c1.metric("❄️ Frozen-value flags", int(counts.get("frozen_value", 0)))
    c2.metric("⚡ Sudden-jump flags", int(counts.get("sudden_jump", 0)))
    c3.metric("🌧️ Rain-no-cloud flags", int(counts.get("rain_no_cloud", 0)))

    fig = px.histogram(
        anomalies, x="date", color="type", nbins=52,
        title="Anomalies over time, by type",
    )
    st.plotly_chart(fig, use_container_width=True)

    by_block = anomalies.groupby(["district", "block", "type"]).size().reset_index(name="count")
    fig2 = px.bar(
        by_block, x="block", y="count", color="type",
        title="Which blocks have the most flagged records?",
    )
    fig2.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Flagged records")
    type_filter = st.multiselect("Filter by type", anomalies["type"].unique(), default=list(anomalies["type"].unique()))
    st.dataframe(
        anomalies[anomalies["type"].isin(type_filter)],
        use_container_width=True, hide_index=True,
    )
    st.caption(
        "This does not automatically mean data is wrong — it flags patterns worth "
        "a human double-check (e.g. forecast values carried over on missing-data days)."
    )
