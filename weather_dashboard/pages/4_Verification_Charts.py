"""Show the comparison graphs produced earlier (results/ folder)."""
from pathlib import Path
import streamlit as st
from utils.style import inject_css, hero, plain_box

st.set_page_config(page_title="Verification Charts", page_icon="🖼️", layout="wide")
inject_css()
hero("🖼️", "Verification Charts", "The season-wise and district-wise comparison graphs from the project results.")

RES = Path(__file__).resolve().parent.parent / "results"
FOLDERS = {"Rainfall": "Rainfall", "Max temperature": "Tmax", "Min temperature": "Tmin",
           "Morning humidity (RH-I)": "RH-I", "Afternoon humidity (RH-II)": "RH-II", "Wind speed": "WindSpeed"}
NICE = {"ratio": "Ratio score", "hk": "Hanssen–Kuipers score", "rmse": "RMSE", "pod": "Probability of detection",
        "missrate": "Miss rate", "pofd": "POFD (false alarms)", "csi": "CSI", "far": "False-alarm ratio",
        "correlation": "Correlation", "bias": "Bias", "ratioscore": "Ratio score"}

def caption(p: Path) -> str:
    s = p.stem.lower()
    for k, v in NICE.items():
        if k in s.replace("_", "").replace("trend", ""):
            return v + (" trend" if "trend" in s else "")
    return p.stem.replace("_", " ")

name = st.selectbox("Variable", list(FOLDERS))
folder = RES / FOLDERS[name]
if not folder.exists():
    st.error(f"Folder not found: results/{FOLDERS[name]}")
    st.stop()
t1, t2 = st.tabs(["📊 All districts together (season × year)", "🏙️ Split by district"])
for tab, sub in [(t1, folder), (t2, folder / "by_District" if (folder / "by_District").exists()
                                  else folder / f"{FOLDERS[name]}_by_District")]:
    with tab:
        imgs = sorted(sub.glob("*.png")) if sub.exists() else []
        if not imgs:
            st.info("No charts here.")
            continue
        cols = st.columns(2)
        for i, p in enumerate(imgs):
            with cols[i % 2], st.container(border=True):
                st.image(str(p), use_container_width=True)
                st.caption(caption(p))
plain_box("These are the static charts exported from the analysis notebook. Use the other pages for interactive, "
          "block-by-block exploration.")
