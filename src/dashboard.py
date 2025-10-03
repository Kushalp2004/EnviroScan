import streamlit as st
import pandas as pd
import joblib
import json
import folium
from streamlit_folium import st_folium
import plotly.express as px
from folium.plugins import HeatMap
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="EnviroScan Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUTURISTIC STYLES ---
st.markdown("""
    <style>
        body {
            background-color: #0e1117;
            color: #ffffff;
            font-family: 'Roboto Mono', monospace;
        }
        .stMetric {
            background: rgba(20, 20, 20, 0.7);
            border: 1px solid #2e2e2e;
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0px 0px 8px rgba(0,255,255,0.2);
        }
        .stButton button {
            background: linear-gradient(90deg, #00c6ff, #0072ff);
            color: white;
            border-radius: 8px;
            border: none;
            font-weight: bold;
        }
        .css-1d391kg, .css-1dp5vir {
            background-color: #111 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
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
        except Exception:
            return None, None

    df['latitude'], df['longitude'] = zip(*df['coordinates'].apply(extract_coords))
    df.dropna(subset=['latitude', 'longitude'], inplace=True)

    # ✅ Fix city handling
    df['city'] = df['city'].fillna(df['name'])   # fallback if city missing
    df['city'] = df['city'].astype(str)

    pollutant_cols = ['pm2_5', 'pm10', 'no2', 'so2', 'o3', 'co', 'aqi']
    for col in pollutant_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].fillna(df[col].median())

    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)

    return df

@st.cache_resource
def load_model_and_scaler():
    model = joblib.load('pollution_source_model.joblib')
    scaler = joblib.load('data_scaler.joblib')
    return model, scaler

# --- LOAD DATA & MODEL ---
df = load_data()
model, scaler = load_model_and_scaler()

features = ['pm2_5', 'pm10', 'no2', 'so2', 'o3', 'co', 'aqi', 'latitude', 'longitude']
X_scaled = scaler.transform(df[features])
df['predicted_source'] = model.predict(X_scaled)
df['prediction_confidence'] = model.predict_proba(X_scaled).max(axis=1)
df['final_prediction'] = df.apply(
    lambda row: row['predicted_source'] if row['prediction_confidence'] >= 0.6 else 'Uncertain',
    axis=1
)

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.title("🛠 Control Panel")

# ✅ Fixed refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Auto refresh every 5 min
st_autorefresh(interval=5 * 60 * 1000, key="autorefresh")

sources = st.sidebar.multiselect("Pollution Sources", options=df['final_prediction'].unique(),
                                 default=list(df['final_prediction'].unique()))

cities = st.sidebar.multiselect("Cities", options=sorted(df['city'].unique()), default=[])

primary_pollutant = st.sidebar.selectbox("Primary Pollutant", 
                                         ['pm2_5','pm10','no2','so2','o3','co','aqi'])

last_update = datetime.now().strftime("%H:%M:%S")
st.sidebar.markdown(f"⏱ Last Updated: **{last_update}**")

# Apply filters
df_filtered = df[df['final_prediction'].isin(sources)]
if cities:
    df_filtered = df_filtered[df_filtered['city'].isin(cities)]

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🗺 Map", "📊 Analytics", "⚠ Alerts", "🤖 Predict"])

# --- MAP TAB ---
with tab1:
    st.header("🗺 Pollution Sources Map")
    if df_filtered.empty:
        st.warning("No data available for selected filters.")
    else:
        map_center = [df_filtered['latitude'].mean(), df_filtered['longitude'].mean()]
        m = folium.Map(location=map_center, zoom_start=6, tiles="CartoDB dark_matter")

        heat_data = df_filtered[['latitude','longitude',primary_pollutant]].values.tolist()
        HeatMap(heat_data, radius=15, name=f"{primary_pollutant} Heatmap").add_to(m)

        color_map = {'Vehicular':'blue','Industrial':'red','Burning':'orange','Dust':'gray','Other':'purple','Uncertain':'darkgreen'}
        for _, row in df_filtered.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=6,
                color=color_map.get(row['final_prediction'], 'white'),
                popup=f"<b>{row['name']}</b><br>Source: {row['final_prediction']}<br>AQI: {row['aqi']}<br>Confidence: {row['prediction_confidence']:.2f}",
                fill=True,
                fill_color=color_map.get(row['final_prediction'], 'white'),
                fill_opacity=0.7
            ).add_to(m)

        folium.LayerControl().add_to(m)
        st_folium(m, use_container_width=True)

# --- ANALYTICS TAB ---
with tab2:
    st.header("📊 Pollution Analytics")
    if df_filtered.empty:
        st.error("No data for selected filters.")
    else:
        col1, col2 = st.columns(2)
        col1.metric("Average AQI", f"{df_filtered['aqi'].mean():.2f}")
        col2.metric("Uncertain Predictions", f"{(df_filtered['final_prediction']=='Uncertain').mean()*100:.1f}%")

        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Source Distribution")
            fig_pie = px.pie(df_filtered, names='final_prediction', color='final_prediction',
                             color_discrete_map={'Vehicular':'blue','Industrial':'red','Burning':'orange','Dust':'gray','Other':'purple','Uncertain':'darkgreen'})
            st.plotly_chart(fig_pie, use_container_width=True)

        with col4:
            st.subheader("Pollutant Trends (Hourly)")
            chart_data = df_filtered.set_index('timestamp')[['pm2_5','pm10','no2','so2','o3','co']]
            fig_line = px.line(chart_data, x=chart_data.index, y=chart_data.columns)
            fig_line.update_layout(template="plotly_dark")
            st.plotly_chart(fig_line, use_container_width=True)

# --- ALERTS TAB ---
with tab3:
    st.header("⚠ Alerts")
    alerts = df_filtered[df_filtered['aqi'] > 150]
    if alerts.empty:
        st.success("✅ No critical alerts. Air quality is safe.")
    else:
        for _, row in alerts.iterrows():
            st.error(f"🚨 High AQI {row['aqi']} at {row['name']} ({row['city']})")

# --- PREDICT TAB ---
with tab4:
    st.header("🤖 Future Predictions")
    if df_filtered.empty:
        st.info("No data available for prediction right now.")
    else:
        preds_df = df_filtered[['timestamp','city','name','pm2_5','pm10','no2','so2','o3','co','aqi','final_prediction','prediction_confidence']].copy()
        st.dataframe(preds_df.head(20))

        # Download CSV
        st.download_button(
            "📥 Download Prediction Report (CSV)",
            preds_df.to_csv(index=False).encode("utf-8"),
            file_name="future_predictions.csv",
            mime="text/csv"
        )

        # PDF Export
        if st.button("📑 Generate PDF Report"):
            doc = SimpleDocTemplate("future_predictions.pdf", pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("🌍 EnviroScan: Future Pollution Prediction Report", styles['Title']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 20))

            table_data = [preds_df.columns.tolist()] + preds_df.head(20).values.tolist()
            table = Table(table_data)
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.grey),
                                       ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                                       ('ALIGN',(0,0),(-1,-1),'CENTER'),
                                       ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                                       ('BOTTOMPADDING',(0,0),(-1,0),12),
                                       ('BACKGROUND',(0,1),(-1,-1),colors.black),
                                       ('GRID',(0,0),(-1,-1),0.5,colors.white)]))
            elements.append(table)

            doc.build(elements)
            st.success("✅ PDF report generated: future_predictions.pdf")
            with open("future_predictions.pdf", "rb") as f:
                st.download_button(
                    "📥 Download PDF Report",
                    f,
                    file_name="future_predictions.pdf",
                    mime="application/pdf"
                )