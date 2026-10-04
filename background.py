"""Attractive background only. Put this file in your utils/ folder.
Call apply_background() once after inject_css() (see EDIT.txt)."""
import streamlit as st


def apply_background():
    st.markdown("""
<style>
.stApp{
  background:
    radial-gradient(rgba(37,99,235,.10) 1.2px, transparent 1.2px),
    radial-gradient(circle at 10% 4%,  rgba(255,214,102,.55), transparent 32%),
    radial-gradient(circle at 92% 8%,  rgba(125,211,252,.60), transparent 38%),
    radial-gradient(circle at 86% 92%, rgba(196,181,253,.60), transparent 40%),
    radial-gradient(circle at 6% 88%,  rgba(110,231,183,.50), transparent 36%),
    linear-gradient(180deg,#EEF4FF 0%,#F8FAFF 100%);
  background-size:26px 26px, auto, auto, auto, auto, auto;
  background-attachment:fixed;
}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stPlotlyChart"]{
  background:rgba(255,255,255,.75); border-radius:16px; padding:6px;
  box-shadow:0 6px 20px rgba(30,41,59,.10); border:1px solid rgba(255,255,255,.9);
}
</style>
""", unsafe_allow_html=True)
