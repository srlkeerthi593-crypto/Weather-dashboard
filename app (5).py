import json, glob, os
from pathlib import Path
import streamlit as st, plotly.express as px, plotly.graph_objects as go, pandas as pd
st.set_page_config("Weather Forecast Verification", "🌦️", layout="wide")
st.markdown("""<style>.stApp{background:linear-gradient(135deg,#0b1e3a,#0f5c6e);color:#eef6fb}
[data-testid=stSidebar]{background:#0b1e3a}h1,h2,h3,label,p,span,div{color:#eef6fb}
[data-testid=stMetricValue]{color:#ffb703}</style>""", unsafe_allow_html=True)
BASE = Path(__file__).resolve().parent
_dj = BASE / "data.json"
if not _dj.exists():
    st.error(f"data.json not found at {_dj}. Upload data.json to the same GitHub folder as app.py."); st.stop()
D = json.load(open(_dj))
XY = {"Anand|Anand":(72.95,22.56),"Anand|Anklav":(72.99,22.38),"Anand|Borsad":(72.90,22.41),"Anand|Khambhat":(72.62,22.31),"Anand|Petlad":(72.80,22.48),"Anand|Sojitra":(72.78,22.55),"Anand|Tarapur":(72.67,22.40),"Anand|Umreth":(73.10,22.70),"Kheda|Galteshwar":(73.13,22.93),"Kheda|Kapadvanj":(73.07,23.02),"Kheda|Kathlal":(72.95,22.87),"Kheda|Kheda":(72.68,22.75),"Kheda|Mahudha":(72.92,22.82),"Kheda|Matar":(72.64,22.69),"Kheda|Mehmedabad":(72.76,22.82),"Kheda|Nadiad":(72.86,22.69),"Kheda|Thasra":(73.20,22.83),"Kheda|Vaso":(72.78,22.72),"Mahisagar|Balasinor":(73.34,22.95),"Mahisagar|Kadana":(73.78,23.30),"Mahisagar|Khanpur":(73.50,23.35),"Mahisagar|Lunawada":(73.61,23.13),"Mahisagar|Santrampur":(73.84,23.17),"Mahisagar|Virpur":(73.55,22.91)}
SS = ["Pre-monsoon","Monsoon","Post-monsoon","Winter"]; DS = ["Anand","Kheda","Mahisagar"]
PAL = ["#ffb703","#2ec4b6","#8ecae6","#fb6f92","#b8f2a0"]
def style(fig): return fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(255,255,255,.06)",font_color="#eef6fb",margin=dict(t=40,b=10))

st.title("🌦️ Weather Forecast Verification")
st.caption("Observed (block-wise) vs Forecast (district-wise) · Anand · Kheda · Mahisagar · 2021–2023")
c = st.sidebar
v = c.selectbox("Parameter", D["vars"]); d = c.selectbox("District", ["All"]+DS)
y = c.selectbox("Year", ["All","2021","2022","2023"]); s = c.selectbox("Season", ["Annual"]+SS)
M = lambda v_,d_,y_,s_: D["metrics"][f"{v_}|{d_}|{y_}|{s_}"]
st.info(f"**{D['units'][v]}** · {d} · {y} · {s}.  RMSE = typical error size · Correlation = how well ups/downs match · Bias = average over/under-forecast (Obs − Forecast).")

# ---------- Block Explorer (top section): pick a district, click a block ----------
st.markdown("## 🗺️ Block Explorer")
bd = st.selectbox("Select district", DS, key="bd")
bk0 = D["blocks"][f"{v}|{y}"]
bdf = pd.DataFrame([{"Block":k.split("|")[1],"lon":XY[k][0],"lat":XY[k][1],"Observed":a[0],"Bias":a[1],"RMSE":a[2]} for k,a in bk0.items() if k.startswith(bd+"|")]).reset_index(drop=True)
bdf["Forecast"] = (bdf.Observed - bdf.Bias).round(2)
mcol, pcol = st.columns([3,2])
with mcol:
    show = st.radio("Colour blocks by", ["Observed","Bias","RMSE"], horizontal=True, key="bshow")
    bfig = px.scatter_mapbox(bdf,lat="lat",lon="lon",color=show,hover_name="Block",hover_data={"lat":False,"lon":False,"Observed":True,"Forecast":True,"Bias":True,"RMSE":True},color_continuous_scale="RdYlBu_r",zoom=9.2,height=460,mapbox_style="carto-darkmatter",center=dict(lat=bdf.lat.mean(),lon=bdf.lon.mean()))
    bfig.update_traces(marker=dict(size=26))
    st.caption("👆 Click a block circle to see its values")
    picked = None
    try:
        ev = st.plotly_chart(style(bfig), use_container_width=True, on_select="rerun", selection_mode="points", key=f"bmap_{bd}_{v}_{y}")
        if ev and ev.selection.points: picked = bdf.Block[ev.selection.points[0]["point_index"]]
    except TypeError:
        st.plotly_chart(style(bfig), use_container_width=True)
names = list(bdf.Block)
with pcol:
    blk = st.selectbox("Block (or choose here)", names, index=names.index(picked) if picked in names else 0, key=f"bsel_{bd}_{v}_{y}_{picked}")
    r = bdf[bdf.Block==blk].iloc[0]
    st.markdown(f"### {blk} — {bd}")
    q1, q2 = st.columns(2); q1.metric("Observed (avg)", r.Observed); q2.metric("Forecast (avg)", r.Forecast)
    q3, q4 = st.columns(2); q3.metric("Bias (Obs − Fcst)", r.Bias); q4.metric("RMSE", r.RMSE)
    st.caption(f"{D['units'][v]} · {y if y!='All' else '2021–2023'} · parameter and year come from the left sidebar")
    st.plotly_chart(style(px.bar(bdf,x="Block",y=show,color=bdf.Block==blk,color_discrete_sequence=["#8ecae6","#ffb703"],title=f"{bd}: all blocks by {show}").update_layout(showlegend=False,height=260)),use_container_width=True)
st.divider()
tabs = st.tabs(["📊 Overview","🗺️ Block Map","🏙️ District Comparison","🌧️ Rain Verification","🖼️ Result Charts"])

with tabs[0]:
    m = M(v,d,y,s); k = st.columns(3)
    k[0].metric("RMSE (lower = better)", m[0]); k[1].metric("Correlation (higher = better)", m[1]); k[2].metric("Mean Bias", m[2])
    mo = D["monthly"][f"{v}|{d}|{y}"]; ML = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    a, b, c3 = st.columns(3)
    a.plotly_chart(style(px.line(pd.DataFrame({"Month":ML,"Observed":mo[0],"Forecast":mo[1]}),x="Month",y=["Observed","Forecast"],title="Monthly average",color_discrete_sequence=PAL)),use_container_width=True)
    b.plotly_chart(style(px.bar(x=SS,y=[M(v,d,y,q)[0] for q in SS],title="RMSE by season",color=SS,color_discrete_sequence=PAL).update_layout(showlegend=False)),use_container_width=True)
    c3.plotly_chart(style(px.pie(names=SS,values=D["rainshare"][f"{d}|{y}"],title="Rainfall share by season",color_discrete_sequence=PAL)),use_container_width=True)

with tabs[1]:
    mi = {"Average observed value":0,"Mean bias (Obs − Fcst)":1,"RMSE":2}; pick = st.radio("Map shows", list(mi), horizontal=True)
    bk = D["blocks"][f"{v}|{y}"]
    df = pd.DataFrame([{"Block":k.split("|")[1],"District":k.split("|")[0],"lon":XY[k][0],"lat":XY[k][1],"Value":a[mi[pick]]} for k,a in bk.items()])
    if d != "All": df = df[df.District==d]
    fig = px.scatter_mapbox(df,lat="lat",lon="lon",color="Value",size=[14]*len(df),hover_name="Block",hover_data=["District","Value"],text="Block",color_continuous_scale="RdYlBu_r",zoom=8.2 if d=="All" else 9,height=560,mapbox_style="carto-darkmatter")
    st.plotly_chart(style(fig),use_container_width=True)

with tabs[2]:
    a, b = st.columns(2)
    for i,(nm,col) in enumerate([("RMSE",0),("Correlation",1),("Mean bias",2)]):
        (a if i%2==0 else b).plotly_chart(style(px.bar(x=DS,y=[M(v,q,y,s)[col] for q in DS],color=DS,title=nm+" by district",color_discrete_sequence=PAL).update_layout(showlegend=False)),use_container_width=True)
    b.plotly_chart(style(px.pie(names=DS,values=[M(v,q,y,s)[0] for q in DS],hole=.4,title="Share of total error (RMSE)",color_discrete_sequence=PAL)),use_container_width=True)

with tabs[3]:
    YY,YN,NY,NN = D["rain"][f"{d}|{y}|{s}"]; n = YY+YN+NY+NN; p = lambda a,b: f"{100*a/b:.1f}%" if b else "–"
    a, b = st.columns(2)
    a.plotly_chart(style(px.pie(names=["Hit","Miss","False alarm","Correct no-rain"],values=[YY,YN,NY,NN],hole=.45,title="Rain ≥ 2.5 mm: forecast outcome",color_discrete_sequence=["#2ec4b6","#fb6f92","#ffb703","#8ecae6"])),use_container_width=True)
    b.markdown(f"### Skill scores\n- Ratio score: **{p(YY+NN,n)}**\n- PoD (hit rate): **{p(YY,YY+YN)}**\n- Miss rate: **{p(YN,YY+YN)}**\n- False alarm ratio: **{p(NY,YY+NY)}**\n- CSI: **{p(YY,YY+YN+NY)}**")

with tabs[4]:
    folder = v.replace(" ","")
    files = sorted(glob.glob(str(BASE/"results_final"/folder/"*.png")))+sorted(glob.glob(str(BASE/"results_final"/folder/"*"/"*.png")))
    cols = st.columns(2)
    for i,f in enumerate(files): cols[i%2].image(f, caption=os.path.basename(f))
