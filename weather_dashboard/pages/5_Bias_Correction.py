"""Simple seasonal bias correction: shrink the systematic block–district gap."""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import VARIABLES, UNITS, YEARS, continuous_metrics, RAIN_THRESHOLD
from utils.style import inject_css, hero, plain_box, need_data, BLOCK_COLOR, DISTRICT_COLOR

st.set_page_config(page_title="Bias Correction", page_icon="🛠️", layout="wide")
inject_css()
df = need_data()
hero("🛠️", "Bias Correction – narrowing the block vs district gap",
     "The comparison shows the district value is usually off by a steady amount in a given block and season. "
     "We learn that offset from past years and remove it.")
plain_box("<b>How it works.</b> For every block and calendar month we measure the typical gap (block − district) in the "
          "<i>training years</i>, then add it to the district value in the <i>test year</i>. For rainfall we use a ratio "
          "(block total ÷ district total) instead of an offset, because rain cannot be negative. "
          "<b>Note:</b> this page is an added analysis – the original result files only <i>measure</i> bias, they do not correct it.")

c1, c2 = st.columns(2)
train_years = c1.multiselect("Training years (learn the offset)", YEARS, default=[2021, 2022])
test_years = [y for y in YEARS if y not in train_years]
c2.markdown(f"**Test year(s):** {', '.join(map(str, test_years)) or '—'}")
if not train_years or not test_years:
    st.warning("Choose at least one training year and leave at least one year for testing.")
    st.stop()

tr, te = df[df["Year"].isin(train_years)], df[df["Year"].isin(test_years)].copy()
keys = ["Block", "Month"]
for k in VARIABLES.values():
    if k == "Rain":
        g = tr.groupby(keys).agg(b=(f"{k}_blk", "sum"), p=(f"{k}_dst", "sum")).reset_index()
        g["adj"] = np.where(g["p"] > 0, g["b"] / g["p"], 1.0).clip(0, 3)
        te = te.merge(g[keys + ["adj"]], on=keys, how="left")
        te[f"{k}_cor"] = te[f"{k}_dst"] * te["adj"].fillna(1.0)
        te = te.drop(columns="adj")
    else:
        g = tr.assign(d=tr[f"{k}_blk"] - tr[f"{k}_dst"]).groupby(keys)["d"].mean().rename("adj").reset_index()
        te = te.merge(g, on=keys, how="left")
        cor = te[f"{k}_dst"] + te["adj"].fillna(0.0)
        if k.startswith("RH"):
            cor = cor.clip(0, 100)
        if k == "Wind":
            cor = cor.clip(lower=0)
        te[f"{k}_cor"] = cor
        te = te.drop(columns="adj")

# ───────── before / after ─────────
rows = []
for k in VARIABLES.values():
    a = continuous_metrics(te[f"{k}_blk"], te[f"{k}_dst"], k)
    b = continuous_metrics(te[f"{k}_blk"], te[f"{k}_cor"], k)
    rows.append({"Variable": k, "Unit": UNITS[k], "RMSE before": a["RMSE"], "RMSE after": b["RMSE"],
                 "RMSE change %": (b["RMSE"] / a["RMSE"] - 1) * 100,
                 "Bias before": a["Bias"], "Bias after": b["Bias"],
                 "Within tol. % before": a["Within"], "Within tol. % after": b["Within"],
                 "Corr before": a["Corr"], "Corr after": b["Corr"]})
res = pd.DataFrame(rows)
st.markdown(f"### Results on unseen year(s): {', '.join(map(str, test_years))}")
st.dataframe(res.style.format({c: "{:.2f}" for c in res.columns if c not in ("Variable", "Unit")})
             .background_gradient(subset=["RMSE change %"], cmap="RdYlGn_r"),
             hide_index=True, use_container_width=True)
better = int((res["RMSE after"] < res["RMSE before"]).sum())
plain_box(f"RMSE improved for <b>{better} of {len(res)}</b> variables. Bias drops to about zero by design; "
          "day-to-day scatter (and therefore correlation) barely changes, because a fixed offset cannot predict "
          "individual weather events.")

col1, col2 = st.columns(2)
m = res.melt("Variable", ["RMSE before", "RMSE after"], var_name="When", value_name="RMSE")
m["When"] = m["When"].str.replace("RMSE ", "")
fig = px.bar(m, x="Variable", y="RMSE", color="When", barmode="group",
             color_discrete_map={"before": DISTRICT_COLOR, "after": "#16A34A"}, title="RMSE: before vs after")
fig.update_layout(height=340, margin=dict(t=40))
col1.plotly_chart(fig, use_container_width=True)
m = res.melt("Variable", ["Bias before", "Bias after"], var_name="When", value_name="Bias")
m["When"] = m["When"].str.replace("Bias ", "")
fig = px.bar(m, x="Variable", y="Bias", color="When", barmode="group",
             color_discrete_map={"before": DISTRICT_COLOR, "after": "#16A34A"}, title="Mean bias (block − district)")
fig.update_layout(height=340, margin=dict(t=40))
col2.plotly_chart(fig, use_container_width=True)

# ───────── per block view ─────────
st.markdown("### Look at one block")
b1, b2 = st.columns(2)
block = b1.selectbox("Block", sorted(te["Block"].unique()))
k = b2.selectbox("Variable", list(VARIABLES.values()))
sub = te[te["Block"] == block].set_index("Date")[[f"{k}_blk", f"{k}_dst", f"{k}_cor"]]
sub = sub.resample("MS").sum() if k == "Rain" else sub.resample("MS").mean()
sub = sub.rename(columns={f"{k}_blk": "Block (reference)", f"{k}_dst": "District (original)", f"{k}_cor": "District (corrected)"})
fig = px.line(sub.reset_index().melt("Date", var_name="Series", value_name=f"{k} ({UNITS[k]})"),
              x="Date", y=f"{k} ({UNITS[k]})", color="Series",
              color_discrete_map={"Block (reference)": BLOCK_COLOR, "District (original)": DISTRICT_COLOR,
                                  "District (corrected)": "#16A34A"})
fig.update_layout(height=380, legend=dict(orientation="h", y=1.1), margin=dict(t=30))
st.plotly_chart(fig, use_container_width=True)

bb = []
for b, s in te.groupby("Block"):
    a, c = continuous_metrics(s[f"{k}_blk"], s[f"{k}_dst"], k), continuous_metrics(s[f"{k}_blk"], s[f"{k}_cor"], k)
    bb.append({"Block": b, "District": s["District"].iloc[0], "RMSE before": a["RMSE"], "RMSE after": c["RMSE"]})
bb = pd.DataFrame(bb).sort_values("RMSE before", ascending=False)
fig = px.bar(bb.melt(["Block", "District"], ["RMSE before", "RMSE after"], var_name="When", value_name="RMSE"),
             x="Block", y="RMSE", color="When", barmode="group",
             color_discrete_map={"RMSE before": DISTRICT_COLOR, "RMSE after": "#16A34A"},
             title=f"{k} RMSE by block (test year)")
fig.update_layout(height=360, margin=dict(t=40))
st.plotly_chart(fig, use_container_width=True)
st.caption("Limits: with only 2 training years each month has few samples, and a block's offset may drift between "
           "years. More years of data would make the correction more stable.")
