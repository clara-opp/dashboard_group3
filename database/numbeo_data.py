"""
numbeo_data.py
--------------
FULL Numbeo refresh: creates/updates ALL 4 Numbeo CSV files in ./data:

  1) numbeo_countries.csv
  2) numbeo_country_prices.csv
  3) numbeo_exchange_rates.csv
  4) numbeo_country_indices.csv

This version uses SAFE WRITES:
- write to .tmp first, then atomic replace
- refuses to overwrite if DataFrame is empty / too small

Requirements:
  pip install requests pandas python-dotenv

Env:
  .env must contain: NUMBEO_API_KEY=...

Other required file:
  iso3_map.py providing ISO3_MAP (dict: country_name -> ISO3)

Run:
  python numbeo_data.py
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests
import pandas as pd
from dotenv import load_dotenv

from iso3_map import ISO3_MAP


# =========================
# Config
# =========================
BASE_URL = "https://www.numbeo.com/api"
TIMEOUT_SECONDS = 30
SLEEP_SECONDS = 0.35  # be gentle, lots of calls


# =========================
# Paths
# =========================
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# API Key
# =========================
load_dotenv()
API_KEY = os.environ.get("NUMBEO_API_KEY")
if not API_KEY:
    raise RuntimeError("NUMBEO_API_KEY is not set; define it in .env or your environment.")


# =========================
# Safe write helper
# =========================
def safe_write_csv(df: pd.DataFrame, target_path: Path, min_rows: int = 1) -> None:
    """
    Write CSV atomically:
      1) validate df size
      2) write to *.tmp
      3) replace target file

    This prevents breaking your pipeline when an API run partially fails.
    """
    n = 0 if df is None else len(df)
    if df is None or df.empty or n < min_rows:
        raise RuntimeError(
            f"Refusing to overwrite '{target_path.name}': only {n} rows (min_rows={min_rows})."
        )

    tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    df.to_csv(tmp_path, index=False)
    tmp_path.replace(target_path)  # atomic if same filesystem


# =========================
# HTTP helper
# =========================
def get_json(endpoint: str, params: Optional[dict] = None) -> Dict[str, Any]:
    """Generic helper to call a Numbeo API endpoint and return JSON."""
    if params is None:
        params = {}
    params = dict(params)
    params["api_key"] = API_KEY

    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        params=params,
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()

    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"Numbeo API error for endpoint '{endpoint}': {data['error']}")

    return data


# =========================
# Fetchers
# =========================
def fetch_exchange_rates() -> pd.DataFrame:
    data = get_json("currency_exchange_rates")
    if "exchange_rates" not in data:
        raise RuntimeError(f"Unexpected response for currency_exchange_rates: {data}")
    return pd.DataFrame(data["exchange_rates"])


def get_numbeo_countries() -> List[str]:
    """Retrieve all cities and derive the unique list of country names."""
    data = get_json("cities")
    if "cities" not in data:
        raise RuntimeError(f"Unexpected response for cities: {data}")
    return sorted({row["country"] for row in data["cities"]})


def get_country_prices(country_param: str) -> pd.DataFrame:
    """Fetch latest price data for a given country and return it as a DataFrame."""
    data = get_json("country_prices", {"country": country_param})
    if "prices" not in data:
        raise RuntimeError(f"Response for country '{country_param}' does not contain 'prices': {data}")
    df = pd.DataFrame(data["prices"])
    df["country_name"] = data.get("name")
    df["currency"] = data.get("currency")
    return df


def fetch_country_indices(country_param: str) -> Dict[str, Any]:
    """Fetch country-level indices (cost of living, QoL, etc.)."""
    return get_json("country_indices", {"country": country_param})


# =========================
# Main
# =========================
def main() -> None:
    print("\nNUMBEO FULL REFRESH")
    print("=" * 60)
    print(f"Data dir: {DATA_DIR}")

    # ------------------------------------------------------------
    # 1) Exchange rates
    # ------------------------------------------------------------
    print("\n[1/4] Updating exchange rates...")
    rates_df = fetch_exchange_rates()
    rates_out = DATA_DIR / "numbeo_exchange_rates.csv"
    safe_write_csv(rates_df, rates_out, min_rows=1)
    print(f"[OK] Saved: {rates_out} (rows={len(rates_df)})")

    # ------------------------------------------------------------
    # 2) Countries list from cities
    # ------------------------------------------------------------
    print("\n[2/4] Fetching country list from Numbeo cities...")
    countries = get_numbeo_countries()
    if len(countries) < 50:
        raise RuntimeError(f"Suspiciously few countries returned by Numbeo cities: {len(countries)}")
    print(f"[OK] Found {len(countries)} countries.")

    # ------------------------------------------------------------
    # 3) Prices for all countries + build numbeo_countries.csv
    # ------------------------------------------------------------
    print("\n[3/4] Fetching country prices for all countries (SLOW)...")
    all_price_frames: List[pd.DataFrame] = []
    country_rows: List[dict] = []
    failures = 0

    for i, country_param in enumerate(countries, start=1):
        try:
            df_country = get_country_prices(country_param)

            country_name = df_country["country_name"].iloc[0] if not df_country.empty else country_param
            currency = df_country["currency"].iloc[0] if not df_country.empty else None

            # map to ISO3 via iso3_map.py
            iso3 = ISO3_MAP.get(country_name) or ISO3_MAP.get(country_param)

            df_country["country_param_used"] = country_param
            df_country["iso3"] = iso3
            all_price_frames.append(df_country)

            country_rows.append(
                {
                    "country_name": country_name,
                    "country_param_used": country_param,
                    "currency": currency,
                    "iso3": iso3,
                }
            )

            if i % 25 == 0:
                print(f"  ...progress {i}/{len(countries)}")

        except Exception as e:
            failures += 1
            print(f"[ERROR] Prices failed for '{country_param}': {e}")

        time.sleep(SLEEP_SECONDS)

    if not all_price_frames:
        raise RuntimeError("No price data was collected; check API key / connectivity / rate limits.")

    prices_df = pd.concat(all_price_frames, ignore_index=True)

    # Write prices safely
    prices_out = DATA_DIR / "numbeo_country_prices.csv"
    # prices table is large; require a non-trivial minimum to avoid overwriting with junk
    safe_write_csv(prices_df, prices_out, min_rows=1000)
    print(f"[OK] Saved: {prices_out} (rows={len(prices_df)}, failures={failures})")

    countries_df = (
        pd.DataFrame(country_rows)
        .drop_duplicates(subset=["country_name"])
        .sort_values("country_name")
        .reset_index(drop=True)
    )

    # Write countries safely
    countries_out = DATA_DIR / "numbeo_countries.csv"
    safe_write_csv(countries_df, countries_out, min_rows=50)
    print(f"[OK] Saved: {countries_out} (rows={len(countries_df)})")

    # ------------------------------------------------------------
    # 4) Indices for all countries (prefer ISO3, fallback to name)
    # ------------------------------------------------------------
    print("\n[4/4] Fetching country indices...")
    idx_rows: List[dict] = []
    idx_failures = 0

    for _, row in countries_df.iterrows():
        iso3 = row.get("iso3")
        base_name = row.get("country_name")
        query_param = iso3 if isinstance(iso3, str) and iso3.strip() else base_name

        try:
            data = fetch_country_indices(query_param)
            idx_rows.append(
                {
                    "iso3": iso3,
                    "country_name": data.get("name", base_name),
                    "cost_of_living_index": data.get("cpi_index"),
                    "cpi_and_rent_index": data.get("cpi_and_rent_index"),
                    "rent_index": data.get("rent_index"),
                    "groceries_index": data.get("groceries_index"),
                    "restaurant_price_index": data.get("restaurant_price_index"),
                    "purchasing_power_incl_rent_index": data.get("purchasing_power_incl_rent_index"),
                    "quality_of_life_index": data.get("quality_of_life_index"),
                    "safety_index": data.get("safety_index"),
                    "health_care_index": data.get("health_care_index"),
                    "pollution_index": data.get("pollution_index"),
                    "property_price_to_income_ratio": data.get("property_price_to_income_ratio"),
                    "year_last_update": data.get("yearLastUpdate"),
                }
            )
        except Exception as e:
            idx_failures += 1
            print(f"[ERROR] Indices failed for '{base_name}' (param='{query_param}', iso3='{iso3}'): {e}")

        time.sleep(SLEEP_SECONDS)

    indices_df = pd.DataFrame(idx_rows)

    indices_out = DATA_DIR / "numbeo_country_indices.csv"
    safe_write_csv(indices_df, indices_out, min_rows=50)
    print(f"[OK] Saved: {indices_out} (rows={len(indices_df)}, failures={idx_failures})")

    print("\nDONE ✅")
    print("Files created/updated in ./data:")
    print("  - numbeo_countries.csv")
    print("  - numbeo_country_prices.csv")
    print("  - numbeo_exchange_rates.csv")
    print("  - numbeo_country_indices.csv")


if __name__ == "__main__":
    main()
