import streamlit as st
import pandas as pd
import joblib
import json
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap, MarkerCluster
import plotly.express as px
import pdfkit
from datetime import datetime

# ------------------- PAGE CONFIG -------------------
st.set_page_config(
    page_title="EnviroScan Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------- CUSTOM CSS -------------------
st.markdown("""
<style>
    body { background-color: #111; color: #EEE; }
    .stMetric { background-color: #1c1c1c; padding: 12px; border-radius: 12px; }
    .stTabs [data-baseweb="tab-list"] button {
        font-size:16px;
        font-weight:bold;
        background-color:#1e1e1e;
        color: #EEE;
        border-radius: 8px;
        margin-right: 4px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #008080 !important;
        color: white !important;
    }
    .css-1d391kg { background-color: #1c1c1c; } /* sidebar */
</style>
""", unsafe_allow_html=True)

# ------------------- DATA LOADING -------------------
@st.cache_data
def load_data():
    df_locations = pd.read_csv("data/specific_locations_cleaned.csv")
    df_pollution = pd.read_csv("data/pollution_data.csv")

    if 'city' in df_pollution.columns:
        df_pollution = df_pollution.drop(columns=['city'])

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

    # Ensure city column exists
    if 'city' not in df.columns or df['city'].isnull().all():
        df['city'] = df['name']
    df['city'] = df['city'].fillna('Unknown')

    pollutant_cols = ['pm2_5', 'pm10', 'no2', 'so2', 'o3', 'co', 'aqi']
    for col in pollutant_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].fillna(df[col].median())

    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df.dropna(subset=['timestamp'], inplace=True)

    return df

@st.cache_resource
def load_model_and_scaler():
    model = joblib.load('pollution_source_model.joblib')
    scaler = joblib.load('data_scaler.joblib')
    return model, scaler

df = load_data()
model, scaler = load_model_and_scaler()

# ------------------- PREDICTIONS -------------------
features_to_use = ['pm2_5', 'pm10', 'no2', 'so2', 'o3', 'co', 'aqi', 'latitude', 'longitude']
X_prepared = df[features_to_use]
X_scaled = scaler.transform(X_prepared)
df['predicted_source'] = model.predict(X_scaled)
df['prediction_confidence'] = model.predict_proba(X_scaled).max(axis=1)
df['final_prediction'] = df.apply(
    lambda row: row['predicted_source'] if row['prediction_confidence'] >= 0.6 else 'Uncertain',
    axis=1
)

# ------------------- SIDEBAR FILTERS -------------------
st.sidebar.title("🛠 Control Panel")

selected_sources = st.sidebar.multiselect(
    "Pollution Sources",
    options=sorted(df['final_prediction'].unique()),
    default=sorted(df['final_prediction'].unique())
)

selected_cities = st.sidebar.multiselect(
    "Cities",
    options=sorted(df['city'].unique()),
    default=[]
)

pollutant_choice = st.sidebar.selectbox(
    "Primary Pollutant",
    ['pm2_5', 'pm10', 'no2', 'so2', 'o3', 'co']
)

st.sidebar.markdown(f"⏱ Last Updated: {datetime.now().strftime('%H:%M:%S')}")

# Filter data
df_filtered = df[df['final_prediction'].isin(selected_sources)]
if selected_cities:
    df_filtered = df_filtered[df_filtered['city'].isin(selected_cities)]

# ------------------- MAIN TABS -------------------
st.title("🌍 EnviroScan: AI-Powered Pollution Source Identifier")
tabs = st.tabs(["🗺 Map", "📊 Analytics", "⚠ Alerts", "🤖 Predict"])

# ------------------- MAP TAB -------------------
with tabs[0]:
    st.subheader("Pollution Sources Map")
    if df_filtered.empty:
        st.error("No data available for selected filters.")
    else:
        map_center = [df_filtered['latitude'].mean(), df_filtered['longitude'].mean()]
        m = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB dark_matter")

        # Heatmap
        heat_data = df_filtered[['latitude', 'longitude', pollutant_choice]].values.tolist()
        HeatMap(heat_data, radius=18, name=f"{pollutant_choice} Heatmap").add_to(m)

        # Clusters
        marker_cluster = MarkerCluster().add_to(m)
        for _, row in df_filtered.iterrows():
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=f"<b>{row['name']}</b><br>Source: {row['final_prediction']}<br>Confidence: {row['prediction_confidence']:.2%}",
                tooltip=row['city']
            ).add_to(marker_cluster)

        folium.LayerControl().add_to(m)
        st_folium(m, use_container_width=True, height=550)

# ------------------- ANALYTICS TAB -------------------
with tabs[1]:
    if df_filtered.empty:
        st.error("No data available for selected filters.")
    else:
        st.subheader("Pollution Analytics")
        col1, col2 = st.columns(2)
        avg_aqi = df_filtered['aqi'].mean()
        uncertain_pct = (df_filtered['final_prediction'] == 'Uncertain').mean() * 100
        col1.metric("Average AQI", f"{avg_aqi:.2f}")
        col2.metric("Uncertain Predictions", f"{uncertain_pct:.1f}%")

        col_a, col_b = st.columns(2)
        with col_a:
            source_counts = df_filtered['final_prediction'].value_counts()
            fig_pie = px.pie(
                names=source_counts.index, values=source_counts.values,
                color=source_counts.index, hole=0.3,
                title="Source Distribution"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_b:
            fig_line = px.line(
                df_filtered, x='timestamp', y=['pm2_5', 'pm10', 'no2', 'so2', 'o3', 'co'],
                title="Pollutant Trends (Hourly)"
            )
            st.plotly_chart(fig_line, use_container_width=True)

# ------------------- ALERTS TAB -------------------
with tabs[2]:
    st.subheader("⚠ Pollution Alerts")
    high_risk = df_filtered[df_filtered['aqi'] > 150]
    if high_risk.empty:
        st.success("✅ All clear! No locations exceeding AQI 150.")
    else:
        st.warning(f"⚠ {len(high_risk)} records exceed AQI 150 (Unhealthy).")
        st.dataframe(high_risk[['city', 'name', 'aqi', 'final_prediction']])

# ------------------- PREDICT TAB -------------------
with tabs[3]:
    st.subheader("Predict Pollution Source from CSV")
    uploaded_file = st.file_uploader("Upload a CSV with pollutant data", type=["csv"])
    if uploaded_file is not None:
        df_input = pd.read_csv(uploaded_file)
        if set(features_to_use).issubset(df_input.columns):
            X_in = scaler.transform(df_input[features_to_use])
            preds = model.predict(X_in)
            df_input['Predicted Source'] = preds
            st.dataframe(df_input)
            st.download_button(
                "📥 Download Predictions",
                df_input.to_csv(index=False).encode('utf-8'),
                "predictions.csv",
                "text/csv"
            )
        else:
            st.error(f"CSV must contain columns: {features_to_use}")
