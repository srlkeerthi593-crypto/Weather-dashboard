import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise, load_districtwise, merged_block_district, VARIABLES
from utils.metrics import block_vs_district_by_group, accuracy_metrics

st.set_page_config(page_title="Block vs District", page_icon="🔍", layout="wide")
st.title("🔍 Block vs. District Comparison")

st.markdown(
    """
This is the core question: **if you only had district-level data, how wrong
would you be about any given block?**

- **RMSE** — the typical size of the daily error (lower = better).
- **Correlation** — do the block and district move together day to day? (closer to 1 = better).
- **Mean Bias** — is the district value usually higher or lower than the block?
  (Bias = Block − District, so a **negative** bias means the district figure
  **overestimates** that block.)
"""
)

block_df = load_blockwise()
dist_df = load_districtwise()
merged = merged_block_district(block_df, dist_df)

var = st.selectbox("Variable", list(VARIABLES.keys()), format_func=lambda k: VARIABLES[k])
years = st.multiselect("Years", sorted(block_df["year"].unique()), default=sorted(block_df["year"].unique()))
sub = merged[merged["year"].isin(years)]

st.divider()
st.subheader(f"Accuracy of district data as a stand-in for each block — {VARIABLES[var]}")

table = block_vs_district_by_group(sub, var, ["district", "block"]).sort_values("RMSE", ascending=False)
st.dataframe(table, use_container_width=True, hide_index=True)

fig = px.bar(
    table, x="block", y="RMSE", color="district",
    title=f"RMSE by block — {VARIABLES[var]} (higher bar = district data is a worse stand-in)",
)
fig.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)

st.info(
    f"📌 Worst-matched block: **{table.iloc[0]['block']}** ({table.iloc[0]['district']}) "
    f"with RMSE {table.iloc[0]['RMSE']}. Best-matched: **{table.iloc[-1]['block']}** "
    f"with RMSE {table.iloc[-1]['RMSE']}."
)

st.divider()
st.subheader("Zoom into one block: day-by-day comparison")
pick_district = st.selectbox("District", sorted(sub["district"].unique()))
pick_block = st.selectbox("Block", sorted(sub[sub["district"] == pick_district]["block"].unique()))

one = sub[(sub["district"] == pick_district) & (sub["block"] == pick_block)].sort_values("date")
fig2 = px.line(
    one, x="date", y=[var, f"{var}_dist"],
    labels={"value": VARIABLES[var], "date": "Date", "variable": "Source"},
    title=f"{pick_block} ({pick_district}) — Block value vs. District value",
)
newnames = {var: f"{pick_block} (block)", f"{var}_dist": f"{pick_district} (district)"}
fig2.for_each_trace(lambda t: t.update(name=newnames.get(t.name, t.name)))
st.plotly_chart(fig2, use_container_width=True)

m = accuracy_metrics(one[var], one[f"{var}_dist"])
c1, c2, c3 = st.columns(3)
c1.metric("RMSE", m["RMSE"])
c2.metric("Correlation", m["Correlation"])
c3.metric("Mean Bias (Block − District)", m["Mean_Bias"])
