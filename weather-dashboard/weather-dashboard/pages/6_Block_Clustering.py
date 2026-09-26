import streamlit as st
import plotly.express as px
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from utils.data_loader import load_blockwise
from utils.metrics import block_feature_table

st.set_page_config(page_title="Block Clustering", page_icon="🧩", layout="wide")
st.title("🧩 Clustering Blocks by Weather Behaviour")

st.markdown(
    """
Instead of assuming administrative district boundaries reflect real weather
patterns, this page **groups blocks purely by their weather data** (average
max/min temperature, rainfall, humidity, wind speed) using K-Means
clustering, then checks: **do the resulting groups match the district
boundaries, or cut across them?**

If a block's weather-based cluster doesn't match its official district, that
block is more similar to blocks in a *different* district than to its own
neighbours.
"""
)

block_df = load_blockwise()
feat = block_feature_table(block_df)

k = st.slider("Number of clusters (k)", 2, 6, 3)

feature_cols = ["tmax_mean", "tmin_mean", "rainfall_total", "rh1_mean", "rh2_mean", "wind_speed_mean"]
X = StandardScaler().fit_transform(feat[feature_cols])

km = KMeans(n_clusters=k, n_init=10, random_state=42)
feat["cluster"] = km.fit_predict(X).astype(str)

pca = PCA(n_components=2, random_state=42)
coords = pca.fit_transform(X)
feat["pc1"], feat["pc2"] = coords[:, 0], coords[:, 1]

col1, col2 = st.columns(2)
with col1:
    st.subheader("Colored by weather cluster")
    fig1 = px.scatter(
        feat, x="pc1", y="pc2", color="cluster", text="block",
        hover_data=["district"], title="Blocks grouped by weather similarity",
    )
    fig1.update_traces(textposition="top center", marker=dict(size=12))
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    st.subheader("Colored by official district")
    fig2 = px.scatter(
        feat, x="pc1", y="pc2", color="district", text="block",
        hover_data=["cluster"], title="Same blocks, colored by administrative district",
    )
    fig2.update_traces(textposition="top center", marker=dict(size=12))
    st.plotly_chart(fig2, use_container_width=True)

st.caption(
    "Axes are the top 2 principal components of the standardized weather "
    "features (not directly interpretable units — position/grouping is what matters)."
)

st.divider()
st.subheader("Do clusters line up with districts?")
cross = pd.crosstab(feat["district"], feat["cluster"])
st.dataframe(cross, use_container_width=True)

mismatches = feat.groupby("district")["cluster"].nunique()
split_districts = mismatches[mismatches > 1].index.tolist()
if split_districts:
    st.warning(
        f"📌 **{', '.join(split_districts)}** district(s) split across more than one "
        f"weather cluster — meaning blocks inside that district don't all behave "
        f"the same way, so a single district-level advisory understates real variation."
    )
else:
    st.success("Every district's blocks landed in the same cluster — district boundaries match weather behaviour well here.")

with st.expander("See the raw feature table used for clustering"):
    st.dataframe(feat[["district", "block", "cluster"] + feature_cols], use_container_width=True, hide_index=True)
