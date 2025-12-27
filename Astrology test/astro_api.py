import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ROXY_API_KEY")
BASE_URL = "https://roxyapi.com/api/v1/data/astro/astrology/horoscope"

zodiac_signs = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]

all_daily_horoscopes = {}

print("Loading daily horoscopes for all zodiac signs...")

for i, sign in enumerate(zodiac_signs, 1):
    url = f"{BASE_URL}/{sign}?token={API_KEY}"
    
    print(f"[{i}/12] Loading {sign.capitalize()}...")
    
    try:
        response = requests.get(url, timeout=(10, 30))
        
        if response.status_code == 200:
            data = response.json()
            all_daily_horoscopes[sign] = data
            print(f"    Success")
        else:
            all_daily_horoscopes[sign] = {
                "error": f"HTTP {response.status_code}",
                "message": response.text
            }
            print(f"    Error: {response.status_code}")
            
    except requests.exceptions.Timeout:
        all_daily_horoscopes[sign] = {"error": "Timeout"}
        print(f"    Timeout")
    except requests.exceptions.RequestException as e:
        all_daily_horoscopes[sign] = {"error": str(e)}
        print(f"    Request error: {e}")

# Save as JSON
with open("all_daily_horoscopes.json", "w", encoding="utf-8") as f:
    json.dump(all_daily_horoscopes, f, ensure_ascii=False, indent=2)

print("\nAll daily horoscopes saved to 'all_daily_horoscopes.json'")
print(f"   {len([s for s in zodiac_signs if 'error' not in all_daily_horoscopes[s]])}/12 successful")
