#!/usr/bin/env python3
"""
Debug: Why is NOAA R-factor calculation giving wrong results?
Test the Brown & Foster equation with real NOAA data.
"""

import requests
import math

NOAA_CDO_TOKEN = "pyhBbWOmnzTdfSJUCpLhDBafxwfCxCbW"

# Test location: Boone, Iowa
lat, lon = 41.875, -93.910

print("=" * 80)
print("DEBUGGING NOAA R-FACTOR CALCULATION")
print("=" * 80)

# Step 1: Get NOAA precipitation data
print(f"\n1️⃣ Fetching NOAA data for Boone, Iowa ({lat}, {lon})...")

extent = f"{lat - 0.5},{lon - 0.5},{lat + 0.5},{lon + 0.5}"
stations_url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
stations_params = {
    "extent": extent,
    "datasetid": "GHCND",
    "limit": 100
}
headers = {"token": NOAA_CDO_TOKEN}

stations_response = requests.get(stations_url, params=stations_params, headers=headers, timeout=10)
stations_data = stations_response.json()

# Find best station
selected_station = None
for station in stations_data["results"]:
    if station.get("maxdate", "")[:4] >= "2023":
        selected_station = station
        break

if not selected_station:
    selected_station = stations_data["results"][0]

station_id = selected_station["id"]
station_name = selected_station.get("name", "Unknown")

print(f"✅ Selected station: {station_name}")

# Step 2: Get precipitation data
print(f"\n2️⃣ Fetching daily precipitation for 2023...")

data_url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
data_params = {
    "datasetid": "GHCND",
    "stationid": station_id,
    "startdate": "2023-01-01",
    "enddate": "2023-12-31",
    "datatypeid": "PRCP",
    "limit": 365
}

data_response = requests.get(data_url, params=data_params, headers=headers, timeout=10)
data = data_response.json()

if "results" in data:
    precip_records = data["results"]
    total_raw = sum([r["value"] for r in precip_records if r.get("value")])
    precip_mm = total_raw / 10.0

    print(f"✅ Retrieved {len(precip_records)} precipitation records")
    print(f"   Total raw: {total_raw} (tenths of mm)")
    print(f"   Converted: {precip_mm:.1f} mm/year")
    print(f"   Expected: ~850 mm/year for Iowa")

    # Step 3: Test different Brown & Foster formulas
    print(f"\n3️⃣ Testing Brown & Foster equations...")
    print(f"\n   Given: P = {precip_mm:.1f} mm/year")
    print(f"   Expected R ≈ 160 for Iowa")

    # Formula 1: Current (wrong)
    r1 = 0.04887 * (precip_mm ** 1.61)
    print(f"\n   Formula 1: R = 0.04887 × P^1.61")
    print(f"   Result: R = {r1:.1f} ❌ (10x too high)")

    # Formula 2: Try with inches
    precip_inches = precip_mm / 25.4
    r2 = 0.04887 * (precip_inches ** 1.61)
    print(f"\n   Formula 2: R = 0.04887 × (P_inches)^1.61")
    print(f"   P = {precip_inches:.1f} inches/year")
    print(f"   Result: R = {r2:.1f} ❌ (way too low)")

    # Formula 3: Try reverse calculation - what constant would work?
    # If R should be 160, what constant C would work?
    # 160 = C × (633.6)^1.61
    c_needed = 160 / (precip_mm ** 1.61)
    print(f"\n   Formula 3: Reverse calculation")
    print(f"   If R_target = 160, then constant needed:")
    print(f"   C = 160 / ({precip_mm:.1f})^1.61 = {c_needed:.6f}")
    print(f"   Current C = 0.04887")
    print(f"   Ratio: {0.04887 / c_needed:.1f}x too high")

    # Formula 4: Try with cm instead of mm
    precip_cm = precip_mm / 10
    r4 = 0.04887 * (precip_cm ** 1.61)
    print(f"\n   Formula 4: R = 0.04887 × (P_cm)^1.61")
    print(f"   P = {precip_cm:.1f} cm/year")
    print(f"   Result: R = {r4:.1f} ❌ (still wrong)")

    # Formula 5: Try different exponent
    r5 = 0.04887 * (precip_mm ** 0.5)
    print(f"\n   Formula 5: R = 0.04887 × P^0.5 (different exponent)")
    print(f"   Result: R = {r5:.1f} ❌")

    # Formula 6: Maybe it's a completely different approach
    # Standard empirical: R ≈ 0.00349 × P^1.733 (some references use this)
    r6 = 0.00349 * (precip_mm ** 1.733)
    print(f"\n   Formula 6: R = 0.00349 × P^1.733 (alternative)")
    print(f"   Result: R = {r6:.1f} {'✓ CLOSE!' if 150 < r6 < 170 else '❌'}")

    # Formula 7: Monthly approach - sum R for each month?
    print(f"\n   Formula 7: Monthly vs Annual?")
    print(f"   Current code sums ALL daily values")
    print(f"   Should it calculate R for each month, then sum?")
    print(f"   (Would require different data structure)")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)
print(f"""
The Brown & Foster equation R = 0.04887 × P^1.61 is giving results 10x too high.

Possible causes:
1. Wrong constant (0.04887 might be for a different unit/context)
2. Wrong exponent (1.61 might be incorrect)
3. Formula should use monthly data, not annual totals
4. NOAA data might need different preprocessing
5. This formula might not be the right one for NOAA CDO data

Recommendation:
- Research the exact Brown & Foster equation source
- Check if it's meant for different precipitation units or time periods
- Consider using NRCS published R-factor maps instead
- Or use NOAA's pre-calculated R-factors if available

For now, state-level R-factors are working correctly.
""")

print("=" * 80)
