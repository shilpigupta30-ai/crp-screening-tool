#!/usr/bin/env python3
"""
Test NOAA CDO API integration for point-specific R-factors
"""

import requests
from datetime import datetime

NOAA_CDO_TOKEN = "pyhBbWOmnzTdfSJUCpLhDBafxwfCxCbW"

def get_noaa_r_factor(lat, lon):
    """Test NOAA CDO R-factor calculation"""
    try:
        # Step 1: Find stations near the point
        extent = f"{lat - 0.5},{lon - 0.5},{lat + 0.5},{lon + 0.5}"

        stations_url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
        stations_params = {
            "extent": extent,
            "datasetid": "ANNUAL",
            "limit": 100
        }
        headers = {"token": NOAA_CDO_TOKEN}

        print(f"  📍 Querying NOAA for stations near ({lat}, {lon})...")
        stations_response = requests.get(stations_url, params=stations_params, headers=headers, timeout=10)
        stations_response.raise_for_status()
        stations_data = stations_response.json()

        if "results" not in stations_data or len(stations_data["results"]) == 0:
            print(f"  ❌ No stations found")
            return None, None

        print(f"  ✅ Found {len(stations_data['results'])} stations")

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

        # Step 2: Get precipitation data
        station_id = nearest_station["id"]
        current_year = datetime.now().year
        start_date = f"{current_year - 1}-01-01"
        end_date = f"{current_year - 1}-12-31"

        data_url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
        data_params = {
            "datasetid": "ANNUAL",
            "stationid": station_id,
            "startdate": start_date,
            "enddate": end_date,
            "datatypeid": "PRCP",
            "units": "metric",
            "limit": 1
        }

        print(f"  🌧️  Fetching precipitation data...")
        data_response = requests.get(data_url, params=data_params, headers=headers, timeout=10)
        data_response.raise_for_status()
        data = data_response.json()

        if "results" not in data or len(data["results"]) == 0:
            print(f"  ❌ No precipitation data found")
            return None, None

        precip_mm = data["results"][0]["value"]
        print(f"  📊 Annual Precipitation: {precip_mm} mm")

        # Step 3: Convert to R-factor
        if precip_mm <= 0:
            return None, None

        r_factor = round(0.04887 * (precip_mm ** 1.61), 1)
        print(f"  🔢 R-factor (Brown & Foster): {r_factor}")

        source_label = f"Point-specific R={r_factor} (NOAA CDO: {nearest_station['name']})"
        return r_factor, source_label

    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return None, None

# Test locations
TEST_LOCATIONS = {
    "Boone, Iowa": (41.875, -93.910),
    "Denver, Colorado": (39.739, -104.990),
    "Miami, Florida": (25.762, -80.193),
}

print("\n" + "="*80)
print("NOAA CDO API R-FACTOR TEST")
print("="*80)

for location, (lat, lon) in TEST_LOCATIONS.items():
    print(f"\n🌍 {location}")
    r, label = get_noaa_r_factor(lat, lon)
    if r:
        print(f"  ✅ SUCCESS: {label}")
    else:
        print(f"  ⚠️  Could not determine R-factor")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80 + "\n")
