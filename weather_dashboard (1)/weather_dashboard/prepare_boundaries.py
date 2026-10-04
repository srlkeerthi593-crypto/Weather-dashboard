"""One-off: build boundaries/blocks.geojson + districts.geojson from the LGD sub-district layer.
Source: ramSeraph/indian_admin_boundaries (LGD_Subdistricts.parquet). Replace the output files with your own
shapefile-converted GeoJSON any time – only the property names 'block' and 'district' matter."""
import geopandas as gpd
SRC = "LGD_Subdistricts.parquet"
g = gpd.read_parquet(SRC)
g = g[g.stname.str.upper().str.contains("GUJARAT") & g.dtname.isin(["Anand", "Kheda", "Mahisagar"])].copy()
g["block"] = g.sdtname.replace({"Anand Rural": "Anand"})
g["district"] = g.dtname
g = g[["block", "district", "geometry"]]
g["geometry"] = g.geometry.simplify(0.0007, preserve_topology=True)
g.to_file("boundaries/blocks.geojson", driver="GeoJSON", COORDINATE_PRECISION=4)
d = g.dissolve(by="district").reset_index()[["district", "geometry"]]
d.to_file("boundaries/districts.geojson", driver="GeoJSON", COORDINATE_PRECISION=4)
print(len(g), "blocks,", len(d), "districts")
