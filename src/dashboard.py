import streamlit as st
import pandas as pd
import joblib
import json
import folium
from streamlit_folium import st_folium
import plotly.express as px
from folium.plugins import HeatMap
import pdfkit
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="EnviroScan Dashboard",
    page_icon="🌍",
    layout="wide",
)

# --- DATA LOADING AND CACHING ---
@st.cache_data
def load_data():
    """Loads and prepares all necessary data."""
    df_locations = pd.read_csv("data/specific_locations_cleaned.csv")
    df_pollution = pd.read_csv("data/pollution_data.csv")

    # --- THE FIX IS HERE ---
    # Drop the empty 'city' column from the pollution data before merging
    if 'city' in df_pollution.columns:
        df_pollution = df_pollution.drop(columns=['city'])
    # ---------------------
    
    df = pd.merge(df_pollution, df_locations, left_on='location_id', right_on='id', how='left')

    def extract_coords(coord_str):
        try:
            valid_json_str = str(coord_str).replace("'", '"')
            coord_dict = json.loads(valid_json_str)
            return coord_dict.get('latitude'), coord_dict.get('longitude')
        except (TypeError, json.JSONDecodeError):
            return None, None

    df['latitude'], df['longitude'] = zip(*df['coordinates'].apply(extract_coords))
    df.dropna(subset=['latitude', 'longitude'], inplace=True)
    
    # Use modern syntax to avoid the warning
    df['city'] = df['city'].fillna('Unknown')
    
    pollutant_cols = ['pm2_5', 'pm10', 'no2', 'so2', 'o3', 'co', 'aqi']
    for col in pollutant_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].fillna(df[col].median())

    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)
    
    return df

@st.cache_resource
def load_model_and_scaler():
    """Loads the trained model and scaler."""
    model = joblib.load('pollution_source_model.joblib')
    scaler = joblib.load('data_scaler.joblib')
    return model, scaler

# Load all data and models
df = load_data()
model, scaler = load_model_and_scaler()

# --- PREDICTIONS ---
features_to_use = ['pm2_5', 'pm10', 'no2', 'so2', 'o3', 'co', 'aqi', 'latitude', 'longitude']
features_present = [f for f in features_to_use if f in df.columns]
X_prepared = df[features_present]
X_scaled = scaler.transform(X_prepared)
df['predicted_source'] = model.predict(X_scaled)
df['prediction_confidence'] = model.predict_proba(X_scaled).max(axis=1)
df['final_prediction'] = df.apply(
    lambda row: row['predicted_source'] if row['prediction_confidence'] >= 0.6 else 'Uncertain',
    axis=1
)

# --- DASHBOARD UI ---
st.title("🌍 EnviroScan: AI-Powered Pollution Source Identifier")
st.markdown("This dashboard provides real-time insights into air pollution levels and their predicted sources across various locations.")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Dashboard Filters")
city_options = sorted([city for city in df['city'].unique() if city != 'Unknown'])
selected_city = st.sidebar.selectbox("Select a City", options=city_options)

# The data is from a single day, so we just filter by city.
df_filtered = df[df['city'] == selected_city]
data_date = df_filtered['timestamp'].dt.date.iloc[0] if not df_filtered.empty else "N/A"

# --- MAIN CONTENT ---
if df_filtered.empty:
    st.error(f"No data available for {selected_city}.")
else:
    st.header(f"Pollution Overview for {selected_city} on {data_date.strftime('%B %d, %Y')}")
    avg_aqi = df_filtered['aqi'].mean()
    uncertain_pct = (df_filtered['final_prediction'] == 'Uncertain').mean() * 100
    col1, col2 = st.columns(2)
    col1.metric("Average Air Quality Index (AQI)", f"{avg_aqi:.2f}")
    col2.metric("Uncertain Predictions", f"{uncertain_pct:.1f}%")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Distribution of Predicted Sources")
        source_counts = df_filtered['final_prediction'].value_counts()
        fig_pie = px.pie(source_counts, values=source_counts.values, names=source_counts.index)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        st.subheader("Pollutant Trends (Hourly)")
        chart_data = df_filtered.set_index('timestamp')[['pm2_5', 'no2', 'so2']]
        st.line_chart(chart_data)

    st.header("Geospatial Pollution Map")
    map_center = [df_filtered['latitude'].mean(), df_filtered['longitude'].mean()]
    m = folium.Map(location=map_center, zoom_start=12, tiles="CartoDB positron")
    heat_data = df_filtered[['latitude', 'longitude', 'aqi']].values.tolist()
    HeatMap(heat_data, radius=15, name='AQI Heatmap').add_to(m)
    for _, row in df_filtered.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"<strong>{row['name']}</strong><br>Source: {row['final_prediction']}<br>Confidence: {row['prediction_confidence']:.2%}",
            tooltip=row['name']
        ).add_to(m)
    folium.LayerControl().add_to(m)
    st_folium(m, use_container_width=True)