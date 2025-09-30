🌍 EnviroScan: AI-Powered Pollution Source Identifier

EnviroScan is an AI-driven environmental monitoring system that collects, processes, and visualizes air quality data.
It predicts pollution sources (e.g., Vehicular, Industrial, Burning, Dust, Other) using machine learning,
and provides interactive geospatial maps and dashboards for decision-makers.

✨ Features

✅ Data Collection from:

OpenAQ
 — monitoring station locations

OpenWeatherMap
 — air pollution & weather API

✅ Preprocessing & Feature Engineering (cleaning, labeling, scaling)

✅ Source Classification using ML (Random Forest)

✅ Geospatial Mapping with layered heatmaps (PM2.5, PM10) + clustered source markers

✅ Interactive Dashboard (Streamlit):

Confidence-aware predictions (“Uncertain” if <60%)

Multi-pollutant trend charts (PM2.5, PM10, NO₂, SO₂, O₃, CO)

Pie charts for source distribution

Interactive heatmaps + source markers

Download filtered data as CSV or PDF

✅ Final Deliverables:

pollution_map.html (interactive map)

EnviroScan_Dashboard (Streamlit app)

report.pdf (project summary with diagrams/screenshots)

slides.pdf (presentation deck)

📂 Project Structure
EnviroScan/
│── data/
│   ├── global_locations_cleaned.csv
│   ├── specific_locations_cleaned.csv
│   ├── pollution_data.csv
│
│── src/
│   ├── get_locations.py        # Fetch locations from OpenAQ
│   ├── enrich_data.py          # Collect pollution data (OpenWeatherMap)
│   ├── create_map.py           # Train model + generate pollution_map.html
│   ├── dashboard.py            # Streamlit dashboard
│   ├── data_processing.ipynb   # Exploratory cleaning & feature engineering
│
│── pollution_map.html          # Interactive pollution heatmap
│── requirements.txt            # Project dependencies
│── report.pdf                  # Final project report (deliverable)
│── slides.pdf                  # 6-slide presentation (deliverable)

⚙️ Installation & Setup
1. Clone the Repository
git clone https://github.com/yourusername/enviro-scan.git
cd enviro-scan

2. Create Virtual Environment
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)

3. Install Dependencies
pip install -r requirements.txt

4. Install System Dependency for PDF Export

Required only if you want PDF downloads in dashboard.

# On Ubuntu/Debian
sudo apt-get install wkhtmltopdf

🚀 Running the Project
(A) Data Collection
python src/get_locations.py       # Fetch monitoring station locations
python src/enrich_data.py         # Fetch latest pollution data

(B) Generate Map & Train Model
python src/create_map.py


Produces:

pollution_source_model.joblib (trained model)

data_scaler.joblib (scaler)

pollution_map.html (interactive map with heatmaps + clusters)

(C) Launch Dashboard
streamlit run src/dashboard.py


Open in browser → http://localhost:8501

📊 Example Outputs
Pollution Map (pollution_map.html)

Layered heatmaps for PM2.5 and PM10

Color-coded source clusters (Industrial=🔴, Vehicular=🔵, Burning=🟠, Dust=🟢, Other=⚪, Uncertain=⚫)

Dashboard (dashboard.py)

Multi-pollutant trend chart

Source distribution pie chart

Interactive heatmap + markers

Data download as CSV/PDF