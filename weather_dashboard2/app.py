"""Block vs District Weather Dashboard.   Run:  streamlit run app.py"""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from helpers import *   # data loading, metrics, styling, maps

st.set_page_config(page_title="Block vs District Weather", page_icon="🌦️", layout="wide")
inject_css()
df = need_data()
mapped = {f["properties"]["block"] for f in load_geojson()["features"]}


def page_compare():
    mapped = {f["properties"]["block"] for f in load_geojson()["features"]}

    hero("🗺️", "Block vs District", "Pick a district, then click any block on the map to compare it with the district.")

    # ── Step 1 ──
    step("1️⃣  Choose a district and a weather variable")
    a, b = st.columns([1.6, 1.6])
    district = a.radio("District", sorted(df["District"].unique()), horizontal=True, key="cmp_district")
    var_label = b.selectbox("Weather variable", list(LABELS), key="cmp_var")
    key, unit = LABELS[var_label], UNITS[LABELS[var_label]]

    d = df[df["District"] == district]
    ny = max(d["Year"].nunique(), 1)

    def agg_value(x):
        return x.sum() / ny if key == "Rain" else x.mean()

    blocks = sorted(d["Block"].unique())
    bval = {bl: agg_value(d[d.Block == bl][f"{key}_blk"]) for bl in blocks}
    dval = agg_value(d[f"{key}_dst"].groupby(d["Date"]).first())     # one district value per day
    diff = {bl: bval[bl] - dval for bl in blocks}
    what = "total per year" if key == "Rain" else "average"

    # keep selected block in session
    skey = f"sel_{district}"
    if st.session_state.get(skey) not in blocks:
        st.session_state[skey] = blocks[0]

    # ── Step 2: two maps ──
    step("2️⃣  Compare the maps – left: each block's own value, right: the one district value")
    allv = list(bval.values()) + [dval]
    zmin, zmax = min(allv), max(allv)
    if zmin == zmax:
        zmax = zmin + 1
    scale = {"Rain": "Blues", "Tmax": "YlOrRd", "Tmin": "PuBu", "RH-I": "Purples", "RH-II": "RdPu", "Wind": "Greens"}[key]
    m1, m2 = st.columns(2)
    with m1:
        fig1 = make_map(district, bval, scale, zmin, zmax, unit, f"📍 Blocks – {var_label} ({what})",
                        selected=st.session_state[skey],
                        hover={bl: f"Block value: {bval[bl]:.1f} {unit}<br>Gap vs district: {diff[bl]:+.1f} {unit}" for bl in blocks})
        ev = plot(fig1, key=f"map_{district}_{key}", select=True)
    with m2:
        flat = {bl: dval for bl in bval}
        fig2 = make_map(district, flat, scale, zmin, zmax, unit, f"🏙️ District – {var_label} ({what})",
                        hover={bl: f"District value: {dval:.1f} {unit}" for bl in blocks})
        plot(fig2, key=f"map2_{district}_{key}")
    tip("Same colour scale on both maps. If a block on the left is darker or lighter than the flat district map on the right, "
        "that block differs from the district. <b>Click a block on the left map</b> to select it.")
    miss = [bl for bl in blocks if bl not in mapped]
    if miss:
        st.caption(f"ℹ️ No boundary available for {', '.join(miss)} (very new talukas) – pick them from the list below.")

    click = clicked_block(ev)
    if click in blocks and st.session_state.get(f"lc_{district}") != click:
        st.session_state[skey] = click
        st.session_state[f"lc_{district}"] = click
        st.rerun()

    # ── gap bar chart ──
    gap = pd.DataFrame({"Block": list(diff), "Gap": list(diff.values())}).sort_values("Gap")
    gap["Direction"] = np.where(gap["Gap"] >= 0, "Block higher than district", "Block lower than district")
    fg = px.bar(gap, x="Gap", y="Block", orientation="h", color="Direction",
                color_discrete_map={"Block higher than district": "#F97316", "Block lower than district": "#2563EB"},
                labels={"Gap": f"Block − district ({unit})"}, title=f"How far is each block from the {district} value?")
    fg.update_layout(height=max(260, 32 * len(gap)), margin=dict(t=45, b=10), legend=dict(orientation="h", y=-0.2, title=None))
    plot(fg)

    # ── Step 3: side-by-side cards ──
    block = st.selectbox("3️⃣  Selected block (click the map or choose here)", blocks, key=skey)
    step(f"3️⃣  {block} (block)  vs  {district} (district)")
    bd = d[d.Block == block]

    def rows(sfx):
        out = []
        for k in VARIABLES.values():
            col = bd[f"{k}_{sfx}"]
            v = col.sum() / ny if k == "Rain" else col.mean()
            out.append((k, v))
        return dict(out)

    sb, sd = rows("blk"), rows("dst")

    def card(title, tag, color, vals, other=None):
        trs = ""
        for k in VARIABLES.values():
            name = "Rain / year" if k == "Rain" else {"Tmax": "Max temp", "Tmin": "Min temp", "RH-I": "Morning humidity",
                                                      "RH-II": "Afternoon humidity", "Wind": "Wind speed"}[k]
            gap_txt = "" if other is None else f" <span style='opacity:.8;font-weight:400'>({vals[k]-other[k]:+.1f})</span>"
            trs += f"<tr><td>{VAR_ICON[k]} {name}</td><td>{vals[k]:.1f} {UNITS[k]}{gap_txt}</td></tr>"
        return (f'<div class="card" style="background:{color}"><span class="pill">{tag}</span><h3>{title}</h3>'
                f'<table>{trs}</table></div>')

    c1, c2 = st.columns(2)
    c1.markdown(card(f"📍 {block}", "LOCAL BLOCK (gap vs district in brackets)", "linear-gradient(135deg,#7c3aed,#c026d3)", sb, sd),
                unsafe_allow_html=True)
    c2.markdown(card(f"🏙️ {district}", "WHOLE DISTRICT", "linear-gradient(135deg,#0284c7,#06b6d4)", sd), unsafe_allow_html=True)

    # ── plain-language verdicts ──
    step("🗣️  What does this mean in plain words?")
    tol_txt = {"Tmax": "±2 °C", "Tmin": "±2 °C", "RH-I": "±10 %", "RH-II": "±10 %", "Wind": "±3 km/h", "Rain": "same rain / no-rain call"}
    lines = []
    for k in VARIABLES.values():
        m = continuous_metrics(bd[f"{k}_blk"], bd[f"{k}_dst"], k)
        emoji, word, _ = verdict(m["Within"])
        direction = "" if abs(m["Bias"]) < 0.05 else (" The block is usually a bit <b>higher</b>." if m["Bias"] > 0 else " The block is usually a bit <b>lower</b>.")
        lines.append(f"{emoji} <b>{VAR_ICON[k]} {k}</b>: district is <b>{word}</b> – on {m['Within']:.0f}% of days it is within "
                     f"{tol_txt[k]} of the block (r = {m['Corr']:.2f}).{direction}")
    say("<br>".join(lines))

    # ── chart over time ──
    step("📈  Block and district month by month")
    s = bd[["Date", f"{key}_blk", f"{key}_dst"]].set_index("Date")
    s = s.resample("MS").sum() if key == "Rain" else s.resample("MS").mean()
    s = s.reset_index().melt("Date", var_name="Source", value_name=f"{var_label}")
    nb, nd = f"{block} (block)", f"{district} (district)"
    s["Source"] = s["Source"].map({f"{key}_blk": nb, f"{key}_dst": nd})
    ft = px.line(s, x="Date", y=var_label, color="Source", color_discrete_map={nb: BLOCK_COLOR, nd: DISTRICT_COLOR})
    ft.update_layout(height=380, legend=dict(orientation="h", y=1.12, title=None), margin=dict(t=30, b=10))
    plot(ft)


def page_reliable():
    hero("🏆", "Which one is reliable?", "A simple traffic-light check: can the district number stand in for a block?")

    step("1️⃣  Choose the area")
    area = st.radio("Area", ["All three districts"] + sorted(df["District"].unique()), horizontal=True, key="rel_area")
    d = df if area.startswith("All") else df[df["District"] == area]

    # ── scorecard ──
    step("2️⃣  Scorecard – how often is the district number 'close enough'?")
    sc = scorecard(d, [])
    TOL = {"Rain": "same rain / no-rain call", "Tmax": "within ±2 °C", "Tmin": "within ±2 °C", "RH-I": "within ±10 %",
           "RH-II": "within ±10 %", "Wind": "within ±3 km/h"}
    cols = st.columns(6)
    for col, (_, r) in zip(cols, sc.iterrows()):
        emoji, word, color = verdict(r["Within"])
        col.markdown(f'<div class="kpi" style="background:{VAR_COLOR[r.Variable]}"><span style="font-size:1.6rem">{VAR_ICON[r.Variable]}</span>'
                     f'<b>{r["Within"]:.0f}%</b>{r.Variable}<br><span style="font-size:.85rem">{emoji} {word}</span></div>',
                     unsafe_allow_html=True)
    tip("Each big number = % of days the district value is <b>close enough</b> to the block "
        "(temperature ±2 °C, humidity ±10 %, wind ±3 km/h, rain = same rain / no-rain call). "
        "🟢 85%+ very close · 🟡 65–85% roughly close · 🔴 below 65% often different.")

    view = sc[["Variable", "Within", "Corr", "MAE", "Bias"]].copy()
    view["Variable"] = [f"{VAR_ICON[v]} {v} ({UNITS[v]})" for v in view["Variable"]]
    view["Verdict"] = [verdict(w)[0] + " " + verdict(w)[1] for w in view["Within"]]
    view["Bias meaning"] = ["block higher than district" if b > 0.05 else "block lower than district" if b < -0.05 else "no steady gap"
                            for b in view["Bias"]]
    view = view.rename(columns={"Within": "Days close enough (%)", "Corr": "Moves together (r)", "MAE": "Typical gap", "Bias": "Average gap"})
    view = view[["Variable", "Verdict", "Days close enough (%)", "Moves together (r)", "Typical gap", "Average gap", "Bias meaning"]].round(2)
    table(view)
    say("<b>Moves together (r)</b> close to 1 means when the block gets hotter/wetter, the district number does too. "
        "<b>Typical gap</b> is the average size of the difference, in the variable's own unit. "
        "<b>Average gap</b> (block − district) shows whether the block is usually above (+) or below (−) the district.")

    # ── by block ──
    step("3️⃣  Which blocks does the district number describe best and worst?")
    bb = scorecard(d, ["District", "Block"])
    rank = bb.groupby(["District", "Block"])["Within"].mean().reset_index().sort_values("Within")
    fig = px.bar(rank, x="Within", y="Block", orientation="h", color="District", color_discrete_map=DIST_COLOR,
                 labels={"Within": "Average % of days close enough (all variables)"})
    fig.update_layout(height=max(320, 28 * len(rank)), margin=dict(t=10, b=10), legend=dict(orientation="h", y=1.08, title=None))
    plot(fig)
    w, b_ = rank.iloc[0], rank.iloc[-1]
    say(f"District value fits <b>{b_.Block}</b> best ({b_.Within:.0f}% of days close) and <b>{w.Block}</b> worst ({w.Within:.0f}%). "
        "Blocks at the bottom are where local weather differs most from the district picture.")

    # ── rainfall ──
    step("4️⃣  Rain: did the district number catch the rainy days?")
    rs = rain_scores(d["Rain_blk"], d["Rain_dst"])
    k1, k2, k3, k4 = st.columns(4)
    kpi(k1, "Rainy days caught", f"{rs['PoD']*100:.0f}%", "#2563EB")
    kpi(k2, "Rainy days missed", f"{rs['Miss']*100:.0f}%", "#EF4444")
    kpi(k3, "Dry days wrongly called rainy", f"{rs['POFD']*100:.0f}%", "#F59E0B")
    kpi(k4, "Overall skill score (HK)", f"{rs['HK']:.2f}", "#10B981")
    tip("Rainy day = 2.5 mm or more. The HK score is 1 for a perfect forecast and 0 for no skill. "
        "The district number rarely misses rain but often shows rain when a block stays dry.")

    # ── conclusion ──
    step("🏁  Overall conclusion")
    best = sc.sort_values("Within").iloc[-1]
    worst = sc.sort_values("Within").iloc[0]
    say(f"The district number follows the blocks well: correlation is {sc['Corr'].min():.2f}–{sc['Corr'].max():.2f} across variables. "
        f"It is most dependable for <b>{best.Variable}</b> ({best.Within:.0f}% of days close) and least for <b>{worst.Variable}</b> "
        f"({worst.Within:.0f}%). The district value is a smoothed average, so it is <b>stable but hides local differences</b>; "
        "the block data keeps that local detail. For decisions at farm level the block data is the more precise guide.")


def page_hotspots():
    hero("🔥", "Spatial Hotspots", "Which blocks are quietly always a bit higher or lower than the rest?")

    step("1️⃣  Choose what to look at")
    label = st.selectbox("Weather variable", list(LABELS), key="hot_var")
    key, unit = LABELS[label], UNITS[LABELS[label]]
    d = df
    ny = max(d["Year"].nunique(), 1)
    agg = d.groupby(["District", "Block"])[f"{key}_blk"].agg("sum" if key == "Rain" else "mean").reset_index(name="v")
    if key == "Rain":
        agg["v"] = agg["v"] / ny
    agg["gap"] = agg["v"] - agg["v"].mean()          # compared with the average of all 24 blocks
    lim = float(agg["gap"].abs().max()) or 1.0

    step("2️⃣  Map and ranking (red = higher than average, blue = lower)")
    c1, c2 = st.columns([1.2, 1])
    with c1:
        vals = dict(zip(agg["Block"], agg["gap"]))
        hov = {r.Block: f"{r.District}<br>Value: {r.v:.1f} {unit}<br>Vs average: {r.gap:+.1f} {unit}" for r in agg.itertuples()}
        fig = make_map(None, vals, "RdBu_r" if key not in ("Rain", "RH-I", "RH-II") else "BrBG", -lim, lim, unit,
                       f"{label}: block vs overall average", hover=hov, height=520)
        plot(fig)
    with c2:
        g = agg.sort_values("gap")
        fb = px.bar(g, x="gap", y="Block", orientation="h", color="District", color_discrete_map=DIST_COLOR,
                    labels={"gap": f"Gap vs average ({unit})"})
        fb.update_layout(height=520, margin=dict(t=10, b=10), legend=dict(orientation="h", y=1.06, title=None))
        plot(fb)

    hi, lo = agg.sort_values("gap").iloc[-1], agg.sort_values("gap").iloc[0]
    say(f"<b>Highest:</b> {hi.Block} ({hi.District}) is {hi.gap:+.1f} {unit} above the average block. "
        f"<b>Lowest:</b> {lo.Block} ({lo.District}) is {lo.gap:+.1f} {unit} below it.")
    tip("Galteshwar and Vaso have no boundary on the map but appear in the ranking.")


def page_charts():
    hero("🖼️", "Result Charts", "The comparison graphs from the project analysis, by season and year.")

    RES = Path(__file__).resolve().parent / "results"
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
    name = st.radio("Variable", list(FOLDERS), horizontal=True, key="chart_var")
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


tabs = st.tabs(["🗺️ Block vs District", "🏆 Which is Reliable?", "🔥 Spatial Hotspots", "🖼️ Result Charts"])
for tab, page in zip(tabs, [page_compare, page_reliable, page_hotspots, page_charts]):
    with tab:
        page()
