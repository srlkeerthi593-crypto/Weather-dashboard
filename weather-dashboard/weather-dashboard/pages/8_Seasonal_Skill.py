import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise, load_districtwise, merged_block_district, VARIABLES
from utils.metrics import block_vs_district_by_group
from utils.style import inject_css, hero, plain_box, glossary_expander, SIMPLE_NAMES

st.set_page_config(page_title="Seasonal Skill Decay", page_icon="📈", layout="wide")
inject_css()
hero("📈", "Does the Season Matter?", "Checking whether district data becomes a worse stand-in during the monsoon.", gradient=("#4338CA", "#818CF8"))
plain_box(
    "Rain is much more unpredictable from place to place than temperature is. This page checks: "
    "<b>does the gap between block and district data grow in the monsoon, and shrink in winter?</b>"
)
glossary_expander()
st.caption("Seasons: ❄️ Winter (Dec–Feb) · 🌤️ Pre-monsoon (Mar–May) · 🌧️ Monsoon (Jun–Sep) · 🍂 Post-monsoon (Oct–Nov)")

block_df = load_blockwise()
dist_df = load_districtwise()
merged = merged_block_district(block_df, dist_df)

var = st.selectbox("Weather variable", list(VARIABLES.keys()), format_func=lambda k: SIMPLE_NAMES[k])
season_order = ["Winter", "Pre-monsoon", "Monsoon", "Post-monsoon"]
table = block_vs_district_by_group(merged, var, ["season", "year"])
table["season"] = table["season"].astype("category").cat.set_categories(season_order, ordered=True)
table = table.sort_values(["year", "season"])
table["year"] = table["year"].astype(str)

col1, col2 = st.columns(2)
with col1:
    fig1 = px.line(table, x="season", y="RMSE", color="year", markers=True, category_orders={"season": season_order},
                    title="Average daily error, by season (higher = bigger gap)")
    fig1.update_layout(height=380)
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    fig2 = px.line(table, x="season", y="Correlation", color="year", markers=True, category_orders={"season": season_order},
                    title="How closely they move together, by season")
    fig2.update_layout(height=380)
    st.plotly_chart(fig2, use_container_width=True)

avg_by_season = table.groupby("season", observed=True)["RMSE"].mean()
worst_season = avg_by_season.idxmax()
best_season = avg_by_season.idxmin()
plain_box(
    f"Averaged across all years, <b>{worst_season}</b> is when district data is <b>least reliable</b> "
    f"for predicting a block's real weather. <b>{best_season}</b> is when it's <b>most reliable</b>.",
    icon="📌",
)

with st.expander("📋 Full numbers table"):
    st.dataframe(table, use_container_width=True, hide_index=True)

st.divider()
st.markdown("### 🏙️ Break it down by district")
by_district_season = block_vs_district_by_group(merged, var, ["district", "season"])
by_district_season["season"] = by_district_season["season"].astype("category").cat.set_categories(season_order, ordered=True)
by_district_season = by_district_season.sort_values(["district", "season"])
fig3 = px.bar(by_district_season, x="season", y="RMSE", color="district", barmode="group",
              category_orders={"season": season_order}, title="Seasonal error, by district")
fig3.update_layout(height=380)
st.plotly_chart(fig3, use_container_width=True)
