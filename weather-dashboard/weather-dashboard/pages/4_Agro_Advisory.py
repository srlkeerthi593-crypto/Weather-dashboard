import streamlit as st
import plotly.express as px

from utils.data_loader import load_blockwise
from utils.metrics import agro_indices

st.set_page_config(page_title="Agro-Advisory Indices", page_icon="🌾", layout="wide")
st.title("🌾 Agro-Advisory Indices, Block by Block")

st.markdown(
    """
These are simplified versions of the indices agriculture departments use to
issue farming advisories. Computing them **per block** (instead of per
district) shows where a district-wide advisory would give farmers the
wrong signal.

- **Heat-stress days** — days with max temp ≥ 35°C (crop heat-stress cutoff)
- **Longest dry spell** — longest run of consecutive days with < 2.5mm rain
- **Monsoon onset (day of year)** — first sustained wet spell in Apr–Jul
  (simple 3-day-rainfall-total proxy, *not* the official IMD method)
- **GDD proxy** — growing-degree-days, sum of `max(avg_temp − 10°C, 0)` for the year

⚠️ *These are educational approximations for comparing blocks against each
other — not a substitute for official agromet advisories.*
"""
)

block_df = load_blockwise()
year = st.selectbox("Year", sorted(block_df["year"].unique()))
sub = block_df[block_df["year"] == year]

with st.spinner("Computing indices..."):
    idx = agro_indices(sub, ["district", "block"])

metric = st.selectbox(
    "Show me",
    ["heat_stress_days", "longest_dry_spell_days", "monsoon_onset_doy", "gdd_proxy"],
    format_func=lambda x: {
        "heat_stress_days": "🔥 Heat-stress days",
        "longest_dry_spell_days": "🏜️ Longest dry spell (days)",
        "monsoon_onset_doy": "🌧️ Monsoon onset (day of year)",
        "gdd_proxy": "🌱 Growing-degree-days (proxy)",
    }[x],
)

fig = px.bar(idx.sort_values(metric), x="block", y=metric, color="district", title=f"{metric} by block — {year}")
fig.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(idx, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Where district-level data would mislead a farmer")
district_avg = idx.groupby("district")[metric].transform("mean")
idx["gap_vs_district_avg"] = idx[metric] - district_avg
worst = idx.reindex(idx["gap_vs_district_avg"].abs().sort_values(ascending=False).index).head(5)
st.dataframe(
    worst[["district", "block", metric, "gap_vs_district_avg"]],
    use_container_width=True, hide_index=True,
)
st.caption(
    "These blocks differ most from their own district's average for this index — "
    "a district-wide advisory would be least accurate for them."
)
