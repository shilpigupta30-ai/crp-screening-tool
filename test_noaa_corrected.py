#!/usr/bin/env python3
"""
Test: Does the corrected Brown & Foster constant (0.004934) give correct R-factors?
"""

import requests

NOAA_CDO_TOKEN = "pyhBbWOmnzTdfSJUCpLhDBafxwfCxCbW"

def get_noaa_r_factor_corrected(lat, lon, location_name, expected_r):
    """Test NOAA R-factor with corrected constant"""

    print(f"\n{'='*80}")
    print(f"TEST: {location_name} ({lat}, {lon})")
    print(f"Expected R-factor: {expected_r}")
    print(f"{'='*80}")

    try:
        # Find station
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

        # Select best station
        selected_station = None
        for station in stations_data["results"]:
            if station.get("maxdate", "")[:4] >= "2023":
                selected_station = station
                break
        if not selected_station:
            selected_station = stations_data["results"][0]

        station_id = selected_station["id"]
        station_name = selected_station.get("name", "Unknown")

        print(f"\n📍 Selected station: {station_name}")

        # Get precipitation
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

        if "results" not in data or len(data["results"]) == 0:
            print(f"❌ No precipitation data")
            return None

        # Calculate precipitation
        total_raw = sum([r["value"] for r in data["results"] if r.get("value")])
        precip_mm = total_raw / 10.0

        print(f"📊 Precipitation: {precip_mm:.1f} mm/year ({len(data['results'])} days with data)")

        # Test BOTH formulas
        print(f"\n🧪 Testing R-factor formulas:")

        # OLD (wrong) constant
        r_old = 0.04887 * (precip_mm ** 1.61)
        print(f"   OLD: R = 0.04887 × {precip_mm:.1f}^1.61 = {r_old:.1f}")

        # NEW (corrected) constant
        r_new = 0.004934 * (precip_mm ** 1.61)
        print(f"   NEW: R = 0.004934 × {precip_mm:.1f}^1.61 = {r_new:.1f}")

        # Compare to expected
        print(f"\n✅ RESULTS:")
        print(f"   Expected: {expected_r}")
        print(f"   Got (NEW): {r_new:.1f}")

        error_pct = abs(r_new - expected_r) / expected_r * 100
        print(f"   Error: {error_pct:.1f}%")

        if error_pct < 15:  # Within 15% is acceptable
            print(f"   Status: ✅ CORRECT (within 15%)")
            return True
        elif error_pct < 30:
            print(f"   Status: ⚠️ ACCEPTABLE (within 30%)")
            return True
        else:
            print(f"   Status: ❌ WRONG (error > 30%)")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


print("=" * 80)
print("TESTING CORRECTED NOAA R-FACTOR FORMULA")
print("=" * 80)

# Test Case 1: Boone, Iowa
test1 = get_noaa_r_factor_corrected(
    lat=41.875,
    lon=-93.910,
    location_name="Boone, Iowa",
    expected_r=160
)

# Test Case 2: Denver, Colorado
test2 = get_noaa_r_factor_corrected(
    lat=39.739,
    lon=-104.990,
    location_name="Denver, Colorado",
    expected_r=50
)

# Summary
print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")

results = [
    ("Boone, Iowa (R=160)", test1),
    ("Denver, Colorado (R=50)", test2)
]

passed = sum(1 for _, result in results if result is True)
total = len(results)

print(f"\nTests passed: {passed}/{total}")

for name, result in results:
    status = "✅ PASS" if result else ("⚠️ PARTIAL" if result is True else "❌ FAIL")
    print(f"  {name}: {status}")

if passed == total:
    print(f"\n🎉 ALL TESTS PASSED!")
    print(f"The corrected constant (0.004934) works correctly!")
    print(f"Ready to update the script.")
elif passed > 0:
    print(f"\n⚠️ PARTIAL SUCCESS - {passed}/{total} tests passed")
    print(f"The formula is better but may need further tuning.")
else:
    print(f"\n❌ ALL TESTS FAILED")
    print(f"The formula still doesn't work.")
    print(f"Keep using state-level R-factors.")

print(f"{'='*80}")
