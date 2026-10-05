```python
"""Home page.  Run:  streamlit run app.py"""
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

step("👀 Quick look: one variable, one chart per district")
label = st.selectbox("Choose a weather variable", list(LABELS))
key = LABELS[label]
agg = df.groupby(["Date", "District"])[[f"{key}_blk", f"{key}_dst"]].mean().reset_index()
for col, dist in zip(st.columns(3), sorted(agg["District"].unique())):
    one = agg[agg["District"] == dist].melt(["Date", "District"], var_name="Source", value_name=label)
    one["Source"] = one["Source"].map({f"{key}_blk": "Blocks (average)", f"{key}_dst": "District"})
    fig = px.line(one, x="Date", y=label, color="Source", title=f"🏙️ {dist}",
                  color_discrete_map={"Blocks (average)": "#7C3AED", "District": DIST_COLOR[dist]})
    fig.update_layout(height=290, legend=dict(orientation="h", y=-0.3, title=None),
                      margin=dict(t=40, b=10, l=10, r=10), xaxis_title=None)
    with col:
        plot(fig)
tip("The two lines almost overlap – that means the district number follows the blocks well. "
    "Open <b>Block vs District</b> to see where they do differ.")

```

streamlit>=1.50
pandas
plotly
openpyxl
matplotlibstreamlit>=1.35
pandas>=2.0
numpy>=1.24
plotly>=5.18
openpyxl>=3.1
