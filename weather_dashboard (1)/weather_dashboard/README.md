# Weather Forecast Verification Dashboard
Run locally:  `pip install -r requirements.txt`  then  `streamlit run app.py`
Deploy: push this whole folder to GitHub (keep `results_final/`, `boundaries/`, `data/` next to `app.py`) and point Streamlit Cloud at `app.py`.

Pages: Overview · Map Comparison · Rainfall · Temperature/Humidity/Wind · District Comparison · Bias Correction

## Map Comparison files
- `boundaries/blocks.geojson` (24 blocks) and `districts.geojson` (3 districts): need properties `block` / `district` matching the Excel names.
  Built from the LGD sub-district layer by `prepare_boundaries.py`. To use your own boundary file, convert it to GeoJSON
  with those two property names and overwrite these files.
- `data/block_stats.csv`, `data/district_stats.csv`: pre-computed by `python prepare_map_data.py` from `data/Weather_*.xlsx`.
  Re-run it if the Excel data changes.
- Observed = blockwise sheet, Forecast = districtwise sheet. Map difference = Forecast − Block.
