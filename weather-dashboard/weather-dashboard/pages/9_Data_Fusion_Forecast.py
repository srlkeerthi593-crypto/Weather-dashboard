import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

from utils.data_loader import load_blockwise, load_districtwise, merged_block_district, VARIABLES
from utils.style import inject_css, hero, plain_box, glossary_expander, SIMPLE_NAMES, BLOCK_COLOR, DISTRICT_COLOR

st.set_page_config(page_title="Data Fusion Forecast", page_icon="🤖", layout="wide")
inject_css()
hero("🤖", "Can AI Blend the Two Sources?", "Testing whether mixing district data with local patterns beats using district data alone.", gradient=("#7C3AED", "#A78BFA"))
plain_box(
    "We train a small AI model (a 'Random Forest') on district readings plus each block's identity and "
    "the time of year, using two years of data. Then we test it on a year it has never seen, and check: "
    "<b>does the blend guess a block's real weather better than the raw district number would?</b>"
)
glossary_expander()

block_df = load_blockwise()
dist_df = load_districtwise()
merged = merged_block_district(block_df, dist_df)

var = st.selectbox("Weather variable", list(VARIABLES.keys()), format_func=lambda k: SIMPLE_NAMES[k])
years = sorted(merged["year"].unique())
test_year = st.selectbox("Test the model on this year (it won't see this data while learning)", years, index=len(years) - 1)
train_years = [y for y in years if y != test_year]
st.caption(f"📚 Learns from {train_years}, then gets tested on {test_year}.")

data = merged.dropna(subset=[var, f"{var}_dist"]).copy()
data["doy"] = data["date"].dt.dayofyear
data["block_code"] = data["block"].astype("category").cat.codes
data["season_code"] = data["season"].astype("category").cat.codes
features = [f"{var}_dist", "block_code", "doy", "season_code"]
train = data[data["year"].isin(train_years)]
test = data[data["year"] == test_year]

if len(train) < 50 or len(test) < 50:
    st.warning("Not enough data for this split.")
else:
    with st.spinner("Training the model..."):
        rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
        rf.fit(train[features], train[var])
        pred_fused = rf.predict(test[features])

    baseline_rmse = float(np.sqrt(mean_squared_error(test[var], test[f"{var}_dist"])))
    fused_rmse = float(np.sqrt(mean_squared_error(test[var], pred_fused)))
    improvement = 100 * (baseline_rmse - fused_rmse) / baseline_rmse

    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("#### 🏙️ Using district data as-is")
            st.metric("Average error", f"{baseline_rmse:.2f}")
    with c2:
        with st.container(border=True):
            st.markdown("#### 🤖 Using the blended AI guess")
            st.metric("Average error", f"{fused_rmse:.2f}")
    with c3:
        with st.container(border=True):
            st.markdown("#### 🏆 Improvement")
            st.metric("Better by", f"{improvement:+.1f}%")

    if improvement > 0:
        st.success(f"✅ Blending beat the raw district value here — {improvement:.1f}% less average error.")
    else:
        st.warning("The blend didn't beat district data alone on this split — try a different year or variable.")

    st.divider()
    st.markdown("### 👀 See it in action for one block")
    plot_df = test[["date", "block", var]].copy()
    plot_df["predicted_fused"] = pred_fused
    plot_df["district_value"] = test[f"{var}_dist"].values
    sample_block = st.selectbox("Pick a block", sorted(test["block"].unique()))
    one = plot_df[plot_df["block"] == sample_block].sort_values("date")
    fig = px.line(
        one, x="date", y=[var, "predicted_fused", "district_value"],
        color_discrete_map={var: "#111827", "predicted_fused": "#7C3AED", "district_value": DISTRICT_COLOR},
        labels={"value": SIMPLE_NAMES[var], "date": "", "variable": "Source"},
        title=f"{sample_block} — actual vs. AI blend vs. raw district value ({test_year})",
    )
    fig.for_each_trace(lambda t: t.update(name={var: "⚫ Actual", "predicted_fused": "🤖 AI blend", "district_value": "🏙️ District (raw)"}.get(t.name, t.name)))
    fig.update_layout(height=420, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("🧠 What is the model paying most attention to?"):
        importances = pd.DataFrame({"feature": features, "importance": rf.feature_importances_}).sort_values("importance", ascending=False)
        fig2 = px.bar(importances, x="feature", y="importance")
        st.plotly_chart(fig2, use_container_width=True)
