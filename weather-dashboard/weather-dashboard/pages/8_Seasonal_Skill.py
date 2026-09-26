import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise, load_districtwise, merged_block_district, VARIABLES
from utils.metrics import block_vs_district_by_group

st.set_page_config(page_title="Seasonal Skill Decay", page_icon="📈", layout="wide")
st.title("📈 Does Block-vs-District Disagreement Change by Season?")

st.markdown(
    """
Weather is harder to generalize across a district during some seasons than
others. This page checks: **does the block-vs-district gap grow in the
monsoon and shrink in winter** (a common pattern, since rainfall is much
more locally variable than temperature)?

Seasons follow the standard India Met Department grouping:
Winter (Dec–Feb) · Pre-monsoon (Mar–May) · Monsoon (Jun–Sep) · Post-monsoon (Oct–Nov)
"""
)

block_df = load_blockwise()
dist_df = load_districtwise()
merged = merged_block_district(block_df, dist_df)

var = st.selectbox("Variable", list(VARIABLES.keys()), format_func=lambda k: VARIABLES[k])

season_order = ["Winter", "Pre-monsoon", "Monsoon", "Post-monsoon"]
table = block_vs_district_by_group(merged, var, ["season", "year"])
table["season"] = table["season"].astype("category").cat.set_categories(season_order, ordered=True)
table = table.sort_values(["year", "season"])

col1, col2 = st.columns(2)
with col1:
    fig1 = px.line(
        table, x="season", y="RMSE", color="year", markers=True,
        category_orders={"season": season_order},
        title=f"RMSE by season — {VARIABLES[var]}",
    )
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    fig2 = px.line(
        table, x="season", y="Correlation", color="year", markers=True,
        category_orders={"season": season_order},
        title=f"Correlation by season — {VARIABLES[var]}",
    )
    st.plotly_chart(fig2, use_container_width=True)

st.dataframe(table, use_container_width=True, hide_index=True)

avg_by_season = table.groupby("season", observed=True)["RMSE"].mean()
worst_season = avg_by_season.idxmax()
best_season = avg_by_season.idxmin()
st.info(
    f"📌 Averaged across years, **{worst_season}** has the highest RMSE "
    f"({avg_by_season[worst_season]:.2f}) — district data is least reliable "
    f"for blocks in this season. **{best_season}** is the most reliable "
    f"({avg_by_season[best_season]:.2f})."
)

st.divider()
st.subheader("Break it down by district too")
by_district_season = block_vs_district_by_group(merged, var, ["district", "season"])
by_district_season["season"] = by_district_season["season"].astype("category").cat.set_categories(season_order, ordered=True)
by_district_season = by_district_season.sort_values(["district", "season"])
fig3 = px.bar(
    by_district_season, x="season", y="RMSE", color="district", barmode="group",
    category_orders={"season": season_order},
    title=f"RMSE by season and district — {VARIABLES[var]}",
)
st.plotly_chart(fig3, use_container_width=True)
