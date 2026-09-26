import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise, load_districtwise
from utils.metrics import extreme_event_counts
from utils.style import inject_css, hero, plain_box, glossary_expander, BLOCK_COLOR, DISTRICT_COLOR

st.set_page_config(page_title="Extreme Events", page_icon="🌡️", layout="wide")
inject_css()
hero("🌡️", "Extreme Weather Days", "Heatwaves, heavy rain and cold nights — counted block by block, then checked against the district file.", gradient=("#DC2626", "#F87171"))
plain_box(
    "Averages can look totally normal even when a place quietly had a dangerous heatwave. "
    "This page counts the actual extreme days in each block, so nothing gets hidden by averaging."
)
glossary_expander()

st.markdown("### 🎚️ What counts as 'extreme'? (adjust if you like)")
c1, c2, c3 = st.columns(3)
hw = c1.number_input("🔥 Heatwave: max temp ≥ (°C)", value=40.0, step=0.5)
hr = c2.number_input("🌧️ Heavy rain: rainfall ≥ (mm)", value=64.5, step=0.5)
cn = c3.number_input("🥶 Cold night: min temp ≤ (°C)", value=10.0, step=0.5)

block_df = load_blockwise()
dist_df = load_districtwise()
years = st.multiselect("Years", sorted(block_df["year"].unique()), default=sorted(block_df["year"].unique()))
b_sub = block_df[block_df["year"].isin(years)]
d_sub = dist_df[dist_df["year"].isin(years)]

block_counts = extreme_event_counts(b_sub, ["district", "block"], hw, hr, cn)
dist_counts = extreme_event_counts(d_sub, ["district"], hw, hr, cn).rename(
    columns={"heatwave_days": "district_heatwave_days",
             "heavy_rain_days": "district_heavy_rain_days",
             "cold_nights": "district_cold_nights"}
)
merged = block_counts.merge(dist_counts, on="district", how="left")

st.divider()
tabs = st.tabs(["🔥 Heatwave days", "🌧️ Heavy rain days", "🥶 Cold nights"])
configs = [
    ("heatwave_days", "district_heatwave_days", "heatwave days"),
    ("heavy_rain_days", "district_heavy_rain_days", "heavy rain days"),
    ("cold_nights", "district_cold_nights", "cold nights"),
]
for tab, (metric, dist_metric, label) in zip(tabs, configs):
    with tab:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"#### 📍 Block-by-block count of {label}")
            fig = px.bar(
                merged.sort_values(metric, ascending=False), x="block", y=metric,
                color_discrete_sequence=[BLOCK_COLOR],
                labels={metric: f"Number of {label}", "block": ""},
            )
            fig.update_layout(xaxis_tickangle=-30, height=380)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.markdown(f"#### 🏙️ What the district file alone says")
            dist_only = merged.drop_duplicates("district")
            fig2 = px.bar(
                dist_only, x="district", y=dist_metric,
                color_discrete_sequence=[DISTRICT_COLOR],
                labels={dist_metric: f"Number of {label}", "district": ""},
            )
            fig2.update_layout(height=380)
            st.plotly_chart(fig2, use_container_width=True)

        under = merged[merged[metric] > merged[dist_metric]]
        if len(under):
            worst = under.sort_values(metric, ascending=False).iloc[0]
            plain_box(
                f"<b>{worst['block']}</b> ({worst['district']}) actually had "
                f"<b>{int(worst[metric])}</b> {label}, but the district file only shows "
                f"<b>{int(worst[dist_metric])}</b>. Relying on district data alone would have "
                f"under-counted the risk here.",
                icon="⚠️",
            )
        with st.expander("📋 Full table"):
            st.dataframe(merged[["district", "block", metric, dist_metric]].sort_values(metric, ascending=False), use_container_width=True, hide_index=True)
