import streamlit as st
import pandas as pd
import joblib

# Load trained model and weather label encoder
model = joblib.load("delay_predictor_model.pkl")
weather_encoder = joblib.load("weather_encoder.pkl")

# Page configuration
st.set_page_config(page_title="TNSTC Bus Delay Predictor", layout="centered")
st.title("🚌 TNSTC / SETC Bus Delay Predictor")
st.markdown("""
This app predicts whether a Tamil Nadu government bus will be **Early**, **On Time**, or **Delayed** based on:

- Distance of the route
- Estimated travel time
- Current weather
- Scheduled departure time
""")

# Input section
col1, col2 = st.columns(2)

with col1:
    distance = st.number_input(
        "Route Distance (in km)",
        min_value=10.0,
        max_value=800.0,
        value=350.0,
        step=10.0
    )
    
    travel_time = st.number_input(
        "Estimated Travel Time (in minutes)",
        min_value=30,
        max_value=1000,
        value=360,
        step=10
    )

with col2:
    weather = st.selectbox("Current Weather Condition", weather_encoder.classes_.tolist())
    dep_hour = st.slider("Scheduled Departure Hour (24hr)", min_value=0, max_value=23, value=17)

# Predict button
if st.button("🔍 Predict Delay Status"):
    try:
        weather_encoded = weather_encoder.transform([weather])[0]

        input_df = pd.DataFrame([{
            "Distance_km": distance,
            "Travel_Time_Min": travel_time,
            "Weather_Enc": weather_encoded,
            "Dep_Hour": dep_hour
        }])

        prediction = model.predict(input_df)[0]
        st.success(f"🧾 Predicted Status: **{prediction}**")
    
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Footer
st.markdown("---")
st.caption("Built as part of a Real-World Data Science Internship Project")
