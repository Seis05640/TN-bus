import pandas as pd
import googlemaps
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Load API keys
load_dotenv()
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
weatherstack_key = os.getenv("WEATHERSTACK_API_KEY")

# Load your data
df = pd.read_csv("SETCbustimings_cleaned.csv")

# Ensure full datetime
today = datetime.today().strftime("%Y-%m-%d")
df['Departure_FullTime'] = pd.to_datetime(today + " " + df['Departure_Time_Formatted'])

# Add new columns
df['Travel_Time_Min'] = None
df['Distance_km'] = None
df['Weather'] = None

for idx, row in df.iterrows():
    try:
        source = row['From']
        dest = row['To']
        depart_time = int(row['Departure_FullTime'].timestamp())

        # === Google Maps ===
        gmap_result = gmaps.distance_matrix(
            source, dest, mode="driving", departure_time=depart_time
        )
        duration = gmap_result['rows'][0]['elements'][0]['duration_in_traffic']['value'] // 60
        distance = gmap_result['rows'][0]['elements'][0]['distance']['value'] / 1000

        df.at[idx, 'Travel_Time_Min'] = duration
        df.at[idx, 'Distance_km'] = distance

        # === Weatherstack ===
        weather_url = f"http://api.weatherstack.com/current?access_key={weatherstack_key}&query={source}"
        weather_data = requests.get(weather_url).json()
        
        if 'current' in weather_data:
            weather_desc = weather_data['current']['weather_descriptions'][0]
            df.at[idx, 'Weather'] = weather_desc
        else:
            df.at[idx, 'Weather'] = "Unavailable"

        print(f"[✓] {source} → {dest} | {duration} min | {weather_desc}")
    except Exception as e:
        print(f"[X] Failed for {source} → {dest}: {e}")
        continue

# Save result
df.to_csv("SETC_enriched_weatherstack.csv", index=False)
print("✅ Enriched data saved as SETC_enriched_weatherstack.csv")
