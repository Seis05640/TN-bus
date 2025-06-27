import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from datetime import datetime

# Step 1: Go directly to the actual form URL (bypass outer iframe wrapper)
driver = uc.Chrome()
driver.get("https://www.tnstc.in/OTRSOnline/advanceBooking.do")

wait = WebDriverWait(driver, 20)

# Step 2: Enter source
from_input = wait.until(EC.presence_of_element_located((By.ID, "matchStartPlace")))
from_input.clear()
from_input.send_keys("CHENNAI CMBT")
time.sleep(1)
from_input.send_keys(Keys.ARROW_DOWN, Keys.ENTER)

# Step 3: Enter destination
to_input = driver.find_element(By.ID, "matchEndPlace")
to_input.clear()
to_input.send_keys("MADURAI")
time.sleep(1)
to_input.send_keys(Keys.ARROW_DOWN, Keys.ENTER)

# Step 4: Enter journey date (today + 1)
journey_date = (datetime.now().date() + pd.Timedelta(days=1)).strftime("%d/%m/%Y")
date_input = driver.find_element(By.ID, "txtJourneyDate")
date_input.clear()
date_input.send_keys(journey_date)

# Step 5: Submit search
search_btn = driver.find_element(By.ID, "searchBtn")
search_btn.click()

# Step 6: Wait for results and collect data
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tblmnJrnys")))

rows = driver.find_elements(By.CLASS_NAME, "tblmnJrnys")
results = []

for row in rows:
    try:
        cols = row.find_elements(By.TAG_NAME, "td")
        results.append({
            "Bus Type": cols[0].text.strip(),
            "Departure": cols[1].text.strip(),
            "Arrival": cols[2].text.strip(),
            "Available Seats": cols[3].text.strip(),
            "Fare": cols[4].text.strip(),
            "Date Scraped": datetime.now().strftime("%Y-%m-%d")
        })
    except:
        continue

# Save to CSV
df = pd.DataFrame(results)
file_name = f"tnstc_results_{datetime.now().strftime('%Y%m%d')}.csv"
df.to_csv(file_name, index=False)

print(f"✅ {len(df)} buses scraped successfully and saved to {file_name}")
driver.quit()
