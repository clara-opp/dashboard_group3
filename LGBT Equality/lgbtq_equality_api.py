import requests
import json

def fetch_equality_index_data():
    """
    Fetch LGBT Equality Index scores for all countries from Equaldex API.
    Save the data as JSON file.
    """
    
    url = "https://www.equaldex.com/api/equality-index?format=json"
    
    try:
        print("Fetching data from Equaldex API...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Save to JSON file
        filename = "equality_index_data.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved {len(data)} countries to {filename}")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

if __name__ == "__main__":
    fetch_equality_index_data()
