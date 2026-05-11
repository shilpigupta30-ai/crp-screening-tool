#!/usr/bin/env python3
"""
Direct test: What is NOAA actually returning for Boone, Iowa?
"""
import requests
import os

NOAA_CDO_TOKEN = "pyhBbWOmnzTdfSJUCpLhDBafxwfCxCbW"

lat, lon = 41.875, -93.910

print("=" * 80)
print("TESTING NOAA CDO API for Boone, Iowa")
print("=" * 80)

# Step 1: Find stations
extent = f"{lat - 0.5},{lon - 0.5},{lat + 0.5},{lon + 0.5}"
print(f"\n1️⃣ Finding stations in extent: {extent}")

stations_url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
stations_params = {
    "extent": extent,
    "datasetid": "GHCND",
    "limit": 100
}
headers = {"token": NOAA_CDO_TOKEN}

try:
    stations_response = requests.get(stations_url, params=stations_params, headers=headers, timeout=10)
    stations_response.raise_for_status()
    stations_data = stations_response.json()

    if "results" in stations_data and len(stations_data["results"]) > 0:
        print(f"✅ Found {len(stations_data['results'])} stations")

        # Show first 3 stations
        for i, station in enumerate(stations_data["results"][:3]):
            print(f"   {i+1}. {station.get('name')} (ID: {station.get('id')})")

        # Use the nearest recent station
        selected = None
        for station in stations_data["results"]:
            maxdate = station.get("maxdate", "")
            if maxdate and maxdate[:4] >= "2023":
                selected = station
                break

        if not selected:
            selected = stations_data["results"][0]

        print(f"\n📍 Selected: {selected.get('name')} (ID: {selected.get('id')})")

        # Step 2: Get precipitation data
        station_id = selected["id"]
        start_date = "2023-01-01"
        end_date = "2023-12-31"

        print(f"\n2️⃣ Fetching daily precipitation for {start_date} to {end_date}...")

        data_url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
        data_params = {
            "datasetid": "GHCND",
            "stationid": station_id,
            "startdate": start_date,
            "enddate": end_date,
            "datatypeid": "PRCP",
            "limit": 365
        }

        data_response = requests.get(data_url, params=data_params, headers=headers, timeout=10)
        data_response.raise_for_status()
        data = data_response.json()

        if "results" in data and len(data["results"]) > 0:
            print(f"✅ Retrieved {len(data['results'])} precipitation records")

            # Show first 10 records
            print(f"\n📊 First 10 daily precipitation values:")
            for i, record in enumerate(data['results'][:10]):
                print(f"   {i+1}. Date: {record.get('date')}, Value: {record.get('value')}")

            # Calculate totals
            total_raw = sum([r["value"] for r in data["results"] if r.get("value")])
            precip_mm = total_raw / 10.0

            print(f"\n3️⃣ Precipitation Calculation:")
            print(f"   Total raw value: {total_raw}")
            print(f"   Converted (÷10): {precip_mm:.1f} mm/year")
            print(f"   Expected for Iowa: ~850 mm/year")
            print(f"   Status: {'✅ REASONABLE' if 600 < precip_mm < 1500 else '❌ UNREASONABLE'}")

            # Brown & Foster equation
            r_factor = 0.04887 * (precip_mm ** 1.61)
            print(f"\n4️⃣ Brown & Foster Conversion:")
            print(f"   R = 0.04887 × {precip_mm:.1f}^1.61")
            print(f"   R = {r_factor:.1f}")
            print(f"   Expected for Iowa: ~160")
            print(f"   Status: {'✅ REASONABLE' if 100 < r_factor < 250 else '❌ UNREASONABLE (too high)'}")
        else:
            print(f"❌ No precipitation data found")
            print(f"Response: {data}")
    else:
        print(f"❌ No stations found")
        print(f"Response: {stations_data}")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
