# 🌦️ Anand · Kheda · Mahisagar Weather Dashboard

An interactive Streamlit dashboard comparing **block-level** vs **district-level**
weather data (2021–2023) for Anand, Kheda and Mahisagar districts, Gujarat.

Kept deliberately simple: **4 clear pages**, plain-English explanations on every
screen, and block data (🔵 blue) always shown separately from district data
(🟠 orange) so the two are never confused. Every chart that compares several
blocks or districts is shown **separately** (its own mini-chart or a
district/block picker) rather than overlapping lines that are hard to read.

## What's inside

| # | Page | What it shows, in one line |
|---|---|---|
| — | **Home** | Overview of the data + a quick chart to explore, one panel per district |
| 1 | **🔍 Block vs District** | Is your district's number a good stand-in for your own local area, or not? |
| 2 | **🗺️ Spatial Hotspots** | Which local areas are quietly always hotter / colder / wetter than the rest of their district |
| 3 | **🌡️ Extreme Events** | Real heatwave days, heavy-rain days, cold nights — block counts vs district counts, plus the **exact dates** of each spell |
| 4 | **🌾 Farm Advisory** | Heat-stress days, dry spells, monsoon start date — simple farming numbers, per block, one tab per number |

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
5. **Check your data is there.** The `data/` folder should already contain your
   3 yearly Excel files (2021, 2022, 2023), each with a `blockwise` and
   `districtwise` sheet. Any file name is fine as long as it ends in `.xlsx`
   and doesn't have the word "result" in it.
6. **Run the dashboard:**
   ```
   streamlit run app.py
   ```
   Your browser should open automatically at `http://localhost:8501`. If not, open
   that link yourself.

If it loads and you can click through the 5 pages, you're ready to publish it.

---

## Part 2 — Put the project on GitHub

GitHub is just an online folder for your code. Streamlit Cloud will read your
code from there to host the live dashboard, for free.

1. **Create a GitHub account** if you don't have one: https://github.com/join
2. **Create a new repository:**
   - Click the **+** icon (top right) → **New repository**
   - Name it something like `weather-dashboard`
   - Keep it **Public** (Streamlit Cloud's free tier needs this)
   - Don't check "Add a README" (you already have one) — click **Create repository**
3. **Upload your project.** Easiest way if you're not comfortable with git commands:
   - On the new repository page, click **"uploading an existing file"**
   - Drag your entire `weather-dashboard` folder's *contents* in (all files: `app.py`,
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

## Notes on the analyses

- **Monsoon onset** and **dry-spell/heat-stress thresholds** on the Farm Advisory
  page are simplified, transparent proxies (explained on the page itself) — not
  the official IMD methodology. Good for comparing blocks against each other,
  not for real agronomic decision-making.
- The thresholds used for heatwaves, heavy rain and cold nights on the Extreme
  Events page can be adjusted right there on the page.

## Project structure
```
weather-dashboard/
├── app.py                     # Home page
├── requirements.txt
├── README.md
├── .streamlit/config.toml     # theme
├── data/                      # your 3 yearly .xlsx files live here
├── utils/
│   ├── data_loader.py         # reads & cleans the Excel files
│   ├── metrics.py             # all the analysis calculations
│   └── style.py                # shared colors, plain-language boxes, CSS
└── pages/
    ├── 1_Block_vs_District.py
    ├── 2_Spatial_Hotspots.py
    ├── 3_Extreme_Events.py
    └── 4_Farm_Advisory.py
```

## What changed in this version
- Removed the Wind Patterns page — compass-style charts were the hardest to
  read at a glance and least essential to the core comparison.
- No chart overlaps several blocks'/districts' lines or bars on top of each
  other anymore — each gets its own mini-chart, or a district/block picker,
  so nothing turns into visual spaghetti.
- Extreme Events now shows the **exact start and end date** of every
  heatwave / heavy-rain / cold-night spell for a chosen block, not just a count.
- Farm Advisory is now 4 tabs (one number at a time) instead of one crowded
  page, and the technical "growing-degree" number is tucked into an
  "Advanced" tab since it's the hardest one to act on.
