# Block vs District Weather Dashboard
Anand · Kheda · Mahisagar, 2021–2023 (Streamlit)

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
Deploy: push to GitHub → share.streamlit.io → main file `app.py`.

## Pages
- Block vs District (opens first): pick district + variable, two maps, click a block, compare
- Which is Reliable?: traffic-light scorecard
- Spatial Hotspots: blocks above / below average
- Result Charts: graphs from `results/`

## Folders
`data/` your 3 Excel files (unchanged) + `blocks.geojson` (block outlines from DataMeet, ODbL)
`results/` your PNG charts · `views/` page code · `utils/` helpers · `scripts/` how outlines were built

Block data = reference; district data = compared series; bias = block − district.
