"""Block-boundary maps (no map tiles needed, so they always load)."""
import plotly.graph_objects as go
from utils.data_loader import load_geojson


def make_map(district, values, colorscale, zmin, zmax, unit, title, selected=None, hover=None, height=470):
    """values: {block: number}. district=None -> draw all districts."""
    gj = load_geojson()
    feats = [f for f in gj["features"] if district is None or f["properties"]["district"] == district]
    feats = [f for f in feats if f["properties"]["block"] in values]
    geo = {"type": "FeatureCollection", "features": feats}
    blocks = [f["properties"]["block"] for f in feats]
    z = [values[b] for b in blocks]
    text = [(hover or {}).get(b, f"{values[b]:.1f} {unit}") for b in blocks]
    fig = go.Figure(go.Choropleth(
        geojson=geo, locations=blocks, z=z, featureidkey="properties.block", colorscale=colorscale,
        zmin=zmin, zmax=zmax, marker_line_color="white", marker_line_width=2, text=text,
        hovertemplate="<b>%{location}</b><br>%{text}<extra></extra>",
        colorbar=dict(title=unit, thickness=14, len=0.8)))
    if selected in blocks:   # dark outline on chosen block
        fig.add_trace(go.Choropleth(geojson=geo, locations=[selected], z=[0], featureidkey="properties.block",
                                    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
                                    marker_line_color="#111827", marker_line_width=4, hoverinfo="skip"))
    pts = [(f["properties"]["lon"], f["properties"]["lat"], f["properties"]["block"]) for f in feats]
    fig.add_trace(go.Scattergeo(lon=[p[0] for p in pts], lat=[p[1] for p in pts], text=[p[2] for p in pts],
                                mode="text", textfont=dict(size=11, color="#111827"), hoverinfo="skip", showlegend=False))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(title=dict(text=title, x=0.5, font=dict(size=16)), height=height,
                      margin=dict(l=0, r=0, t=45, b=0), paper_bgcolor="rgba(0,0,0,0)", dragmode=False)
    return fig


def clicked_block(event):
    try:
        pts = event.selection.points
        if pts:
            return pts[0].get("location")
    except Exception:
        pass
    return None
