# 🌦️ Anand · Kheda · Mahisagar Weather Dashboard

An interactive Streamlit dashboard comparing **block-level** vs **district-level**
weather data (2021–2023) for Anand, Kheda and Mahisagar districts, Gujarat.

## What's inside

| Page | What it shows |
|---|---|
| **Home** | Dataset overview, quick trend explorer |
| **🔍 Block vs District** | RMSE / Correlation / Bias — how well district data represents each block |
| **🗺️ Spatial Hotspots** | Which blocks are consistently hotter/cooler/wetter than their own district average |
| **🌡️ Extreme Events** | Heatwave days, heavy-rain days, cold nights — block counts vs district counts |
| **🌾 Agro-Advisory** | Heat-stress days, dry spells, monsoon onset, growing-degree-days, per block |
| **🚨 Anomaly Detector** | Frozen values, sudden jumps, rain-with-no-cloud data-quality flags |
| **🧩 Block Clustering** | Groups blocks by weather behaviour (K-Means) and checks against district boundaries |
| **🌬️ Wind Rose** | Wind direction/speed patterns, block-aggregated vs district file |
| **📈 Seasonal Skill** | Whether block-vs-district disagreement grows in monsoon, shrinks in winter |
| **🤖 Data Fusion Forecast** | Does a model blending block + district data beat either alone? |

---

## Part 1 — Run it on your own computer first (recommended)

1. **Install Python** (3.10 or newer) if you don't have it: https://www.python.org/downloads/
2. **Open a terminal** inside this folder (`weather-dashboard/`).
3. **Create a virtual environment** (keeps this project's packages separate):
   ```
   python -m venv venv
   ```
   Activate it:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. **Install the required packages:**
   ```
   pip install -r requirements.txt
   ```
5. **Add your data.** Put your 3 yearly Excel files (2021, 2022, 2023 — each with a
   `blockwise` and `districtwise` sheet) inside the `data/` folder. Any file name is
   fine as long as it ends in `.xlsx` and doesn't have the word "result" in it.
6. **Run the dashboard:**
   ```
   streamlit run app.py
   ```
   Your browser should open automatically at `http://localhost:8501`. If not, open
   that link yourself.

If it loads and you can click through the sidebar pages, you're ready to publish it.

---

## Part 2 — Put the project on GitHub

GitHub is just an online folder for your code. Streamlit Cloud will read your
code from there to host the live dashboard.

1. **Create a GitHub account** if you don't have one: https://github.com/join
2. **Create a new repository:**
   - Click the **+** icon (top right) → **New repository**
   - Name it something like `weather-dashboard`
   - Keep it **Public** (Streamlit Cloud's free tier needs this, unless you pay for private app hosting)
   - Don't check "Add a README" (you already have one) — click **Create repository**
3. **Upload your project.** Easiest way if you're not comfortable with git commands:
   - On the new repository page, click **"uploading an existing file"**
   - Drag your entire `weather-dashboard` folder's contents in (all files: `app.py`,
     `requirements.txt`, `README.md`, `.gitignore`, the `pages/` folder, `utils/`
     folder, `.streamlit/` folder, and your `data/` folder with the 3 Excel files)
   - Scroll down, write a message like "Initial dashboard", click **Commit changes**

   **Or, if you're comfortable with a terminal**, from inside the `weather-dashboard` folder:
   ```
   git init
   git add .
   git commit -m "Initial dashboard"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/weather-dashboard.git
   git push -u origin main
   ```
4. **Double-check** your repository on GitHub actually shows the `data/` folder
   with your 3 Excel files inside it — the app can't work without them.

---

## Part 3 — Deploy for free on Streamlit Community Cloud

1. Go to **https://share.streamlit.io** and click **"Sign up"** (sign in with your
   GitHub account — this links the two automatically).
2. Click **"Create app"** (or "New app").
3. Choose **"Deploy a public app from GitHub"**.
4. Fill in:
   - **Repository:** `YOUR-USERNAME/weather-dashboard`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Click **"Deploy"**.
6. Wait 1–3 minutes while it installs the packages from `requirements.txt` and
   starts the app. You'll get a live public link like:
   `https://your-app-name.streamlit.app`
7. Share that link with your professor / anyone — it updates automatically every
   time you push new changes to the GitHub repository.

### If something goes wrong on Streamlit Cloud
- Click **"Manage app"** (bottom right of your app) → **"Logs"** to see the error.
- The most common issue: the `data/` folder or Excel files weren't uploaded to
  GitHub, or a package is missing from `requirements.txt`.

---

## Notes on the "beyond the task" analyses

- **Monsoon onset** and **dry-spell/heat-stress thresholds** are simplified,
  transparent proxies (documented on the Agro-Advisory page itself) — not the
  official IMD methodology. Good for comparing blocks against each other, not
  for real agronomic decision-making.
- **Clustering** uses K-Means on standardized yearly averages (temperature,
  rainfall, humidity, wind) — try different values of *k* on that page.
- **Data Fusion Forecast** trains a small Random Forest per session (not
  pre-saved), so it will take a few seconds to run each time you open that page.

## Project structure
```
weather-dashboard/
├── app.py                     # Home page
├── requirements.txt
├── README.md
├── .streamlit/config.toml     # theme
├── data/                      # put your 3 yearly .xlsx files here
├── utils/
│   ├── data_loader.py         # reads & cleans the Excel files
│   └── metrics.py             # all the analysis calculations
└── pages/
    ├── 1_Block_vs_District.py
    ├── 2_Spatial_Hotspots.py
    ├── 3_Extreme_Events.py
    ├── 4_Agro_Advisory.py
    ├── 5_Anomaly_Detector.py
    ├── 6_Block_Clustering.py
    ├── 7_Wind_Rose.py
    ├── 8_Seasonal_Skill.py
    └── 9_Data_Fusion_Forecast.py
```
