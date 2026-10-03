"""Look & feel helpers shared by every page."""
import streamlit as st

DIST_COLOR = {"Anand": "#2563EB", "Kheda": "#16A34A", "Mahisagar": "#F97316"}
BLOCK_COLOR = "#7C3AED"      # purple  = block (local)
DISTRICT_COLOR = "#0EA5E9"   # blue    = district (wide area)

CSS = """
<style>
.block-container {padding-top: 1.6rem; max-width: 1350px;}
.hero {background: linear-gradient(120deg,#1e3a8a,#0ea5e9); color:#fff; padding:1.4rem 1.6rem;
       border-radius:16px; margin-bottom:1rem;}
.hero h1 {margin:0; font-size:1.9rem; color:#fff;}
.hero p {margin:.4rem 0 0; opacity:.92; font-size:1rem;}
.plain {background:#f1f5f9; border-left:5px solid #0ea5e9; padding:.8rem 1rem; border-radius:8px;
        color:#0f172a; margin:.6rem 0;}
.tag-b {background:#ede9fe; color:#5b21b6; padding:2px 10px; border-radius:999px; font-weight:600; font-size:.8rem;}
.tag-d {background:#e0f2fe; color:#075985; padding:2px 10px; border-radius:999px; font-weight:600; font-size:.8rem;}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(emoji: str, title: str, subtitle: str):
    st.markdown(f'<div class="hero"><h1>{emoji} {title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def plain_box(html: str):
    st.markdown(f'<div class="plain">{html}</div>', unsafe_allow_html=True)


def glossary():
    with st.expander("📖 Quick glossary (plain words)"):
        st.markdown(
            "- **Block (taluka)** – a small local area. Its data is our *reference* (the closer-to-the-ground view).\n"
            "- **District** – the big region. Its data is the *wide-area forecast* that we test against the block.\n"
            "- **Bias (block − district)** – positive means the block is warmer/wetter/windier than the district number; negative means the opposite.\n"
            "- **RMSE / MAE** – typical size of the gap between the two. Smaller = closer.\n"
            "- **Correlation (r)** – do they rise and fall together? 1 = perfectly in step.\n"
            "- **Within tolerance %** – share of days when the district value is 'close enough' to the block "
            "(±2 °C temperature, ±10 % humidity, ±3 km/h wind, same rain/no-rain call).\n"
            "- **HK score** – rain score that punishes both missed rain and false alarms (1 is perfect).\n"
            "- **PoD / POFD** – share of rainy days caught / share of dry days wrongly called rainy."
        )


def need_data():
    """Call at top of each page: stops with a friendly message if data are missing."""
    from utils.data_loader import load_merged
    try:
        return load_merged()
    except FileNotFoundError as e:
        st.error(str(e))
        st.info("Add the 3 yearly Excel files to the `data/` folder and reload.")
        st.stop()
