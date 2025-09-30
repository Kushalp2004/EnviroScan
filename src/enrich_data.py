import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

LOCATIONS_FILE = "data/specific_locations_cleaned.csv"
OUTPUT_FILE = "data/pollution_data.csv"
API_KEY = os.getenv("OPENWEATHER_API_KEY") # Ensure this matches your .env file
POLLUTANTS = ['pm2_5', 'pm10', 'no2', 'so2', 'o3', 'co']
SLEEP_TIME = 1

if not API_KEY:
    raise ValueError("No API key found. Please set OPENWEATHER_API_KEY in your .env file.")

# LOAD LOCATIONS
df_locations = pd.read_csv(LOCATIONS_FILE)

def extract_lat_lon(coord_str):
    try:
        # Safely evaluate string to dictionary
        coord_dict = eval(coord_str)
        return float(coord_dict['latitude']), float(coord_dict['longitude'])
    except:
        return None, None

df_locations['latitude'], df_locations['longitude'] = zip(*df_locations['coordinates'].map(extract_lat_lon))

# FUNCTION TO FETCH DATA (NOW WITH TIMESTAMP)
def fetch_latest_pollution(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if 'list' in data and len(data['list']) > 0:
                item = data['list'][0]
                components = item.get('components', {})
                aqi = item.get('main', {}).get('aqi')
                
                # ⭐ FIX: Capture the timestamp and convert it
                timestamp = datetime.fromtimestamp(item.get('dt', 0))
                
                measures = {p: components.get(p) for p in POLLUTANTS}
                measures['aqi'] = aqi
                measures['timestamp'] = timestamp # Add timestamp to the record
                return measures
        return {p: None for p in POLLUTANTS + ['aqi', 'timestamp']}
    except Exception as e:
        print(f"Error fetching data for {lat}, {lon}: {e}")
        return {p: None for p in POLLUTANTS + ['aqi', 'timestamp']}

# FETCH DATA FOR ALL LOCATIONS
results = []
print("Starting data enrichment (with timestamps)...")
for idx, row in df_locations.iterrows():
    loc_id, lat, lon = row.get("id"), row.get("latitude"), row.get("longitude")
    if pd.isnull(lat) or pd.isnull(lon):
        continue

    measures = fetch_latest_pollution(lat, lon)
    data = {'location_id': loc_id}
    data.update(measures)
    results.append(data)

    if (idx + 1) % 50 == 0:
        print(f"{idx + 1} of {len(df_locations)} locations processed...")
    time.sleep(SLEEP_TIME)

# CONVERT TO DATAFRAME & SAVE
pollution_df = pd.DataFrame(results)
pollution_df.to_csv(OUTPUT_FILE, index=False)
print(f"\n✅ Realtime pollution data with timestamps saved to {OUTPUT_FILE}")