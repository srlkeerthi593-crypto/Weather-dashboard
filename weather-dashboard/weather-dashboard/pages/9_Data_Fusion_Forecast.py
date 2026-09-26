import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

from utils.data_loader import load_blockwise, load_districtwise, merged_block_district, VARIABLES

st.set_page_config(page_title="Data Fusion Forecast", page_icon="🤖", layout="wide")
st.title("🤖 Data-Fusion Forecast: Does Blending Beat Either Source Alone?")

st.markdown(
    """
Can a model that combines **district-level values with simple block
identity/seasonal features** predict a block's true reading better than
just using the raw district value?

**Method:** train a Random Forest on one or two years of data to predict
each block's value from `(district value that day, block, day-of-year,
season)`, then test it on a year it hasn't seen. Compare its error to
simply using the district value directly ("baseline").

This is a lightweight demonstration, not a production forecasting model.
"""
)

block_df = load_blockwise()
dist_df = load_districtwise()
merged = merged_block_district(block_df, dist_df)

var = st.selectbox("Variable", list(VARIABLES.keys()), format_func=lambda k: VARIABLES[k])
years = sorted(merged["year"].unique())
test_year = st.selectbox("Test on year", years, index=len(years) - 1)
train_years = [y for y in years if y != test_year]
st.caption(f"Training on {train_years}, testing on {test_year}.")

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
    with st.spinner("Training Random Forest..."):
        rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
        rf.fit(train[features], train[var])
        pred_fused = rf.predict(test[features])

    baseline_rmse = float(np.sqrt(mean_squared_error(test[var], test[f"{var}_dist"])))
    fused_rmse = float(np.sqrt(mean_squared_error(test[var], pred_fused)))
    improvement = 100 * (baseline_rmse - fused_rmse) / baseline_rmse

    c1, c2, c3 = st.columns(3)
    c1.metric("Baseline RMSE (district value as-is)", f"{baseline_rmse:.3f}")
    c2.metric("Fused model RMSE", f"{fused_rmse:.3f}")
    c3.metric("Improvement", f"{improvement:+.1f}%")

    if improvement > 0:
        st.success(
            f"✅ Blending district data with block identity and seasonal timing "
            f"reduced error by {improvement:.1f}% vs. using district data alone."
        )
    else:
        st.warning(
            "The fused model did not beat the raw district value on this split — "
            "try a different year or variable."
        )

    st.divider()
    st.subheader("Predicted vs actual, test year")
    plot_df = test[["date", "block", var]].copy()
    plot_df["predicted_fused"] = pred_fused
    plot_df["district_value"] = test[f"{var}_dist"].values
    sample_block = st.selectbox("Inspect one block", sorted(test["block"].unique()))
    one = plot_df[plot_df["block"] == sample_block].sort_values("date")
    fig = px.line(
        one, x="date", y=[var, "predicted_fused", "district_value"],
        labels={"value": VARIABLES[var], "date": "Date", "variable": "Series"},
        title=f"{sample_block} — actual vs. fused model vs. raw district value ({test_year})",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("What the model relies on most")
    importances = pd.DataFrame({"feature": features, "importance": rf.feature_importances_}).sort_values("importance", ascending=False)
    fig2 = px.bar(importances, x="feature", y="importance", title="Feature importance")
    st.plotly_chart(fig2, use_container_width=True)
