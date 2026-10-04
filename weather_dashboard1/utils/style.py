"""Look & feel + small helpers that work on old AND new Streamlit versions."""
import streamlit as st

DIST_COLOR = {"Anand": "#2563EB", "Kheda": "#16A34A", "Mahisagar": "#F97316"}
BLOCK_COLOR = "#7C3AED"      # purple = block (local)
DISTRICT_COLOR = "#0EA5E9"   # sky blue = district (whole area)
GOOD, OK, BAD = "#16A34A", "#F59E0B", "#EF4444"
VAR_ICON = {"Rain": "🌧️", "Tmax": "🔥", "Tmin": "❄️", "RH-I": "💧", "RH-II": "💦", "Wind": "🌬️"}
VAR_COLOR = {"Rain": "#3B82F6", "Tmax": "#EF4444", "Tmin": "#06B6D4", "RH-I": "#8B5CF6", "RH-II": "#EC4899", "Wind": "#10B981"}

CSS = """
<style>
.block-container {padding-top: 1.4rem; max-width: 1300px;}
.hero {background: linear-gradient(120deg,#7c3aed,#2563eb 55%,#06b6d4); color:#fff; padding:1.5rem 1.8rem;
       border-radius:18px; margin-bottom:1rem; box-shadow:0 6px 18px rgba(37,99,235,.25);}
.hero h1 {margin:0; font-size:2rem; color:#fff;}
.hero p {margin:.4rem 0 0; opacity:.95; font-size:1.05rem;}
.tip {background:#fffbeb; border-left:6px solid #f59e0b; padding:.8rem 1rem; border-radius:10px; color:#78350f; margin:.6rem 0;}
.say {background:#ecfdf5; border-left:6px solid #10b981; padding:.8rem 1rem; border-radius:10px; color:#064e3b; margin:.6rem 0;}
.step {background:linear-gradient(90deg,#ede9fe,#e0f2fe); padding:.5rem 1rem; border-radius:10px; font-weight:700;
       color:#312e81; margin:1.1rem 0 .5rem;}
.card {border-radius:16px; padding:1rem 1.1rem; color:#fff; box-shadow:0 4px 12px rgba(0,0,0,.12);}
.card h3 {margin:0 0 .5rem; color:#fff;}
.card table {width:100%; border-collapse:collapse;}
.card td {padding:5px 2px; border-bottom:1px solid rgba(255,255,255,.28); font-size:1rem;}
.card td:last-child {text-align:right; font-weight:700;}
.pill {display:inline-block; padding:2px 10px; border-radius:999px; background:rgba(255,255,255,.25); font-size:.78rem; font-weight:700;}
.kpi {border-radius:14px; padding:.8rem 1rem; color:#fff; text-align:center;}
.kpi b {font-size:1.6rem; display:block;}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(emoji, title, subtitle):
    st.markdown(f'<div class="hero"><h1>{emoji} {title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def step(text):
    st.markdown(f'<div class="step">{text}</div>', unsafe_allow_html=True)


def tip(html):
    st.markdown(f'<div class="tip">💡 {html}</div>', unsafe_allow_html=True)


def say(html):
    st.markdown(f'<div class="say">📝 {html}</div>', unsafe_allow_html=True)


def kpi(col, label, value, color):
    col.markdown(f'<div class="kpi" style="background:{color}"><b>{value}</b>{label}</div>', unsafe_allow_html=True)


def plot(fig, key=None, select=False):
    """Show a plotly figure. Works on old and new Streamlit. Returns selection event (or None)."""
    attempts = []
    if select:
        attempts += [dict(on_select="rerun", width="stretch"), dict(on_select="rerun", use_container_width=True)]
    attempts += [dict(width="stretch"), dict(use_container_width=True), dict()]
    for kw in attempts:
        try:
            return st.plotly_chart(fig, key=key, **kw)
        except TypeError:
            continue


def table(df, **kw):
    try:
        st.dataframe(df, hide_index=True, width="stretch", **kw)
    except TypeError:
        st.dataframe(df, hide_index=True, use_container_width=True, **kw)


def image(path):
    try:
        st.image(str(path), width="stretch")
    except TypeError:
        st.image(str(path), use_container_width=True)


def need_data():
    from utils.data_loader import load_merged
    try:
        return load_merged()
    except FileNotFoundError as e:
        st.error(str(e))
        st.info("Put the 3 yearly Excel files in the `data/` folder and reload.")
        st.stop()


def verdict(match_pct):
    """Traffic-light wording from '% of days the district value is close enough to the block'."""
    if match_pct >= 85:
        return "🟢", "very close", GOOD
    if match_pct >= 65:
        return "🟡", "roughly close", OK
    return "🔴", "often different", BAD
