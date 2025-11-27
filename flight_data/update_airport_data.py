import pandas as pd
import os
import sqlite3
import requests
import io

def get_passenger_rankings(script_dir):
    """
    Retrieves passenger rankings. Checks for a local CSV cache first to avoid
    losing data if the website changes. If missing, scrapes the website.
    """
    cache_file = os.path.join(script_dir, 'airport_rankings.csv')
    
    # 1. Try to load from local cache
    if os.path.exists(cache_file):
        print(f"Using cached ranking data from {cache_file}")
        return pd.read_csv(cache_file)

    # 2. If cache missing, scrape the website
    print("Cache not found. Scraping ranking data from website...")
    url = "https://gettocenter.com/airports/top-100-airports-in-world/1000"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Read HTML tables
        dfs = pd.read_html(io.StringIO(response.text))
        
        if not dfs: 
            print("Warning: No tables found on ranking site.")
            return pd.DataFrame()
        
        # Force selection of the first 6 columns (Rank, Name, Code, City, Country, Passengers)
        # This discards the empty columns 6-99 that caused issues previously.
        df = dfs[0].iloc[:, :6]
        df.columns = ['passenger_rank', 'name', 'iata_code', 'city', 'country', 'passenger_volume']
        
        # Clean IATA code
        if 'iata_code' in df.columns:
            df['iata_code'] = df['iata_code'].astype(str).str.upper().str.strip()
            df = df[df['iata_code'].str.match(r'^[A-Z]{3}$', na=False)]
            
        # Clean Passenger Volume
        if 'passenger_volume' in df.columns:
            df['passenger_volume'] = df['passenger_volume'].astype(str).str.replace(r'[,\.]', '', regex=True)
            df['passenger_volume'] = pd.to_numeric(df['passenger_volume'], errors='coerce')
            
        # Save to CSV for future runs (Cache it)
        result_df = df[['iata_code', 'passenger_volume']]
        result_df.to_csv(cache_file, index=False)
        print(f"Rankings scraped and saved to {cache_file}")
        
        return result_df
        
    except Exception as e:
        print(f"Warning: Could not fetch rankings: {e}")
        return pd.DataFrame()

def fetch_and_process_airport_data():
    """
    Fetches the latest airport data from OpenTravelData, processes it,
    merges it with passenger rankings, and saves it to a SQLite database.
    """
    url = 'https://raw.githubusercontent.com/opentraveldata/opentraveldata/master/opentraveldata/optd_por_public.csv'

    # Determine script directory early to locate the cache file
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    # Define the columns you are interested in to save memory
    columns_to_use = [
        'iata_code',
        'name',
        'city_name_list',
        'country_name',      
        'country_code',      
        'latitude',
        'longitude',
        'timezone',
        'page_rank',          
        'fcode'
    ]

    # --- 1. Get Ranking Data ---
    df_rankings = get_passenger_rankings(script_dir)

    print("Starting main airport data download from OpenTravelData...")
    try:
        # --- 2. Get Base Data ---
        # OpenTravelData uses '^' as a separator in their CSV
        df = pd.read_csv(url, sep='^', usecols=columns_to_use, low_memory=False)
        print("Base data downloaded successfully.")

        # --- 3. Data Cleaning and Processing ---

        # Filter for valid airports
        df_airports = df[df['iata_code'].str.match(r'^[A-Z]{3}$', na=False)].copy()

        # Filter out heliports, etc., keeping only major airports
        df_airports = df_airports[df_airports['fcode'] == 'AIRP'].copy()
        
        # Drop rows with missing essential data
        df_airports.dropna(subset=['timezone', 'city_name_list', 'country_name'], inplace=True)
        
        # Clean up city names (e.g., "Dallas=Fort Worth" -> "Dallas")
        df_airports.rename(columns={
            'city_name_list': 'city',
            'country_code': 'ISO_3166'
            }, inplace=True)

        df_airports['city'] = df_airports['city'].str.split('=').str[0]

        # --- 4. Merge with Passenger Rankings ---
        # We use a LEFT join. Airports not in the ranking list will get NaN passenger_volume.
        df_airports = df_airports.merge(df_rankings, on='iata_code', how='left')
        
        # Fill missing passenger volumes with 0 so we can sort
        df_airports['passenger_volume'] = df_airports['passenger_volume'].fillna(0)

        # --- 5. Sort and Index ---
        # Sort by passenger_volume descending (most important airports first)
        df_airports.sort_values(by='passenger_volume', ascending=False, inplace=True)
        
        # Set the index to iata_code
        df_airports.set_index('iata_code', inplace=True)
        
        # --- 6. Saving the Data ---
        output_filename = 'airports.db'
        table_name = 'airports'
            
        output_path = os.path.join(script_dir, output_filename)

        # Connect to SQLite database (this will create the file if it doesn't exist)
        conn = sqlite3.connect(output_path)
        
        # Write the dataframe to a table, replacing it if it already exists
        df_airports.to_sql(table_name, conn, if_exists='replace', index=True)
        
        conn.close()

        print(f"Processing complete. Data saved to table '{table_name}' in {output_path}")
        print(f"Total airports processed: {len(df_airports)}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    fetch_and_process_airport_data()