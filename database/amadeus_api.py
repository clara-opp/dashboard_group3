import pandas as pd
import os
import requests
import io

def get_passenger_rankings(script_dir):
    """
    Retrieves passenger rankings. Checks for a local CSV cache first.
    """
    # Look for data in a 'data' subdirectory or current directory
    cache_file = os.path.join(script_dir, 'data', 'airport_rankings.csv')
    if not os.path.exists(os.path.dirname(cache_file)):
        # Fallback to current dir if data folder doesn't exist
        cache_file = os.path.join(script_dir, 'airport_rankings.csv')
    
    # 1. Try to load from local cache
    if os.path.exists(cache_file):
        print(f"  Using cached ranking data from {cache_file}")
        return pd.read_csv(cache_file)

    # 2. If cache missing, scrape the website
    print("  Cache not found. Scraping ranking data from website...")
    url = "https://gettocenter.com/airports/top-100-airports-in-world/1000"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        dfs = pd.read_html(io.StringIO(response.text))
        
        if not dfs: 
            return pd.DataFrame()
        
        df = dfs[0].iloc[:, :6]
        df.columns = ['passenger_rank', 'name', 'iata_code', 'city', 'country', 'passenger_volume']
        
        if 'iata_code' in df.columns:
            df['iata_code'] = df['iata_code'].astype(str).str.upper().str.strip()
            df = df[df['iata_code'].str.match(r'^[A-Z]{3}$', na=False)]
            
        if 'passenger_volume' in df.columns:
            df['passenger_volume'] = df['passenger_volume'].astype(str).str.replace(r'[,\.]', '', regex=True)
            df['passenger_volume'] = pd.to_numeric(df['passenger_volume'], errors='coerce')
            
        # Ensure directory exists before saving
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        result_df = df[['iata_code', 'passenger_volume']]
        result_df.to_csv(cache_file, index=False)
        
        return result_df
        
    except Exception as e:
        print(f"  Warning: Could not fetch rankings: {e}")
        return pd.DataFrame()

def load_airport_data():
    """
    Fetches airport data, merges with rankings, and returns a DataFrame.
    """
    url = 'https://raw.githubusercontent.com/opentraveldata/opentraveldata/master/opentraveldata/optd_por_public.csv'

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    columns_to_use = [
        'iata_code', 'name', 'city_name_list', 'country_name',      
        'country_code', 'latitude', 'longitude', 'timezone', 'page_rank', 'fcode'
    ]

    # 1. Get Ranking Data
    df_rankings = get_passenger_rankings(script_dir)

    print("  Downloading main airport data from OpenTravelData (this may take a moment)...")
    try:
        # 2. Get Base Data
        df = pd.read_csv(url, sep='^', usecols=columns_to_use, low_memory=False)

        # 3. Data Cleaning
        df_airports = df[df['iata_code'].str.match(r'^[A-Z]{3}$', na=False)].copy()
        df_airports = df_airports[df_airports['fcode'] == 'AIRP'].copy()
        df_airports.dropna(subset=['timezone', 'city_name_list', 'country_name'], inplace=True)
        
        # Rename columns to match Unified DB conventions
        df_airports.rename(columns={
            'city_name_list': 'city',
            'country_code': 'iso2'  # Changed from ISO_3166 to iso2
            }, inplace=True)

        df_airports['city'] = df_airports['city'].str.split('=').str[0]

        # 4. Merge with Passenger Rankings
        df_airports = df_airports.merge(df_rankings, on='iata_code', how='left')
        df_airports['passenger_volume'] = df_airports['passenger_volume'].fillna(0)

        # 5. Sort
        df_airports.sort_values(by='passenger_volume', ascending=False, inplace=True)
        
        # Note: We do NOT set the index here, because we want iata_code to be a column in the SQL table
        
        print(f"  Processed {len(df_airports)} airports.")
        return df_airports

    except Exception as e:
        print(f"  Error processing airport data: {e}")
        return pd.DataFrame()

if __name__ == '__main__':
    # Test run
    df = load_airport_data()
    print(df.head())