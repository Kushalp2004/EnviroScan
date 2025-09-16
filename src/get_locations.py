import os
import requests
import pandas as pd
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_URL = "https://api.openaq.org/v3/locations"
# Get the API key from environment variables
API_KEY = os.getenv("OPENAQ_API_KEY")

# Add a check to ensure the API key was loaded successfully
if not API_KEY:
    raise ValueError("No API key found. Please set OPENAQ_API_KEY in your .env file.")

page = 1
limit = 100
# Initial hardcoded locations
all_locations_data = [
    # Manually adding some major cities as they might not have government monitors
    {'id': 'manual-delhi', 'name': 'Delhi', 'city': 'Delhi', 'country': 'IN', 'coordinates': {'latitude': 28.6139, 'longitude': 77.2090}},
    {'id': 'manual-mumbai', 'name': 'Mumbai', 'city': 'Mumbai', 'country': 'IN', 'coordinates': {'latitude': 19.0760, 'longitude': 72.8777}},
    {'id': 'manual-bangalore', 'name': 'Bangalore', 'city': 'Bangalore', 'country': 'IN', 'coordinates': {'latitude': 12.9716, 'longitude': 77.5946}}
]


headers = {"X-API-Key": API_KEY}

while True:
    # An approximate bounding box for India: [West, South, East, North]
    INDIA_BBOX = "68.1,8.0,97.4,37.1"

    params = {"bbox": INDIA_BBOX, "limit": limit, "page": page, "entity": "government"} # Fetching government monitors
    try:
        resp = requests.get(BASE_URL, headers=headers, params=params, timeout=20)

        if resp.status_code == 429:
            print("Rate limit hit. Waiting 10 seconds...")
            time.sleep(10)
            continue
        elif resp.status_code != 200:
            print(f"Error fetching data: {resp.status_code} - {resp.text}")
            break

        data = resp.json()
        results = data.get("results", [])
        if not results:
            print("No more results to fetch.")
            break

        all_locations_data.extend(results)
        print(f"Page {page} fetched, total locations so far: {len(all_locations_data)}")
        page += 1
        time.sleep(1) # Be respectful of the API rate limits

    except requests.exceptions.RequestException as e:
        print(f"A network error occurred: {e}")
        break


# Flatten the nested JSON data and save to CSV
flat_locations = []
for loc in all_locations_data:
    flat_loc = {
        'id': loc.get('id'),
        'name': loc.get('name'),
        'city': loc.get('city'),
        'country': loc.get('country'),
        'coordinates': loc.get('coordinates') # Keep coordinates as a string representation of a dict
    }
    flat_locations.append(flat_loc)


df = pd.DataFrame(flat_locations)
# Remove potential duplicates based on ID, keeping the first instance
df.drop_duplicates(subset='id', keep='first', inplace=True)

df.to_csv("data/global_locations_cleaned.csv", index=False)
print(f"Saved {len(df)} unique locations to data/global_locations_cleaned.csv")