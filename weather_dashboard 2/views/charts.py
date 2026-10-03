"""Your published comparison graphs from results/."""
from pathlib import Path
import streamlit as st
from utils.style import inject_css, hero, step, tip, image

inject_css()
hero("🖼️", "Result Charts", "The comparison graphs from the project analysis, by season and year.")

RES = Path(__file__).resolve().parent.parent / "results"
FOLDERS = {"🌧️ Rainfall": "Rainfall", "🔥 Max temperature": "Tmax", "❄️ Min temperature": "Tmin",
           "💧 Morning humidity (RH-I)": "RH-I", "💦 Afternoon humidity (RH-II)": "RH-II", "🌬️ Wind speed": "WindSpeed"}
NAMES = {"ratio": "Ratio score", "hk": "HK score", "rmse": "RMSE (typical error)", "pod": "Rain caught (PoD)",
         "miss": "Miss rate", "pofd": "False alarms (POFD)", "csi": "CSI", "far": "False-alarm ratio",
         "correlation": "Correlation", "bias": "Bias"}

def title_of(p):
    s = p.stem.lower().replace("_", "")
    for k, v in NAMES.items():
        if k in s:
            return v + (" – trend" if "trend" in s else "")
    return p.stem

step("1️⃣  Choose a variable")
name = st.radio("Variable", list(FOLDERS), horizontal=True)
folder = RES / FOLDERS[name]
t1, t2 = st.tabs(["📊 All districts together", "🏙️ Split by district"])
sub2 = folder / "by_District" if (folder / "by_District").exists() else folder / "Rainfall_by_District"
for tab, sub in [(t1, folder), (t2, sub2)]:
    with tab:
        imgs = sorted(sub.glob("*.png")) if sub.exists() else []
        if not imgs:
            st.info("No charts found here.")
        for i in range(0, len(imgs), 2):
            cols = st.columns(2)
            for col, p in zip(cols, imgs[i:i + 2]):
                with col:
                    st.markdown(f"**{title_of(p)}**")
                    image(p)
tip("Each group of bars is a season; colours are years. For error/bias charts, lower (or closer to zero) is better.")
