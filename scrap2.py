import requests
from bs4 import BeautifulSoup
import pandas as pd

# Inputs
source = "chennai"
destination = "madurai"
date = "28-06-2025"  # Format: dd-mm-yyyy

# TamilVandi URL
url = f"https://www.tamilvandi.com/search?from={source}&to={destination}&date={date}"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Find all bus cards
bus_cards = soup.find_all("div", class_="search-result-card")

results = []

for card in bus_cards:
    try:
        operator = card.find("div", class_="search-bus-name").text.strip()
        bus_type = card.find("div", class_="search-bus-type").text.strip()
        departure = card.find("div", class_="search-depart-time").text.strip()
        arrival = card.find("div", class_="search-arrive-time").text.strip()
        price = card.find("div", class_="search-price").text.strip()

        results.append({
            "Operator": operator,
            "Bus Type": bus_type,
            "Departure": departure,
            "Arrival": arrival,
            "Fare": price,
            "Source": source,
            "Destination": destination,
            "Date": date
        })
    except Exception as e:
        print("Error parsing a card:", e)

# Save to CSV
df = pd.DataFrame(results)
df.to_csv("tamilvandi_bus_data.csv", index=False)
print("✅ Data saved to tamilvandi_bus_data.csv")
