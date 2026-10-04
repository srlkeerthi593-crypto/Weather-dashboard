import pandas as pd, numpy as np, json
V={"Rainfall":"Rainfall (mm)","Tmax":"Tmax (°C)","Tmin":"Tmin (°C)","RH-I":"RH-I (%)","RH-II":"RH-II (%)","Wind Speed":"Wind Speed (km/h)"}
Y=[2021,2022,2023]; S=["Pre-monsoon","Monsoon","Post-monsoon","Winter"]
def season(m): return "Pre-monsoon" if m in(3,4,5) else "Monsoon" if m in(6,7,8,9) else "Post-monsoon" if m in(10,11) else "Winter"
fr=[]
for y in Y:
    f=f"data/Weather_{y}_365days_Complete_Anand_Kheda_Mahisagar.xlsx"
    b=pd.read_excel(f,"blockwise");d=pd.read_excel(f,"districtwise")
    b["Date"]=pd.to_datetime(b["Date"]);d["Date"]=pd.to_datetime(d["Date"])
    m=b.merge(d.drop(columns=["Source"]),on=["Date","District"],suffixes=("_o","_f"));m["Year"]=y;fr.append(m)
df=pd.concat(fr);df["Month"]=df.Date.dt.month;df["Season"]=df.Date.dt.month.map(season)
def met(g,c):
    o,f=g[c+"_o"],g[c+"_f"];return [round(float(np.sqrt(((o-f)**2).mean())),3),round(float(o.corr(f)),3),round(float((o-f).mean()),3)]
out={"vars":list(V),"units":V,"metrics":{},"monthly":{},"blocks":{},"rain":{},"mapblocks":{}}
dists=["All"]+sorted(df.District.unique())
for k,c in V.items():
    for dn in dists:
        dd=df if dn=="All" else df[df.District==dn]
        for yn in ["All"]+Y:
            yy=dd if yn=="All" else dd[dd.Year==yn]
            for s in ["Annual"]+S:
                g=yy if s=="Annual" else yy[yy.Season==s]
                out["metrics"][f"{k}|{dn}|{yn}|{s}"]=met(g,c)
            out["monthly"][f"{k}|{dn}|{yn}"]=[[round(float(x),2) for x in yy.groupby("Month")[c+t].mean()] for t in("_o","_f")]
    for yn in ["All"]+Y:
        yy=df if yn=="All" else df[df.Year==yn]
        gb=yy.groupby(["District","Block"])
        out["blocks"][f"{k}|{yn}"]={f"{a}|{b}":[round(float(g[c+'_o'].mean()),2),round(float((g[c+'_o']-g[c+'_f']).mean()),2),round(float(np.sqrt(((g[c+'_o']-g[c+'_f'])**2).mean())),2)] for (a,b),g in gb}
for dn in dists:
    dd=df if dn=="All" else df[df.District==dn]
    for yn in ["All"]+Y:
        yy=dd if yn=="All" else dd[dd.Year==yn]
        for s in ["Annual"]+S:
            g=yy if s=="Annual" else yy[yy.Season==s]
            ro,rf=g["Rainfall (mm)_o"]>=2.5,g["Rainfall (mm)_f"]>=2.5
            YY,YN,NY,NN=[int(x) for x in((ro&rf).sum(),(ro&~rf).sum(),(~ro&rf).sum(),(~ro&~rf).sum())]
            out["rain"][f"{dn}|{yn}|{s}"]=[YY,YN,NY,NN]
        out.setdefault("rainshare",{})[f"{dn}|{yn}"]=[round(float(yy[yy.Season==s]["Rainfall (mm)_o"].sum()/max(len(yy.District.unique()),1)/max(yy.Block.nunique(),1)*0+yy[yy.Season==s]["Rainfall (mm)_o"].sum()),1) for s in S]
s=json.dumps(out,separators=(",",":"),allow_nan=True).replace("NaN","null");open("data.json","w").write(s)
print(sorted(df.groupby(["District","Block"]).size().index.tolist()));print(len(open("data.json").read())//1024,"KB")
