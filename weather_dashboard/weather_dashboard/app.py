"""
Weather Forecast Verification Dashboard
Anand · Kheda · Mahisagar  |  2021 – 2023
Observed = blockwise data   |   Forecast = districtwise data
"""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ───────────────────────── Page setup ─────────────────────────
st.set_page_config(page_title="Weather Forecast Verification", page_icon="🌦️", layout="wide")

BASE = Path(__file__).parent / "results_final"
YEARS = [2021, 2022, 2023]
SEASONS = ["Winter", "Summer", "Monsoon", "Post-monsoon"]

# parameter → (folder, file prefix, unit, icon)
PARAMS = {
    "Max Temperature":  dict(folder="Tmax",      prefix="Tmax",      unit="°C",   icon="🌡️"),
    "Min Temperature":  dict(folder="Tmin",      prefix="Tmin",      unit="°C",   icon="❄️"),
    "Humidity (RH-I)":  dict(folder="RH-I",      prefix="RHI",       unit="%",    icon="💧"),
    "Humidity (RH-II)": dict(folder="RH-II",     prefix="RHII",      unit="%",    icon="💦"),
    "Wind Speed":       dict(folder="WindSpeed", prefix="WindSpeed", unit="km/h", icon="🌬️"),
}

# colour palette (used in CSS + pies)
TEAL, AMBER, CORAL, INDIGO, SKY, NAVY, GREEN = "#0E9F9A", "#F59E0B", "#EF4444", "#6366F1", "#38BDF8", "#0B2545", "#22C55E"

# ───────────────────────── Theme / CSS ─────────────────────────
st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(180deg,#EAF4FB 0%,#F7FAFC 40%); }}
.block-container {{ padding-top: 1.4rem; max-width: 1250px; }}

/* sidebar */
[data-testid="stSidebar"] {{ background: linear-gradient(180deg,{NAVY} 0%,#13406B 100%); }}
[data-testid="stSidebar"] * {{ color: #EAF4FB !important; }}
[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.18); }}

/* hero banner */
.hero {{ background: linear-gradient(120deg,{NAVY} 0%,#146C94 55%,{TEAL} 100%);
         border-radius: 20px; padding: 26px 32px; color: white; margin-bottom: 18px;
         box-shadow: 0 8px 24px rgba(11,37,69,.25); }}
.hero h1 {{ margin: 0; font-size: 2rem; color: white; }}
.hero p  {{ margin: 6px 0 0 0; opacity: .92; font-size: 1.02rem; }}

/* KPI cards */
.kpi {{ background: white; border-radius: 16px; padding: 16px 18px; height: 100%;
        box-shadow: 0 4px 14px rgba(11,37,69,.08); border-top: 5px solid var(--c); }}
.kpi .lab {{ font-size: .82rem; color: #5B6B7B; text-transform: uppercase; letter-spacing: .04em; }}
.kpi .val {{ font-size: 2rem; font-weight: 800; color: var(--c); line-height: 1.2; }}
.kpi .sub {{ font-size: .82rem; color: #5B6B7B; }}

/* takeaway + info boxes */
.take {{ background: linear-gradient(90deg,#FFF7E0,#FFFBF0); border-left: 6px solid {AMBER};
         border-radius: 12px; padding: 14px 18px; margin: 10px 0 16px 0; color:#4A3A0A; }}
.info {{ background: #E8F7F6; border-left: 6px solid {TEAL}; border-radius: 12px;
         padding: 12px 18px; margin: 6px 0 14px 0; color:#0B4F4C; }}

h2, h3 {{ color: {NAVY}; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ background: white; border-radius: 16px; }}
.bar-row {{ display:flex; align-items:center; margin:8px 0; font-size:.92rem; }}
.bar-row .n {{ width: 150px; color:#12263A; }}
.bar-row .b {{ flex:1; background:#E3ECF3; border-radius:8px; height:16px; overflow:hidden; }}
.bar-row .b > div {{ height:100%; border-radius:8px; background: linear-gradient(90deg,{TEAL},{SKY}); }}
.bar-row .v {{ width: 60px; text-align:right; font-weight:700; color:{NAVY}; }}
</style>
""", unsafe_allow_html=True)


# ───────────────────────── Data loaders ─────────────────────────
@st.cache_data
def load_param(key):
    p = PARAMS[key]
    f = BASE / p["folder"] / f"{p['prefix']}_long_format.xlsx"
    return pd.read_excel(f)

@st.cache_data
def load_param_district(key):
    p = PARAMS[key]
    f = BASE / p["folder"] / "by_District" / f"{p['folder']}_by_District_long.xlsx"
    return pd.read_excel(f)

@st.cache_data
def load_rain_district():
    d = pd.read_excel(BASE / "Rainfall" / "Rainfall_by_District" / "Rainfall_by_District_long.xlsx")
    d["Year"] = d["Year"].astype(str)
    return d

@st.cache_data
def load_rain_table():
    """Season table (Table 1) → tidy dataframe."""
    raw = pd.read_excel(BASE / "Rainfall" / "Table1_rainfall_verification.xlsx", header=[0, 1], index_col=0)
    raw.columns = pd.MultiIndex.from_tuples([(a, int(float(b))) for a, b in raw.columns])
    rows = []
    for season in raw.index:
        for (metric, yr) in raw.columns:
            rows.append(dict(Season=season, Metric=metric, Year=yr, Value=raw.loc[season, (metric, yr)]))
    return pd.DataFrame(rows).dropna(subset=["Season"])


def img(path, caption=None):
    path = BASE / path
    if path.exists():
        st.image(str(path), width="stretch", caption=caption)
    else:
        st.warning(f"Chart not found: {path.name}")


def kpi(col, label, value, sub, color):
    col.markdown(f'<div class="kpi" style="--c:{color}"><div class="lab">{label}</div>'
                 f'<div class="val">{value}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)


def pie(labels, values, colors, title, hole=0.5, center=None):
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=hole, sort=False,
                           marker=dict(colors=colors, line=dict(color="white", width=3)),
                           textinfo="percent", textfont=dict(size=15, color="white"),
                           hovertemplate="%{label}<br>%{value:,} (%{percent})<extra></extra>"))
    fig.update_layout(title=dict(text=title, font=dict(size=16, color=NAVY), x=0.5),
                      height=370, margin=dict(t=60, b=10, l=10, r=10),
                      legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"),
                      paper_bgcolor="rgba(0,0,0,0)")
    if center:
        fig.add_annotation(text=center, x=0.5, y=0.5, showarrow=False, font=dict(size=22, color=NAVY))
    return fig


def quality_label(r):
    return "Strong (r ≥ 0.80)" if r >= 0.8 else ("Moderate (0.60–0.80)" if r >= 0.6 else "Weak (r < 0.60)")

QUAL_COLORS = {"Strong (r ≥ 0.80)": GREEN, "Moderate (0.60–0.80)": AMBER, "Weak (r < 0.60)": CORAL}


def quality_counts(df):
    d = df[df["Season"] != "Annual"]
    return d["Correlation"].apply(quality_label).value_counts().reindex(list(QUAL_COLORS), fill_value=0)


def hero(title, subtitle):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


# ───────────────────────── Sidebar ─────────────────────────
with st.sidebar:
    st.markdown("## 🌦️ Forecast Verification")
    st.caption("Anand · Kheda · Mahisagar  \n2021 – 2023")
    page = st.radio("Go to", ["🏠 Overview", "🌧️ Rainfall", "🌡️ Temperature, Humidity & Wind",
                              "📍 District Comparison", "🔧 Bias Correction"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**How the data is used**")
    st.caption("**Observed** → block-wise data  \n**Forecast** → district-wise data  \n"
               "Seasons: Winter · Summer · Monsoon · Post-monsoon")


# ═════════════════════════ 1. OVERVIEW ═════════════════════════
if page == "🏠 Overview":
    hero("How good are our weather forecasts?",
         "Forecast vs. observed weather for 3 districts over 3 years — in one glance.")

    rd = load_rain_district()
    yr = rd[rd["Year"].isin(["2021", "2022", "2023"])]
    tot = yr[["NN", "NY", "YN", "YY", "N"]].sum()
    ratio = (tot.YY + tot.NN) / tot.N * 100
    pod = tot.YY / (tot.YY + tot.YN) * 100

    tmax = load_param("Max Temperature"); tmax_a = tmax[tmax.Season == "Annual"]

    c = st.columns(4)
    kpi(c[0], "Rainfall accuracy", f"{ratio:.1f}%", "days correctly forecast (rain / no rain)", TEAL)
    kpi(c[1], "Rain events caught", f"{pod:.1f}%", "of actual rainy days were forecast", INDIGO)
    kpi(c[2], "Max-temp error", f"{tmax_a.RMSE.mean():.2f} °C", "average RMSE over 3 years", AMBER)
    kpi(c[3], "Max-temp match", f"{tmax_a.Correlation.mean():.2f}", "correlation (1.0 = perfect)", CORAL)
    st.write("")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.plotly_chart(pie(["Rain forecast & rain happened (Hit)", "No rain forecast & none happened",
                                 "Rain forecast but none (False alarm)", "Rain happened but not forecast (Miss)"],
                                [tot.YY, tot.NN, tot.NY, tot.YN], [GREEN, SKY, AMBER, CORAL],
                                "Rainfall forecast outcomes (rain ≥ 2.5 mm, all districts, 2021–23)",
                                center=f"{ratio:.0f}%<br><span style='font-size:12px'>correct</span>"),
                            width="stretch")
    with right:
        with st.container(border=True):
            tot_q = sum(quality_counts(load_param(k)) for k in PARAMS)
            st.plotly_chart(pie(list(tot_q.index), list(tot_q.values), [QUAL_COLORS[i] for i in tot_q.index],
                                "Temperature, humidity & wind — forecast quality",
                                center=f"{int(tot_q.sum())}<br><span style='font-size:12px'>checks</span>"),
                            width="stretch")
            st.caption("Each check = one parameter × one season × one year, rated by correlation with observations.")

    with st.container(border=True):
        st.markdown("#### 🏆 Which parameter is forecast best? (average correlation, 2021–23)")
        rows = []
        for k in PARAMS:
            d = load_param(k); rows.append((k, d[d.Season == "Annual"].Correlation.mean()))
        rows.sort(key=lambda t: -t[1])
        html = "".join(f'<div class="bar-row"><div class="n">{PARAMS[k]["icon"]} {k}</div>'
                       f'<div class="b"><div style="width:{v*100:.0f}%"></div></div><div class="v">{v:.2f}</div></div>'
                       for k, v in rows)
        st.markdown(html, unsafe_allow_html=True)

    mon = load_rain_table(); mon = mon[(mon.Season == "Monsoon") & (mon.Metric == "Ratio score (%)")].Value.mean()
    ann = load_rain_table(); ann = ann[(ann.Season == "Annual") & (ann.Metric == "Ratio score (%)")].Value.mean()
    st.markdown(f'<div class="take">💡 <b>Key message:</b> Rainfall is correctly forecast on about <b>{ann:.0f}%</b> of days '
                f'over the year, but accuracy drops to about <b>{mon:.0f}%</b> in the monsoon — the hardest season to forecast. '
                f'Best-matched parameter: <b>{rows[0][0]}</b>.</div>', unsafe_allow_html=True)


# ═════════════════════════ 2. RAINFALL ═════════════════════════
elif page == "🌧️ Rainfall":
    hero("🌧️ Rainfall Forecast Verification", "Did the forecast say 'rain' when it rained, and 'no rain' when it didn't?")

    rd = load_rain_district()
    choice = st.segmented_control("Year", ["All years"] + [str(y) for y in YEARS], default="All years") or "All years"
    sel = rd[rd["Year"].isin(["2021", "2022", "2023"])] if choice == "All years" else rd[rd["Year"] == choice]
    t = sel[["NN", "NY", "YN", "YY", "N"]].sum()
    ratio = (t.YY + t.NN) / t.N * 100
    pod = t.YY / (t.YY + t.YN) * 100
    hk = (t.YY * t.NN - t.NY * t.YN) / ((t.YY + t.YN) * (t.NN + t.NY))

    c = st.columns(3)
    kpi(c[0], "Ratio score", f"{ratio:.1f}%", "days correct out of all days", TEAL)
    kpi(c[1], "Probability of Detection", f"{pod:.1f}%", "rainy days that were forecast", INDIGO)
    kpi(c[2], "HK score", f"{hk:.2f}", "overall skill (1 = perfect, 0 = no skill)", AMBER)
    st.write("")

    p1, p2 = st.columns(2)
    with p1:
        with st.container(border=True):
            st.plotly_chart(pie(["Hit", "Correct 'no rain'", "False alarm", "Miss"],
                                [t.YY, t.NN, t.NY, t.YN], [GREEN, SKY, AMBER, CORAL],
                                f"Forecast outcomes — {choice}"), width="stretch")
    with p2:
        with st.container(border=True):
            st.plotly_chart(pie(["Correct forecasts", "Wrong forecasts"], [t.YY + t.NN, t.NY + t.YN],
                                [TEAL, CORAL], f"Right vs wrong — {choice}",
                                center=f"{ratio:.0f}%"), width="stretch")
    st.markdown('<div class="info"><b>Hit</b> = rain forecast and it rained · <b>Miss</b> = it rained but no forecast · '
                '<b>False alarm</b> = rain forecast but dry · Rain day = ≥ 2.5 mm</div>', unsafe_allow_html=True)

    st.markdown("### Season-wise results")
    chart = st.segmented_control("Choose a chart",
                                 ["Ratio score", "HK score", "Rain detected (PoD)", "Forecast error (RMSE)"],
                                 default="Ratio score") or "Ratio score"
    files = {"Ratio score": "chart1_ratio_score.png", "HK score": "chart2_hk_score_labeled.png",
             "Rain detected (PoD)": "chart4_Rainfall_PoD.png", "Forecast error (RMSE)": "chart3_rmse_trend.png"}
    notes = {"Ratio score": "Share of days the forecast got right. Higher = better.",
             "HK score": "Balances catching rain against false alarms. Higher = better.",
             "Rain detected (PoD)": "Of the days it really rained, how many were forecast. Higher = better.",
             "Forecast error (RMSE)": "Typical size of rainfall error in mm. Lower = better."}
    with st.container(border=True):
        img(f"Rainfall/{files[chart]}")
        st.caption(notes[chart])

    with st.expander("📊 More scores (Miss rate, False alarms, CSI, FAR)"):
        a, b = st.columns(2)
        with a: img("Rainfall/chart4a_MissRate.png"); img("Rainfall/chart4c_CSI.png")
        with b: img("Rainfall/chart4b_POFD.png"); img("Rainfall/chart4d_FAR.png")

    tb = load_rain_table(); r = tb[(tb.Metric == "Ratio score (%)") & (tb.Season != "Annual")].groupby("Season").Value.mean()
    st.markdown(f'<div class="take">💡 <b>Key message:</b> Forecasts are most reliable in <b>{r.idxmax()}</b> '
                f'(~{r.max():.0f}% correct) and weakest in <b>{r.idxmin()}</b> (~{r.min():.0f}%), the season with the most rainfall. '
                f'<br><small>Dry seasons show "N/A" HK scores when no rain ≥ 2.5 mm occurred.</small></div>', unsafe_allow_html=True)


# ═════════════════════════ 3. TEMPERATURE / HUMIDITY / WIND ═════════════════════════
elif page == "🌡️ Temperature, Humidity & Wind":
    hero("🌡️ Temperature, Humidity & Wind", "How close is the forecast to what was actually measured?")

    names = list(PARAMS)
    param = st.segmented_control("Parameter", names, default=names[0]) or names[0]
    P = PARAMS[param]; u = P["unit"]
    d = load_param(param); ann = d[d.Season == "Annual"]

    c = st.columns(3)
    kpi(c[0], "Average error (RMSE)", f"{ann.RMSE.mean():.2f} {u}", "lower is better", AMBER)
    kpi(c[1], "Correlation", f"{ann.Correlation.mean():.2f}", "closer to 1 is better", TEAL)
    b = ann["Mean_Bias (O-P)"].mean()
    kpi(c[2], "Average bias", f"{b:+.2f} {u}", "forecast too high" if b < 0 else "forecast too low", INDIGO)
    st.write("")

    left, right = st.columns([3, 2])
    with left:
        metric = st.segmented_control("Show", ["Error (RMSE)", "Correlation", "Bias"], default="Error (RMSE)") or "Error (RMSE)"
        idx = {"Error (RMSE)": 1, "Correlation": 2, "Bias": 3}[metric]
        fname = sorted((BASE / P["folder"]).glob(f"chart{idx}_*.png"))[0].name
        with st.container(border=True):
            img(f"{P['folder']}/{fname}")
        st.caption({1: "Typical size of the forecast error — lower is better.",
                    2: "How well forecast and observed move together — higher is better.",
                    3: "Observed − Forecast. Below 0 means the forecast ran too high; above 0 means too low."}[idx])
    with right:
        with st.container(border=True):
            q = quality_counts(d)
            st.plotly_chart(pie(list(q.index), list(q.values), [QUAL_COLORS[i] for i in q.index],
                                f"{param}: forecast quality", center=f"{int(q.sum())}<br><span style='font-size:12px'>checks</span>"),
                            width="stretch")
            st.caption("Each check = one season × one year.")

    s = d[d.Season != "Annual"].groupby("Season").Correlation.mean()
    st.markdown(f'<div class="take">💡 <b>Key message:</b> {param} matches observations best in <b>{s.idxmax()}</b> '
                f'(r ≈ {s.max():.2f}) and least in <b>{s.idxmin()}</b> (r ≈ {s.min():.2f}).</div>', unsafe_allow_html=True)


# ═════════════════════════ 4. DISTRICT COMPARISON ═════════════════════════
elif page == "📍 District Comparison":
    hero("📍 District Comparison", "Anand vs Kheda vs Mahisagar — which district is forecast best?")

    opts = ["🌧️ Rainfall"] + [f"{v['icon']} {k}" for k, v in PARAMS.items()]
    sel = st.segmented_control("Parameter", opts, default=opts[0]) or opts[0]

    if sel.startswith("🌧️"):
        rd = load_rain_district(); pooled = rd[rd.Year == "2021-23 Pooled"].set_index("District")
        c = st.columns(3)
        for col, (dist, color) in zip(c, zip(pooled.index, [TEAL, INDIGO, AMBER])):
            kpi(col, dist, f"{pooled.loc[dist, 'Ratio_score']*100:.1f}%",
                f"rainfall accuracy · HK {pooled.loc[dist, 'HK_score']:.2f}", color)
        st.write("")
        p1, p2 = st.columns([2, 3])
        with p1:
            with st.container(border=True):
                st.plotly_chart(pie(list(pooled.index), list(pooled.YY), [TEAL, INDIGO, AMBER],
                                    "Share of rain events caught (hits)", center="Hits"), width="stretch")
        with p2:
            m = st.segmented_control("Show", ["Ratio score", "HK score", "Rain detected (PoD)"], default="Ratio score") or "Ratio score"
            f = {"Ratio score": "chart1_District_RatioScore.png", "HK score": "chart2_District_HK.png",
                 "Rain detected (PoD)": "chart3_District_PoD.png"}[m]
            with st.container(border=True):
                img(f"Rainfall/Rainfall_by_District/{f}")
        best = pooled.Ratio_score.idxmax()
        st.markdown(f'<div class="take">💡 <b>Key message:</b> <b>{best}</b> has the highest rainfall accuracy '
                    f'({pooled.Ratio_score.max()*100:.1f}%). Differences between districts are small, so forecast quality is fairly uniform across the region.</div>',
                    unsafe_allow_html=True)
    else:
        param = sel.split(" ", 1)[1]; P = PARAMS[param]; u = P["unit"]
        dd = load_param_district(param)
        avg = dd.groupby("District")[["RMSE", "Correlation", "Mean_Bias (O-P)"]].mean()
        c = st.columns(3)
        for col, (dist, color) in zip(c, zip(avg.index, [TEAL, INDIGO, AMBER])):
            kpi(col, dist, f"{avg.loc[dist, 'RMSE']:.2f} {u}", f"avg error (RMSE) · r = {avg.loc[dist, 'Correlation']:.2f}", color)
        st.write("")
        p1, p2 = st.columns([2, 3])
        with p1:
            with st.container(border=True):
                inv = 1 / avg["RMSE"]   # larger slice = smaller error = better
                st.plotly_chart(pie(list(avg.index), list(inv.values), [TEAL, INDIGO, AMBER],
                                    "Forecast reliability share (larger = lower error)", center="Reliability"),
                                width="stretch")
        with p2:
            m = st.segmented_control("Show", ["Error (RMSE)", "Correlation", "Bias"], default="Error (RMSE)") or "Error (RMSE)"
            f = {"Error (RMSE)": "chart1_RMSE_by_District.png", "Correlation": "chart2_Correlation_by_District.png",
                 "Bias": "chart3_Bias_by_District.png"}[m]
            with st.container(border=True):
                img(f"{P['folder']}/by_District/{f}")
        best = avg.RMSE.idxmin()
        st.markdown(f'<div class="take">💡 <b>Key message:</b> For {param.lower()}, <b>{best}</b> has the lowest error '
                    f'({avg.RMSE.min():.2f} {u}); <b>{avg.RMSE.idxmax()}</b> has the highest ({avg.RMSE.max():.2f} {u}).</div>',
                    unsafe_allow_html=True)


# ═════════════════════════ 5. BIAS CORRECTION ═════════════════════════
else:
    hero("🔧 Bias Correction", "Forecasts that run consistently high or low can be corrected — here is where it matters most.")

    st.markdown("### Current bias in the raw forecast (Observed − Forecast, annual)")
    rows = []
    for k, P in PARAMS.items():
        d = load_param(k); a = d[d.Season == "Annual"].set_index("Year")["Mean_Bias (O-P)"]
        rows.append({"Parameter": f"{P['icon']} {k}", "Unit": P["unit"], **{str(y): round(a.get(y, float('nan')), 2) for y in YEARS}})
    tb = pd.DataFrame(rows)
    st.dataframe(tb.style.background_gradient(cmap="RdYlGn_r", subset=[str(y) for y in YEARS], vmin=-3, vmax=3)
                 .format({str(y): "{:+.2f}" for y in YEARS}), width="stretch", hide_index=True)
    st.caption("Negative = forecast too high · Positive = forecast too low · Values near 0 = little correction needed.")

    st.markdown('<div class="info">🛠️ <b>Bias-correction results are not in the dashboard yet.</b> '
                'Send the bias-correction code/results and they will be added here as a Before-vs-After view.</div>',
                unsafe_allow_html=True)
