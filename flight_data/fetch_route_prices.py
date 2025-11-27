import pandas as pd
import os
import datetime
import time
from pathlib import Path
from dotenv import load_dotenv

# Assumes amadeus_api_client is now in the same 'database' folder
import amadeus_api_client as amadeus

def get_flight_network_data(airports_df):
    """
    Generates flight prices from US/DE to all other countries.
    
    Logic:
    1. Selects the single busiest airport for every country (ISO2).
    2. Uses the busiest US airport and busiest DE airport as origins.
    3. Fetches flight prices to the ~200 resulting country hubs.
    """
    # 1. Setup Paths
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    cache_file = data_dir / "flight_network_data.json"

    # 2. Check Cache
    if cache_file.exists():
        print(f"  Using cached flight network data from {cache_file}")
        try:
            return pd.read_json(cache_file)
        except ValueError:
            print("  ⚠️ Error reading cached JSON. Re-fetching data...")

    print("  Cache not found. Preparing to fetch live flight prices...")

    # 3. Load Env
    load_dotenv(script_dir.parent / ".env")
    
    AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
    AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")
    
    if not AMADEUS_API_KEY or not AMADEUS_API_SECRET:
        print("  ❌ Error: Amadeus credentials not found in .env")
        return pd.DataFrame()

    # 4. Define Origins and Destinations (CRITICAL STEP)
    try:
        # Ensure we have the necessary columns
        if 'iso2' not in airports_df.columns or 'passenger_volume' not in airports_df.columns:
            print("  ❌ Error: airports_df missing 'iso2' or 'passenger_volume' columns.")
            return pd.DataFrame()

        # FILTER: Group by Country (iso2) and take ONLY the 1 busiest airport
        top_airports_per_country = airports_df.sort_values(
            by='passenger_volume', ascending=False
        ).groupby('iso2').head(1)

        print(f"  Filtered down to {len(top_airports_per_country)} airports (1 per country).")

        # Get the busiest airport for US and DE from this filtered list
        us_row = top_airports_per_country[top_airports_per_country['iso2'] == 'US']
        de_row = top_airports_per_country[top_airports_per_country['iso2'] == 'DE']

        if us_row.empty or de_row.empty:
            print("  ⚠️ Error: Could not find airports for US or Germany in airport data.")
            return pd.DataFrame()

        us_origin = us_row.iloc[0]['iata_code']
        de_origin = de_row.iloc[0]['iata_code']
        
        # DESTINATIONS: Use the FILTERED list, not the full dataframe
        destinations = top_airports_per_country['iata_code'].tolist()

    except Exception as e:
        print(f"  ❌ Error identifying origins/destinations: {e}")
        return pd.DataFrame()

    print(f"  Origins selected: {us_origin} (US) and {de_origin} (DE)")

    # 5. Generate Routes
    routes = []
    for dest in destinations:
        if dest != us_origin:
            routes.append((us_origin, dest))
        if dest != de_origin:
            routes.append((de_origin, dest))

    total_routes = len(routes)
    print(f"  Total routes to fetch: {total_routes}")

    # --- SAFETY CHECK ---
    if total_routes > 1000:
        print(f"  🛑 STOPPING: {total_routes} routes is too many! Something is wrong with the filtering.")
        print("  Please check that you are grouping by 'iso2' correctly.")
        return pd.DataFrame()
    # --------------------
    
    # 6. Authenticate
    token = amadeus.get_amadeus_access_token(AMADEUS_API_KEY, AMADEUS_API_SECRET)
    if not token: return pd.DataFrame()

    # 7. Set Dates (90 days out)
    today = datetime.date.today()
    departure_date = today + datetime.timedelta(days=90)
    return_date = departure_date + datetime.timedelta(days=7)

    results = []
    
    # 8. Fetch Data
    print(f"  Starting API calls (Approx. time: {total_routes * 0.3 / 60:.1f} minutes)...")
    
    for i, (origin, destination) in enumerate(routes):
        if i % 10 == 0:
            print(f"  Fetching route {i+1}/{total_routes}...", end="\r")

        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date.strftime("%Y-%m-%d"),
            "returnDate": return_date.strftime("%Y-%m-%d"),
            "adults": 1,
            "nonStop": "false",
            "currencyCode": "EUR",
            "max": 1
        }

        try:
            response = amadeus.search_flight_offers(token, params)
            
            if response and 'data' in response and len(response['data']) > 0:
                cheapest = response['data'][0]
                price = float(cheapest['price']['total'])
                
                itineraries = cheapest.get('itineraries', [])
                stops_outbound = len(itineraries[0]['segments']) - 1 if itineraries else 0
                is_direct = (stops_outbound == 0)
                
                results.append({
                    "origin": origin,
                    "destination": destination,
                    "price_eur": price,
                    "is_direct": is_direct,
                    "stops": stops_outbound
                })
        except Exception:
            pass 
        
        time.sleep(0.3) 

    print(f"\n  Fetch complete. Found prices for {len(results)} routes.")

    # 9. Save and Return
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results.to_json(cache_file, orient='records', indent=4)
        print(f"  ✅ Flight data cached to {cache_file}")
    
    return df_results