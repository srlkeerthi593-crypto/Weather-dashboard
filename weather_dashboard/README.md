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
pages/1_District_Map_Compare.py   district → block map (click) → block vs district side by side
pages/2_Accuracy_and_Reliability.py  scorecard, verdicts, heat-map, rain skill, in-district spread
pages/3_Spatial_Hotspots.py       hotter / wetter / windier blocks
pages/4_Verification_Charts.py    your graphs from results/
pages/5_Bias_Correction.py        seasonal bias correction (added analysis)
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
