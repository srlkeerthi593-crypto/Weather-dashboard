import streamlit as st
import plotly.express as px
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from utils.data_loader import load_blockwise
from utils.metrics import block_feature_table
from utils.style import inject_css, hero, plain_box, glossary_expander

st.set_page_config(page_title="Block Clustering", page_icon="🧩", layout="wide")
inject_css()
hero("🧩", "Grouping Areas by Real Weather", "Forget the official district map for a second — which blocks actually behave alike?", gradient=("#0EA5E9", "#67E8F9"))
plain_box(
    "This groups blocks purely by their weather patterns (temperature, rain, humidity, wind) using a "
    "technique called K-Means clustering — no knowledge of district boundaries is used. Then we check: "
    "<b>do the groups line up with the real districts, or cut across them?</b>"
)
glossary_expander()

block_df = load_blockwise()
feat = block_feature_table(block_df)

k = st.slider("🔢 How many groups should we look for?", 2, 6, 3)
feature_cols = ["tmax_mean", "tmin_mean", "rainfall_total", "rh1_mean", "rh2_mean", "wind_speed_mean"]
X = StandardScaler().fit_transform(feat[feature_cols])
km = KMeans(n_clusters=k, n_init=10, random_state=42)
feat["cluster"] = "Group " + (km.fit_predict(X) + 1).astype(str)

pca = PCA(n_components=2, random_state=42)
coords = pca.fit_transform(X)
feat["pc1"], feat["pc2"] = coords[:, 0], coords[:, 1]

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### 🎨 Colored by weather group (what the data says)")
    fig1 = px.scatter(feat, x="pc1", y="pc2", color="cluster", text="block", hover_data=["district"])
    fig1.update_traces(textposition="top center", marker=dict(size=13))
    fig1.update_layout(height=420, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    st.markdown("#### 🗺️ Colored by official district (what the map says)")
    fig2 = px.scatter(feat, x="pc1", y="pc2", color="district", text="block", hover_data=["cluster"])
    fig2.update_traces(textposition="top center", marker=dict(size=13))
    fig2.update_layout(height=420, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig2, use_container_width=True)

plain_box("Blocks placed close together behave similarly. Compare the two pictures: if the colors match up between them, districts = real weather groups. If not, some blocks are more similar to a different district than their own.")

st.divider()
st.markdown("### 🔗 Do the groups line up with districts?")
cross = pd.crosstab(feat["district"], feat["cluster"])
st.dataframe(cross, use_container_width=True)

mismatches = feat.groupby("district")["cluster"].nunique()
split_districts = mismatches[mismatches > 1].index.tolist()
if split_districts:
    plain_box(
        f"<b>{', '.join(split_districts)}</b> — blocks inside this district don't all behave the same way. "
        f"A single district-wide advisory would understate real local variation here.",
        icon="⚠️",
    )
else:
    st.success("✅ Every district's blocks landed in the same weather group — district boundaries match real weather behaviour well.")

with st.expander("📋 Raw numbers used for grouping"):
    st.dataframe(feat[["district", "block", "cluster"] + feature_cols], use_container_width=True, hide_index=True)
