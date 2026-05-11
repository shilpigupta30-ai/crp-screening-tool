#!/usr/bin/env python3
"""
Test NOAA CDO API with GHCND (Daily Climate Data) dataset
"""

import requests
from datetime import datetime

NOAA_CDO_TOKEN = "pyhBbWOmnzTdfSJUCpLhDBafxwfCxCbW"

def get_noaa_r_factor_v2(lat, lon):
    """
    Using GHCND (Global Historical Climatology Network - Daily) dataset
    which has more comprehensive precipitation data
    """
    try:
        # Step 1: Find GHCND stations near the point
        extent = f"{lat - 0.5},{lon - 0.5},{lat + 0.5},{lon + 0.5}"

        stations_url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
        stations_params = {
            "extent": extent,
            "datasetid": "GHCND",  # Global Historical Climatology Network Daily
            "limit": 100
        }
        headers = {"token": NOAA_CDO_TOKEN}

        print(f"  📍 Querying NOAA GHCND stations near ({lat}, {lon})...")
        stations_response = requests.get(stations_url, params=stations_params, headers=headers, timeout=10)
        stations_response.raise_for_status()
        stations_data = stations_response.json()

        if "results" not in stations_data or len(stations_data["results"]) == 0:
            print(f"  ❌ No stations found")
            return None, None

        print(f"  ✅ Found {len(stations_data['results'])} GHCND stations")

        # Find nearest station
        nearest_station = None
        min_distance = float('inf')

        for station in stations_data["results"]:
            stn_lat = station["latitude"]
            stn_lon = station["longitude"]
            distance = ((lat - stn_lat) ** 2 + (lon - stn_lon) ** 2) ** 0.5

            if distance < min_distance:
                min_distance = distance
                nearest_station = station

        print(f"  📌 Nearest station: {nearest_station['name']} ({min_distance:.2f}° away)")

        # Step 2: Get precipitation data from recent years
        station_id = nearest_station["id"]

        # Try recent year (2023)
        start_date = "2023-01-01"
        end_date = "2023-12-31"

        data_url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
        data_params = {
            "datasetid": "GHCND",
            "stationid": station_id,
            "startdate": start_date,
            "enddate": end_date,
            "datatypeid": "PRCP",  # Precipitation
            "units": "metric",
            "limit": 365
        }

        print(f"  🌧️  Fetching daily precipitation data for 2023...")
        data_response = requests.get(data_url, params=data_params, headers=headers, timeout=10)
        data_response.raise_for_status()
        data = data_response.json()

        if "results" not in data or len(data["results"]) == 0:
            print(f"  ❌ No precipitation data found for 2023")
            return None, None

        # Sum up all daily precipitation to get annual
        total_precip = sum([r["value"] for r in data["results"] if r.get("value")])
        print(f"  📊 Annual Precipitation (2023): {total_precip} mm ({len(data['results'])} days recorded)")

        if total_precip <= 0:
            return None, None

        # Convert to R-factor using Brown & Foster
        r_factor = round(0.04887 * (total_precip ** 1.61), 1)
        print(f"  🔢 R-factor (Brown & Foster): {r_factor}")

        source_label = f"Point-specific R={r_factor} (NOAA GHCND: {nearest_station['name']})"
        return r_factor, source_label

    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

# Test locations
TEST_LOCATIONS = {
    "Boone, Iowa": (41.875, -93.910),
    "Denver, Colorado": (39.739, -104.990),
}

print("\n" + "="*80)
print("NOAA CDO API R-FACTOR TEST (v2 - GHCND Dataset)")
print("="*80)

for location, (lat, lon) in TEST_LOCATIONS.items():
    print(f"\n🌍 {location}")
    r, label = get_noaa_r_factor_v2(lat, lon)
    if r:
        print(f"  ✅ SUCCESS: {label}")
    else:
        print(f"  ⚠️  Could not determine R-factor")

print("\n" + "="*80)
