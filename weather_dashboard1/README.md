# Block vs District Weather Dashboard
Anand · Kheda · Mahisagar, 2021–2023 (Streamlit)

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Community Cloud)
Push this folder to GitHub → share.streamlit.io → New app → pick the repo, main file `app.py`.

## Folder layout
```
app.py                         home page
pages/1_Block_vs_District.py   pick district -> 2 maps -> click block -> compare
pages/2_Which_is_Reliable.py   traffic-light scorecard
pages/3_Spatial_Hotspots.py    blocks higher/lower than average
pages/4_Result_Charts.py       your graphs from results/
pages/5_Bias_Correction.py     simple bias correction
utils/                         data loading, metrics, styling
data/                          3 yearly Excel files + blocks.geojson (block boundaries)
results/                       PNG charts from results_final.zip
scripts/build_boundaries.py    how blocks.geojson was made
```

## Method
Block data = reference, district data = compared series. Bias = block − district.
Rain skill uses a 2.5 mm threshold (ratio, HK, PoD, POFD, miss rate, CSI, FAR).

## Credits
Block boundaries: DataMeet Indian Village Boundaries (Gujarat), ODbL, dissolved to talukas.
Galteshwar and Vaso are newer talukas without a polygon in that file; they work everywhere except on the map.
