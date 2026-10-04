"""Home page.  Run:  streamlit run app.py"""
import numpy as np
import plotly.express as px
import streamlit as st

from utils.data_loader import LABELS, YEARS, scorecard
from utils.style import (inject_css, hero, step, tip, kpi, plot, need_data, DIST_COLOR, VAR_ICON)

st.set_page_config(page_title="Block vs District Weather", page_icon="🌦️", layout="wide")
inject_css()
df = need_data()

hero("🌦️", "Block vs District Weather",
     "Is the weather number for a whole <b>district</b> good enough for a small local <b>block</b>? "
     "Anand · Kheda · Mahisagar, 2021–2023.")
tip("<b>In one line:</b> a <b>district</b> value is one number for a big area. A <b>block</b> is a small local area inside it. "
    "We use the block as the closer-to-ground <i>reference</i> and check how well the district number matches it.")

c1, c2, c3, c4 = st.columns(4)
kpi(c1, "Years", f"{min(YEARS)}–{max(YEARS)}", "#7C3AED")
kpi(c2, "Districts", df["District"].nunique(), "#2563EB")
kpi(c3, "Blocks", df["Block"].nunique(), "#06B6D4")
kpi(c4, "Daily records", f"{len(df):,}", "#F97316")

step("🧭 Where to go (use the left sidebar)")
cards = [("🗺️", "Block vs District", "Pick a district, click a block on the map, compare.", "pages/1_Block_vs_District.py", "#7C3AED"),
         ("🏆", "Which is reliable?", "Simple traffic-light scorecard.", "pages/2_Which_is_Reliable.py", "#2563EB"),
         ("🔥", "Spatial Hotspots", "Blocks that run hotter, wetter, windier.", "pages/3_Spatial_Hotspots.py", "#F97316"),
         ("🖼️", "Result Charts", "Your published graphs.", "pages/4_Result_Charts.py", "#10B981"),
         ("🛠️", "Fixing the gap", "Simple bias correction.", "pages/5_Bias_Correction.py", "#EC4899")]
for col, (e, t, d, target, color) in zip(st.columns(5), cards):
    with col:
        st.markdown(f'<div class="card" style="background:{color}"><h3>{e}</h3><b>{t}</b><br>'
                    f'<span style="font-size:.88rem">{d}</span></div>', unsafe_allow_html=True)
        try:
            st.page_link(target, label="Open →")
        except Exception:
            pass

step("👀 Quick look: pick a variable and a district")
sel1, sel2 = st.columns(2)
label = sel1.selectbox("Choose a weather variable", list(LABELS))
all_dists = sorted(df["District"].unique())
choice = sel2.selectbox("Choose a district", ["All districts"] + all_dists)
key = LABELS[label]
agg = df.groupby(["Date", "District"])[[f"{key}_blk", f"{key}_dst"]].mean().reset_index()
shown = all_dists if choice == "All districts" else [choice]
for col, dist in zip(st.columns(len(shown)), shown):
    one = agg[agg["District"] == dist].melt(["Date", "District"], var_name="Source", value_name=label)
    one["Source"] = one["Source"].map({f"{key}_blk": "Blocks (average)", f"{key}_dst": "District"})
    fig = px.line(one, x="Date", y=label, color="Source", title=f"🏙️ {dist}",
                  color_discrete_map={"Blocks (average)": "#7C3AED", "District": DIST_COLOR[dist]})
    fig.update_layout(height=290 if choice == "All districts" else 380,
                      legend=dict(orientation="h", y=-0.3, title=None),
                      margin=dict(t=40, b=10, l=10, r=10), xaxis_title=None)
    with col:
        plot(fig)

# ---- district-wise results (block vs district) ----
step(f"📊 Results for {choice.lower() if choice == 'All districts' else choice}")
rows = []
for dist in shown:
    d = df[df["District"] == dist]
    b, s = d[f"{key}_blk"], d[f"{key}_dst"]
    r = b.corr(s)
    rows.append({"District": dist, "Block average": round(float(b.mean()), 2), "District value": round(float(s.mean()), 2),
                 "Error (RMSE)": round(float(np.sqrt(((b - s) ** 2).mean())), 2),
                 "Bias (Block − District)": round(float((b - s).mean()), 2),
                 "Correlation": None if np.isnan(r) else round(float(r), 2)})
res = __import__("pandas").DataFrame(rows)
if choice != "All districts":
    r0 = rows[0]
    k1, k2, k3, k4 = st.columns(4)
    kpi(k1, "Block average", r0["Block average"], "#7C3AED")
    kpi(k2, "District value", r0["District value"], "#2563EB")
    kpi(k3, "Error (RMSE)", r0["Error (RMSE)"], "#F97316")
    kpi(k4, "Correlation", r0["Correlation"] if r0["Correlation"] is not None else "n/a", "#10B981")
    blk = (df[df["District"] == choice].assign(diff=lambda x: x[f"{key}_blk"] - x[f"{key}_dst"])
           .groupby("Block")["diff"].mean().round(2).reset_index())
    fig2 = px.bar(blk.sort_values("diff"), x="Block", y="diff", title=f"Each block compared with {choice} district ({label})",
                  color="diff", color_continuous_scale="RdBu_r")
    fig2.update_layout(height=340, yaxis_title="Block − District", xaxis_title=None, margin=dict(t=40, b=10, l=10, r=10))
    plot(fig2)
    tip("Bars above 0 = that block runs <b>higher</b> than the district number; below 0 = <b>lower</b>.")
else:
    st.dataframe(res, hide_index=True, width="stretch")
tip("The two lines almost overlap – that means the district number follows the blocks well. "
    "Open <b>Block vs District</b> to see where they do differ.")
