"""
style.py
--------
Everything that makes the dashboard look nice AND speak plain language,
kept in one place so every page looks and sounds consistent.
"""
import streamlit as st

# Block = blue, District = orange. Used EVERYWHERE so the eye learns:
# "blue = my small area, orange = the big area average" without reading anything.
BLOCK_COLOR = "#2563EB"
DISTRICT_COLOR = "#F97316"
GOOD_COLOR = "#16A34A"
OK_COLOR = "#F59E0B"
BAD_COLOR = "#DC2626"

UNITS = {
    "tmax": "°C", "tmin": "°C", "rainfall": "mm",
    "rh1": "%", "rh2": "%", "wind_speed": "km/h",
}

SIMPLE_NAMES = {
    "tmax": "🌡️ Hottest temperature of the day",
    "tmin": "❄️ Coldest temperature of the day",
    "rainfall": "🌧️ Rain",
    "rh1": "💧 Humidity (morning)",
    "rh2": "💧 Humidity (evening)",
    "wind_speed": "💨 Wind speed",
}


def inject_css():
    st.markdown(
        """
        <style>
        html, body, [class*="css"]  { font-family: 'Segoe UI', 'Inter', sans-serif; }

        /* Bigger, friendlier headers */
        h1 { font-weight: 800 !important; }
        h2, h3 { font-weight: 700 !important; }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 14px 18px 10px 18px;
        }
        div[data-testid="stMetric"] label { font-weight: 600 !important; color: #475569 !important; }

        /* Buttons */
        .stButton>button, .stDownloadButton>button {
            border-radius: 10px;
            font-weight: 600;
        }

        /* Tabs look like pills */
        button[data-baseweb="tab"] {
            border-radius: 10px 10px 0 0;
            font-weight: 600;
        }

        /* Sidebar nav a little roomier */
        section[data-testid="stSidebar"] { padding-top: 0.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(emoji: str, title: str, subtitle: str, gradient=("#2563EB", "#38BDF8")):
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(120deg, {gradient[0]}, {gradient[1]});
            padding: 1.6rem 2rem; border-radius: 18px; color: white;
            margin-bottom: 1.4rem; box-shadow: 0 6px 20px rgba(37,99,235,0.15);">
            <div style="font-size: 2.1rem; font-weight: 800;">{emoji} {title}</div>
            <div style="font-size: 1.05rem; opacity: 0.95; margin-top: 0.3rem; max-width: 820px;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def plain_box(text: str, icon="💬"):
    """A friendly 'in simple words' callout — use this liberally."""
    st.markdown(
        f"""
        <div style="background:#EFF6FF; border-left:5px solid {BLOCK_COLOR};
                    padding:0.8rem 1.1rem; border-radius:10px; margin:0.6rem 0;">
        <b>{icon} In simple words:</b> {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def glossary_expander():
    with st.expander("📖 Not sure what a word means? Click here"):
        st.markdown(
            """
- **Block** 📍 — a small local area (like a taluka). This is the most *local* data we have.
- **District** 🏙️ — the bigger area made of many blocks, averaged together. This is the *zoomed-out* data.
- **Match score** — a simple 0–100 score for how closely two sets of readings agree. Higher = more trustworthy stand-in.
- **RMSE** — the *technical* version of "how far off, on average" (smaller number = closer match). You don't need this number to use the dashboard — the plain-word summaries above it say the same thing in words.
- **Correlation** — do two numbers go up and down *together*? 100% = perfectly together, 0% = no relationship at all.
- **Bias** — is one source usually a bit higher or a bit lower than the other, consistently?
            """
        )


def match_rating(var: str, rmse: float):
    """
    Turn a raw RMSE number into a friendly (emoji, label, color, plain sentence).
    Thresholds are rough, hand-picked per variable so 'good' actually means good.
    """
    thresholds = {
        "tmax": (1.5, 3.0), "tmin": (1.5, 3.0),
        "rainfall": (5, 15), "rh1": (8, 15), "rh2": (8, 15),
        "wind_speed": (2, 4),
    }
    good_cut, ok_cut = thresholds.get(var, (1, 3))
    unit = UNITS.get(var, "")
    if rmse <= good_cut:
        return "🟢", "Good match", GOOD_COLOR, f"District data is a **pretty reliable stand-in** here — usually only about {rmse:.1f}{unit} off."
    elif rmse <= ok_cut:
        return "🟡", "Okay, but not perfect", OK_COLOR, f"District data is **roughly right but noticeably off** — about {rmse:.1f}{unit} on a typical day."
    else:
        return "🔴", "Poor match", BAD_COLOR, f"District data is **not a good stand-in** for this block — off by about {rmse:.1f}{unit} on a typical day."


def correlation_sentence(corr: float):
    pct = round(corr * 100)
    if corr >= 0.8:
        return "🟢", f"{pct}%", "They rise and fall together **very closely**."
    elif corr >= 0.5:
        return "🟡", f"{pct}%", "They rise and fall together **somewhat**, but not always."
    else:
        return "🔴", f"{pct}%", "They **don't** move together very reliably."


def bias_sentence(var: str, bias: float):
    unit = UNITS.get(var, "")
    if abs(bias) < 0.05 * (1 if var != "rainfall" else 1):
        return "District and block values are **usually about the same**, no strong pattern of one being higher."
    direction = "LOWER than" if bias > 0 else "HIGHER than"
    return f"The district file tends to read **{direction} the real block value**, by about {abs(bias):.1f}{unit} on average."
