import datetime
import pandas as pd
import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise
from utils.metrics import agro_indices
from utils.style import inject_css, hero, plain_box, glossary_expander, BLOCK_COLOR

st.set_page_config(page_title="Farm Advisory", page_icon="🌾", layout="wide")
inject_css()
hero("🌾", "Farm Advisory Numbers", "3 simple, farming-relevant numbers — worked out separately for every local area, not just one number for the whole district.", gradient=("#16A34A", "#4ADE80"))
plain_box(
    "Farmers plan around <b>local</b> weather, not a district-wide average. This page works out simple, "
    "practical numbers <b>for every block</b>, so you can see which areas need different advice than their neighbours."
)
glossary_expander()
st.caption("⚠️ These are simplified, transparent estimates for comparing blocks side by side — not an official government agromet advisory.")

block_df = load_blockwise()
year = st.selectbox("📅 Pick a year", sorted(block_df["year"].unique()))
sub = block_df[block_df["year"] == year]

with st.spinner("Working it out..."):
    idx = agro_indices(sub, ["district", "block"])


def _doy_to_date(doy, yr):
    if pd.isna(doy):
        return "No clear monsoon start found"
    try:
        return (datetime.date(int(yr), 1, 1) + datetime.timedelta(days=int(doy) - 1)).strftime("%d %B")
    except Exception:
        return "No clear monsoon start found"


idx["monsoon_onset_date"] = idx["monsoon_onset_doy"].apply(lambda d: _doy_to_date(d, year))

tab1, tab2, tab3, tab4 = st.tabs([
    "🔥 Days too hot for crops", "🏜️ Longest dry spell", "🌧️ When monsoon arrived", "🌱 Advanced: crop warmth",
])

# ---------------------------------------------------------------------
with tab1:
    st.markdown("#### 🔥 How many days were too hot for crops?")
    plain_box(
        "Many crops start struggling once the daily high crosses <b>35°C</b>. This counts how many such days "
        f"each block had in {year} — the higher the number, the more heat stress that area's crops faced."
    )
    district = st.selectbox("Pick a district", sorted(idx["district"].unique()), key="heat_district")
    d = idx[idx["district"] == district].sort_values("heat_stress_days", ascending=False)
    fig = px.bar(d, x="block", y="heat_stress_days", color_discrete_sequence=[BLOCK_COLOR],
                 labels={"heat_stress_days": "Days over 35°C", "block": ""},
                 title=f"{district} — heat-stress days per block, {year}")
    fig.update_layout(xaxis_tickangle=-30, height=380)
    st.plotly_chart(fig, use_container_width=True)
    worst = d.iloc[0]
    st.info(f"📌 **{worst['block']}** had the most: **{int(worst['heat_stress_days'])} days** over 35°C in {district} this year.")

# ---------------------------------------------------------------------
with tab2:
    st.markdown("#### 🏜️ What was the longest stretch without real rain?")
    plain_box(
        "The longest run of <b>back-to-back days</b> with under 2.5mm of rain — a rough guide to how long "
        "fields went without meaningful rainfall, useful for planning irrigation."
    )
    district2 = st.selectbox("Pick a district", sorted(idx["district"].unique()), key="dry_district")
    d2 = idx[idx["district"] == district2].sort_values("longest_dry_spell_days", ascending=False)
    fig2 = px.bar(d2, x="block", y="longest_dry_spell_days", color_discrete_sequence=["#D97706"],
                  labels={"longest_dry_spell_days": "Longest dry spell (days)", "block": ""},
                  title=f"{district2} — longest dry spell per block, {year}")
    fig2.update_layout(xaxis_tickangle=-30, height=380)
    st.plotly_chart(fig2, use_container_width=True)
    worst2 = d2.iloc[0]
    st.info(f"📌 **{worst2['block']}** went the longest without rain: **{int(worst2['longest_dry_spell_days'])} days in a row** in {district2} this year.")

# ---------------------------------------------------------------------
with tab3:
    st.markdown("#### 🌧️ When did the monsoon actually arrive, block by block?")
    plain_box(
        "The approximate date each block's <b>first proper, sustained wet spell</b> began that year. "
        "If this date is very different across blocks in the same district, a single district-wide "
        "'monsoon has arrived' announcement would be too early for some areas and too late for others."
    )
    show = idx[["district", "block", "monsoon_onset_date"]].rename(
        columns={"district": "District", "block": "Block", "monsoon_onset_date": "Monsoon started around"}
    ).sort_values(["District", "Block"])
    st.dataframe(show, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------
with tab4:
    st.markdown("#### 🌱 Advanced: total warmth crops received (optional, technical)")
    plain_box(
        "This is a more technical number called a <b>growing-degree total</b>: every day, we add up how much "
        "the average temperature was above 10°C, then total it for the whole year. A <b>higher number means "
        "crops accumulated more warmth</b>, which generally speeds up growth — but there's no single "
        "'good' or 'bad' value, so use it only to <b>compare blocks against each other</b>, not as a target."
    )
    district3 = st.selectbox("Pick a district", sorted(idx["district"].unique()), key="gdd_district")
    d3 = idx[idx["district"] == district3].sort_values("gdd_proxy", ascending=False)
    fig3 = px.bar(d3, x="block", y="gdd_proxy", color_discrete_sequence=["#059669"],
                  labels={"gdd_proxy": "Total warmth score", "block": ""},
                  title=f"{district3} — total crop warmth per block, {year}")
    fig3.update_layout(xaxis_tickangle=-30, height=380)
    st.plotly_chart(fig3, use_container_width=True)

st.divider()
st.markdown("### 🚩 Blocks that differ most from their own district")
st.caption("Pick a number above (using the tabs) — this shows which local areas a one-size-fits-all district advisory would be most wrong about.")
metric_choice = st.selectbox(
    "Compare using:",
    ["heat_stress_days", "longest_dry_spell_days", "gdd_proxy"],
    format_func=lambda k: {"heat_stress_days": "🔥 Heat-stress days", "longest_dry_spell_days": "🏜️ Longest dry spell", "gdd_proxy": "🌱 Crop warmth"}[k],
)
district_avg = idx.groupby("district")[metric_choice].transform("mean")
idx["gap_vs_district_avg"] = idx[metric_choice] - district_avg
worst = idx.reindex(idx["gap_vs_district_avg"].abs().sort_values(ascending=False).index).head(5)
st.dataframe(
    worst[["district", "block", metric_choice, "gap_vs_district_avg"]].rename(
        columns={"district": "District", "block": "Block", metric_choice: "This block's value", "gap_vs_district_avg": "Gap vs. its own district's average"}
    ),
    use_container_width=True, hide_index=True,
)
plain_box("A local officer using only the district-wide number would give the wrong advice to these 5 blocks — worth a closer look before sending out generic advice.")
