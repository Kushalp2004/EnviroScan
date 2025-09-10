
import streamlit as st

st.set_page_config(page_title="Pollution Source Identification")
st.title("Ai Powered Pollution Source Identifier")

city = st.text_input("Enter the city name: ", placeholder="eg: Delhi")

if st.button("Analyze"):
  if city.strip() == "":
    st.warning("Please enter a valid city name. ")
  else:
    st.success("Analyzing pollution sources for {city}")
    st.markdown(f"""
          AI Powered Analysis for {city} (Simulated)
          Main Pollutants: PM2.5, NOx, SO2
          Likely Sources:
           - Industrial
           - Agricultural Burning/ Garbage burning
           - Vehicular
          Air Quality Index (AQI) : 185 (Unhealthy)
          Recommendation: Limit outdoor activities and stay indoors. Use Masks. Air purifiers are recommended for indoors
    """)
