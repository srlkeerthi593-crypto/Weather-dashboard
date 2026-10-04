"""Simple bias correction: learn the usual gap, remove it."""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import VARIABLES, UNITS, continuous_metrics
from utils.style import inject_css, hero, step, tip, say, plot, table, need_data, VAR_ICON

st.set_page_config(page_title="Fixing the gap", page_icon="🛠️", layout="wide")
inject_css()
df = need_data()
hero("🛠️", "Fixing the gap (bias correction)", "Can we shrink the difference between district and block values?")

step("💡  How it works – 3 simple steps")
c1, c2, c3 = st.columns(3)
for col, color, t, txt in [(c1, "#7C3AED", "1. Learn", "Using 2021 and 2022, find the usual gap (block − district) for each block and month."),
                           (c2, "#2563EB", "2. Fix", "Add that usual gap to the district value (for rain: multiply by the usual ratio)."),
                           (c3, "#10B981", "3. Test", "Check on 2023, which the method has never seen.")]:
    col.markdown(f'<div class="card" style="background:{color}"><h3>{t}</h3>{txt}</div>', unsafe_allow_html=True)
tip("The original result files only <b>measure</b> bias. This page is an added step showing how the bias could be removed.")

train, test = df[df["Year"].isin([2021, 2022])], df[df["Year"] == 2023].copy()
keys = ["Block", "Month"]
for k in VARIABLES.values():
    if k == "Rain":
        g = train.groupby(keys).agg(b=(f"{k}_blk", "sum"), p=(f"{k}_dst", "sum")).reset_index()
        g["adj"] = np.where(g["p"] > 0, g["b"] / g["p"], 1.0).clip(0, 3)
        test = test.merge(g[keys + ["adj"]], on=keys, how="left")
        test[f"{k}_cor"] = test[f"{k}_dst"] * test["adj"].fillna(1.0)
    else:
        g = train.assign(x=train[f"{k}_blk"] - train[f"{k}_dst"]).groupby(keys)["x"].mean().rename("adj").reset_index()
        test = test.merge(g, on=keys, how="left")
        cor = test[f"{k}_dst"] + test["adj"].fillna(0.0)
        test[f"{k}_cor"] = cor.clip(0, 100) if k.startswith("RH") else cor.clip(lower=0) if k == "Wind" else cor
    test = test.drop(columns="adj")

rows = []
for k in VARIABLES.values():
    a, b = continuous_metrics(test[f"{k}_blk"], test[f"{k}_dst"], k), continuous_metrics(test[f"{k}_blk"], test[f"{k}_cor"], k)
    rows.append({"Variable": f"{VAR_ICON[k]} {k}", "k": k, "Gap before": a["RMSE"], "Gap after": b["RMSE"],
                 "Improvement %": (1 - b["RMSE"] / a["RMSE"]) * 100,
                 "Days close enough before %": a["Within"], "Days close enough after %": b["Within"]})
res = pd.DataFrame(rows)

step("📊  Result on 2023 – typical gap before and after")
m = res.melt("Variable", ["Gap before", "Gap after"], var_name="When", value_name="Typical gap (RMSE)")
fig = px.bar(m, x="Variable", y="Typical gap (RMSE)", color="When", barmode="group",
             color_discrete_map={"Gap before": "#F97316", "Gap after": "#10B981"})
fig.update_layout(height=340, margin=dict(t=10, b=10), legend=dict(orientation="h", y=1.1, title=None))
plot(fig)
table(res.drop(columns="k").round(1))
better = res[res["Improvement %"] > 0]
say(f"The gap got smaller for <b>{len(better)} of {len(res)}</b> variables"
    + (f", most for <b>{res.sort_values('Improvement %').iloc[-1].k}</b> ({res['Improvement %'].max():.0f}% smaller)." if len(better) else ".")
    + " Correction removes the <i>steady</i> gap but cannot predict day-to-day surprises, so it helps most where the gap is a steady offset.")

step("🔍  Look at one block")
a, b = st.columns(2)
block = a.selectbox("Block", sorted(test["Block"].unique()))
k = b.selectbox("Variable", list(VARIABLES.values()))
s = test[test["Block"] == block].set_index("Date")[[f"{k}_blk", f"{k}_dst", f"{k}_cor"]]
s = s.resample("MS").sum() if k == "Rain" else s.resample("MS").mean()
s = s.rename(columns={f"{k}_blk": "Block (reference)", f"{k}_dst": "District (original)", f"{k}_cor": "District (corrected)"})
fl = px.line(s.reset_index().melt("Date", var_name="Series", value_name=f"{k} ({UNITS[k]})"), x="Date", y=f"{k} ({UNITS[k]})",
             color="Series", color_discrete_map={"Block (reference)": "#7C3AED", "District (original)": "#0EA5E9",
                                                 "District (corrected)": "#10B981"})
fl.update_layout(height=360, legend=dict(orientation="h", y=1.12, title=None), margin=dict(t=30, b=10))
plot(fl)
tip("The green line (corrected) should sit closer to the purple line (block) than the blue line (original).")
