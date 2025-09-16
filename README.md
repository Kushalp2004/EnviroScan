# Air Quality Data Pipeline: Module 1 Collection

This document outlines the data collection process executed on **September 15, 2025**. The project uses a two-step pipeline to first gather monitoring station locations and then collect real-time air quality data for those locations.

## Scripts

-   **`fetch_locations.py`**: Queries the OpenAQ API to fetch a list of government air quality monitoring stations within India.
-   **`fetch_pollution.py`**: Reads the locations from the generated CSV and queries the OpenWeatherMap API for current air pollution data at each location.

---
## Outputs

-   **`global_locations_cleaned.csv`**: A list of unique monitoring stations with their coordinates.
-   **`pollution_data.csv`**: The consolidated dataset containing real-time pollution measurements.

---
## Data Schema (`pollution_data.csv`)

-   **location\_id**: The unique identifier for the monitoring station, sourced from OpenAQ or manually assigned.
-   **pm2\_5**: Concentration of Particulate Matter 2.5 ($µg/m³$).
-   **pm10**: Concentration of Particulate Matter 10 ($µg/m³$).
-   **no2**: Concentration of Nitrogen Dioxide ($µg/m³$).
-   **so2**: Concentration of Sulphur Dioxide ($µg/m³$).
-   **o3**: Concentration of Ozone ($µg/m³$).
-   **co**: Concentration of Carbon Monoxide ($µg/m³$).
-   **aqi**: The calculated Air Quality Index (1 = Good, 5 = Very Poor).
-   **data\_source**: OpenWeatherMap (for pollution data) and OpenAQ (for location data).



---
## Assumptions & Process

-   Location data was collected for a bounding box approximating the geographical limits of **India**.
-   The pollution data represents a **real-time snapshot** taken at the moment the `fetch_pollution.py` script was executed for each location.
-   A **one-second delay** was enforced between API calls to OpenWeatherMap to respect rate limits and ensure stable data collection.
-   The final dataset relies on the availability and accuracy of the public APIs at the time of data collection.