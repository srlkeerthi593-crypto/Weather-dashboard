import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise, load_districtwise
from utils.metrics import extreme_event_counts, event_spells
from utils.style import inject_css, hero, plain_box, glossary_expander, BLOCK_COLOR, DISTRICT_COLOR

st.set_page_config(page_title="Extreme Events", page_icon="🌡️", layout="wide")
inject_css()
hero("🌡️", "Extreme Weather Days", "Heatwaves, heavy rain and cold nights — counted block by block, with the exact dates, then checked against the district file.", gradient=("#DC2626", "#F87171"))
plain_box(
    "Averages can look totally normal even when a place quietly had a dangerous heatwave. "
    "This page counts the actual extreme days in each block — and lets you see the exact dates — "
    "so nothing gets hidden by averaging."
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
b_sub = block_df[block_df["year"].isin(years)].copy()
d_sub = dist_df[dist_df["year"].isin(years)].copy()

b_sub["is_heatwave"] = b_sub["tmax"] >= hw
b_sub["is_heavy_rain"] = b_sub["rainfall"] >= hr
b_sub["is_cold_night"] = b_sub["tmin"] <= cn

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
    ("heatwave_days", "district_heatwave_days", "heatwave days", "is_heatwave", f"max temp ≥ {hw}°C"),
    ("heavy_rain_days", "district_heavy_rain_days", "heavy rain days", "is_heavy_rain", f"rainfall ≥ {hr}mm"),
    ("cold_nights", "district_cold_nights", "cold nights", "is_cold_night", f"min temp ≤ {cn}°C"),
]
for tab, (metric, dist_metric, label, cond_col, rule_text) in zip(tabs, configs):
    with tab:
        st.caption(f"Counting days where **{rule_text}**.")

        st.markdown(f"#### 1️⃣ Pick a district to see its own blocks — {label}")
        pick_district = st.selectbox("District", sorted(merged["district"].unique()), key=f"dist_{metric}")
        d_merged = merged[merged["district"] == pick_district].sort_values(metric, ascending=False)

        col1, col2 = st.columns([1.4, 1])
        with col1:
            fig = px.bar(
                d_merged, x="block", y=metric,
                color_discrete_sequence=[BLOCK_COLOR],
                title=f"📍 {pick_district}'s blocks — number of {label}",
                labels={metric: f"Number of {label}", "block": ""},
            )
            fig.update_layout(xaxis_tickangle=-30, height=380)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            dist_val = int(d_merged[dist_metric].iloc[0]) if len(d_merged) else 0
            st.markdown("#### 🏙️ What the district file alone says")
            st.metric(f"{pick_district} district total", f"{dist_val} {label}")
            block_max = d_merged[metric].max() if len(d_merged) else 0
            if block_max > dist_val:
                worst = d_merged.iloc[0]
                st.error(
                    f"⚠️ **{worst['block']}** actually had **{int(worst[metric])}** {label} — "
                    f"more than the district total of **{dist_val}**. The district file alone under-counts this."
                )
            else:
                st.success("All this district's blocks are in line with the district file here.")

        st.markdown(f"#### 2️⃣ See the exact dates for one block")
        pick_block = st.selectbox("Block", sorted(d_merged["block"].unique()), key=f"block_{metric}")
        one_block = b_sub[(b_sub["district"] == pick_district) & (b_sub["block"] == pick_block)]
        spells = event_spells(one_block, cond_col)
        if spells.empty:
            st.info(f"Good news — {pick_block} had zero {label} in the years you selected.")
        else:
            spells_display = spells.copy()
            spells_display["Dates"] = spells_display.apply(
                lambda r: r["start_date"].strftime("%d %b %Y") if r["start_date"] == r["end_date"]
                else f"{r['start_date'].strftime('%d %b %Y')} → {r['end_date'].strftime('%d %b %Y')}",
                axis=1,
            )
            spells_display = spells_display.rename(columns={"days": "How many days in a row"})
            st.dataframe(spells_display[["Dates", "How many days in a row"]], use_container_width=True, hide_index=True)
            plain_box(f"{pick_block} had <b>{len(spells)}</b> separate spells of {label} — each row above is one unbroken stretch, with its exact start and end date.")

        with st.expander("📋 Full table — every block in every district"):
            st.dataframe(
                merged[["district", "block", metric, dist_metric]]
                .sort_values(metric, ascending=False)
                .rename(columns={"district": "District", "block": "Block", metric: f"Block's {label}", dist_metric: f"District file's {label}"}),
                use_container_width=True, hide_index=True,
            )
