import os
import json
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Import the ISO loader from your database script to ensure country list matches
from database import load_iso_codes, get_data_path

load_dotenv()

ACCESS_KEY = os.getenv("ACCESS_KEY_UNSPLASH")
DATA_FILE = "pictures.json"

def get_existing_pictures():
    """Load existing pictures.json if it exists."""
    try:
        # This looks in ./data/pictures.json
        path = get_data_path(DATA_FILE)
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return []

def save_pictures(data):
    """Save the current list of pictures to ./data/pictures.json."""
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    filepath = data_dir / DATA_FILE
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} records to {filepath}")

def fetch_country_images():
    if not ACCESS_KEY:
        print("Error: ACCESS_KEY_UNSPLASH not found in .env")
        return

    print("--- Starting Unsplash Image Fetch (Top 3 per Country) ---")
    
    # 1. Load Countries (Source of Truth for the DB)
    try:
        df_iso = load_iso_codes().reset_index()
    except Exception as e:
        print(f"Error loading ISO codes: {e}")
        return

    # 2. Load existing progress
    existing_data = get_existing_pictures()
    existing_iso3 = {item['iso3'] for item in existing_data}
    
    results = existing_data
    
    print(f"Found {len(existing_data)} existing records.")

    # Filter df to only countries we still need
    countries_to_fetch = df_iso[~df_iso['iso3'].isin(existing_iso3)]
    total_to_fetch = len(countries_to_fetch)
    print(f"Remaining countries to fetch: {total_to_fetch}")

    # 3. Iterate through countries
    for index, row in countries_to_fetch.iterrows():
        iso3 = row['iso3']
        country_name = row['country_name']

        # Search using only the country name as requested
        search_query = country_name 

        print(f"Fetching: '{search_query}'...", end=" ")

        url = "https://api.unsplash.com/search/photos"
        params = {
            "query": search_query,
            "page": 1,
            "per_page": 3,          # Fetch top 3 most relevant
            "orientation": "landscape",
            "content_filter": "high"
        }
        headers = {
            "Authorization": f"Client-ID {ACCESS_KEY}",
            "Accept-Version": "v1"
        }

        while True:
            try:
                response = requests.get(url, params=params, headers=headers)
                
                # CHECK FOR RATE LIMITS (403 or 429)
                if response.status_code == 403 or response.status_code == 429:
                    print("\nRate limit hit! 🛑")
                    print("Sleeping for 60 minutes to reset quota...")
                    save_pictures(results)
                    time.sleep(3660) # Sleep 1 hour + 1 minute
                    print("Resuming fetch...")
                    continue 

                if response.status_code == 200:
                    data = response.json()
                    remaining = response.headers.get('X-Ratelimit-Remaining', '?')
                    
                    if data['results']:
                        country_entry = {
                            "iso3": iso3,
                            "country_name": country_name,
                            "images": []
                        }
                        
                        for i, photo in enumerate(data['results']):
                            img_data = {
                                "rank": i + 1,
                                "image_url": photo['urls']['regular'],
                                "image_small_url": photo['urls']['small'],
                                "photographer_name": photo['user']['name'],
                                "photographer_url": photo['user']['links']['html']
                            }
                            country_entry['images'].append(img_data)
                        
                        results.append(country_entry)
                        print(f"✅ Found {len(country_entry['images'])} images (Rem: {remaining})")
                    else:
                        print(f"❌ No results (Rem: {remaining})")
                    break 
                
                else:
                    print(f"Error {response.status_code}")
                    break

            except Exception as e:
                print(f"Exception: {e}")
                break

        # Small pause to be polite
        time.sleep(0.5)

    # 4. Final Save
    save_pictures(results)
    print("--- Fetch Complete ---")

if __name__ == "__main__":
    fetch_country_images()