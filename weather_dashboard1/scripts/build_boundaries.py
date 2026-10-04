"""
One-off helper: builds data/blocks.geojson (block = taluka polygons) from the
DataMeet Gujarat village boundaries (gj.geojson, ODbL licence).
Download first:
https://raw.githubusercontent.com/datameet/indian_village_boundaries/master/gj/gj.geojson
Usage: python scripts/build_boundaries.py path/to/gj.geojson
"""
import sys
import geopandas as gpd

BLOCKS = {
    "Anand": ["Anand","Anklav","Borsad","Khambhat","Petlad","Sojitra","Tarapur","Umreth"],
    "Kheda": ["Galteshwar","Kapadvanj","Kathlal","Kheda","Mahudha","Matar","Mehmedabad","Nadiad","Thasra","Vaso"],
    "Mahisagar": ["Balasinor","Kadana","Khanpur","Lunawada","Santrampur","Virpur"],
}
g = gpd.read_file(sys.argv[1])
g = g[g.SUB_DISTRICT.isin([b for v in BLOCKS.values() for b in v])
      & g.DISTRICT.isin(["Anand", "Kheda", "Panch Mahals"])]
t = g.dissolve(by="SUB_DISTRICT").reset_index()
rows = []
for dist, blocks in BLOCKS.items():
    for b in blocks:
        r = t[t.SUB_DISTRICT == b]
        if len(r):
            rows.append({"block": b, "district": dist, "geometry": r.geometry.iloc[0]})
out = gpd.GeoDataFrame(rows, crs=g.crs)
out["geometry"] = out.geometry.simplify(0.002, preserve_topology=True)
c = out.geometry.centroid
out["lon"], out["lat"] = c.x.round(4), c.y.round(4)
out.to_file("data/blocks.geojson", driver="GeoJSON")
print(out[["block", "district"]].to_string())
