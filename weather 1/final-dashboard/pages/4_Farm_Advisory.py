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

with st.expander("❓ This data is from the past (2021–2023) — how does that help with the FUTURE?", expanded=False):
    st.markdown(
        "Good question, and worth being upfront about: **this page cannot predict next season's weather.** "
        "What it *can* do is tell you what's **typical** for each block, based on 3 real years of data — a "
        "baseline you can actually trust, instead of a guess.\n\n"
        "**How to actually use it for planning ahead:**\n"
        "- Pick **'Typical (3-year average)'** below — it smooths out one unusually good or bad year, "
        "giving a steadier sense of what to normally expect in that block.\n"
        "- Use it to answer *'how much heat stress does this block usually see?'* or *'roughly when does the "
        "monsoon usually reach this block?'* — useful for planning sowing dates, irrigation budgets, and crop choice.\n"
        "- For the **specific upcoming season**, combine this baseline with an actual seasonal/monsoon forecast "
        "(e.g. from IMD — the India Meteorological Department) — this dashboard only shows you the past, "
        "a forecast tells you how this particular year is expected to differ from that past pattern."
    )

block_df = load_blockwise()
year_options = ["Typical (3-year average)"] + sorted(block_df["year"].unique())
year = st.selectbox("📅 Pick a year (or the 3-year typical baseline)", year_options)

with st.spinner("Working it out..."):
    if year == "Typical (3-year average)":
        yearly = []
        for yr in sorted(block_df["year"].unique()):
            t = agro_indices(block_df[block_df["year"] == yr], ["district", "block"])
            t["year"] = yr
            yearly.append(t)
        allyears = pd.concat(yearly, ignore_index=True)
        idx = allyears.groupby(["district", "block"], as_index=False).agg(
            heat_stress_days=("heat_stress_days", "mean"),
            longest_dry_spell_days=("longest_dry_spell_days", "mean"),
            monsoon_onset_doy=("monsoon_onset_doy", "mean"),
            gdd_proxy=("gdd_proxy", "mean"),
        )
        display_year = 2022  # any non-leap reference year, just for turning the average day-of-year into a date
    else:
        sub = block_df[block_df["year"] == year]
        idx = agro_indices(sub, ["district", "block"])
        display_year = year


def _doy_to_date(doy, yr):
    if pd.isna(doy):
        return "No clear monsoon start found"
    try:
        return (datetime.date(int(yr), 1, 1) + datetime.timedelta(days=int(doy) - 1)).strftime("%d %B")
    except Exception:
        return "No clear monsoon start found"


idx["monsoon_onset_date"] = idx["monsoon_onset_doy"].apply(lambda d: _doy_to_date(d, display_year))
year_label = "a typical year (2021–2023 average)" if year == "Typical (3-year average)" else str(year)

tab1, tab2, tab3, tab4 = st.tabs([
    "🔥 Days too hot for crops", "🏜️ Longest dry spell", "🌧️ When monsoon arrived", "🌱 Advanced: crop warmth",
])

# ---------------------------------------------------------------------
with tab1:
    st.markdown("#### 🔥 How many days were too hot for crops?")
    plain_box(
        "Many crops start struggling once the daily high crosses <b>35°C</b>. This counts how many such days "
        f"each block had in {year_label} — the higher the number, the more heat stress that area's crops faced. "
        "The chart starts a little above zero (not at zero) so the real differences between blocks are actually visible — "
        "the exact number is printed on every bar too."
    )
    district = st.selectbox("Pick a district", sorted(idx["district"].unique()), key="heat_district")
    d = idx[idx["district"] == district].sort_values("heat_stress_days", ascending=False)
    y_lo = max(0, d["heat_stress_days"].min() - 15)
    fig = px.bar(d, x="block", y="heat_stress_days", color_discrete_sequence=[BLOCK_COLOR],
                 text=d["heat_stress_days"].round(0).astype(int),
                 labels={"heat_stress_days": "Days over 35°C", "block": ""},
                 title=f"{district} — heat-stress days per block, {year_label}")
    fig.update_traces(textposition="outside")
    fig.update_layout(xaxis_tickangle=-30, height=420, yaxis_range=[y_lo, d["heat_stress_days"].max() * 1.12])
    st.plotly_chart(fig, use_container_width=True)
    worst = d.iloc[0]
    st.info(f"📌 **{worst['block']}** had the most: **{int(worst['heat_stress_days'])} days** over 35°C in {district} for {year_label}.")

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
                  text=d2["longest_dry_spell_days"].round(0).astype(int),
                  labels={"longest_dry_spell_days": "Longest dry spell (days)", "block": ""},
                  title=f"{district2} — longest dry spell per block, {year_label}")
    fig2.update_traces(textposition="outside")
    fig2.update_layout(xaxis_tickangle=-30, height=420, yaxis_range=[0, d2["longest_dry_spell_days"].max() * 1.15])
    st.plotly_chart(fig2, use_container_width=True)
    worst2 = d2.iloc[0]
    st.info(f"📌 **{worst2['block']}** went the longest without rain: **{int(worst2['longest_dry_spell_days'])} days in a row** in {district2} for {year_label}.")

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
                  text=d3["gdd_proxy"].round(0).astype(int),
                  labels={"gdd_proxy": "Total warmth score", "block": ""},
                  title=f"{district3} — total crop warmth per block, {year_label}")
    fig3.update_traces(textposition="outside")
    fig3.update_layout(xaxis_tickangle=-30, height=420, yaxis_range=[d3["gdd_proxy"].min() * 0.9, d3["gdd_proxy"].max() * 1.1])
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
