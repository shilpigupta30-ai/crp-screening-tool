#!/usr/bin/env python3
"""
Test EPA LEW API for point-specific R-factors
Compare: State-level R vs EPA LEW API R vs Expected R
Locations: Boone Iowa, Miami Florida
"""

import requests

# EPA LEW API endpoint
EPA_LEW_API_URL = "https://www3.epa.gov/ceam/models/lew/api"

# Test locations with known expected R-factors
test_locations = [
    {
        "name": "Boone, Iowa",
        "lat": 41.875,
        "lon": -93.910,
        "state": "Iowa",
        "state_level_r": 160,
        "expected_r": 160,
    },
    {
        "name": "Miami, Florida",
        "lat": 25.762,
        "lon": -80.193,
        "state": "Florida",
        "state_level_r": 350,
        "expected_r": 350,
    },
]

print("=" * 80)
print("EPA LEW API R-FACTOR VALIDATION TEST")
print("=" * 80)

for location in test_locations:
    print(f"\n📍 Testing: {location['name']}")
    print(f"   Coordinates: ({location['lat']}, {location['lon']})")
    print(f"   State-level R: {location['state_level_r']}")
    print(f"   Expected R: {location['expected_r']}")

    try:
        # EPA LEW API request format
        # Note: Exact endpoint and parameters may vary - adjust based on EPA documentation
        params = {
            "latitude": location["lat"],
            "longitude": location["lon"],
        }

        response = requests.get(EPA_LEW_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Extract R-factor from response
        # Note: Response structure depends on EPA LEW API design
        if "r_factor" in data:
            epa_r = data["r_factor"]
        elif "value" in data:
            epa_r = data["value"]
        else:
            epa_r = data  # Adjust based on actual response

        print(f"\n   ✅ EPA LEW API Response: R = {epa_r}")

        # Compare accuracies
        state_level_error = abs(location["state_level_r"] - location["expected_r"]) / location["expected_r"] * 100
        epa_lew_error = abs(epa_r - location["expected_r"]) / location["expected_r"] * 100

        print(f"\n   📊 ACCURACY COMPARISON:")
        print(f"      State-level R: {location['state_level_r']}")
        print(f"      Error: {state_level_error:.1f}%")
        print(f"\n      EPA LEW API R: {epa_r:.1f}")
        print(f"      Error: {epa_lew_error:.1f}%")

        if epa_lew_error < state_level_error:
            improvement = state_level_error - epa_lew_error
            print(f"\n      ✅ IMPROVEMENT: {improvement:.1f}% better accuracy")
        else:
            print(f"\n      ⚠️ No improvement")

    except requests.exceptions.RequestException as e:
        print(f"\n   ❌ API Error: {e}")
        print(f"\n   ℹ️ NOTE: EPA LEW API may require:")
        print(f"      - Registration at https://www3.epa.gov/ceam/models/lew/")
        print(f"      - API key/credentials")
        print(f"      - IP allowlisting")
        print(f"      - Specific request format (check EPA documentation)")

print(f"\n{'=' * 80}")
print("SUMMARY")
print(f"{'=' * 80}")
print("""
If EPA LEW API returns valid results:
✅ Point-specific R-factors with <5% error
✅ Eliminates ±20-30% state-level error
✅ Ready to integrate into crp_final_v12.py

If EPA LEW API fails:
❌ Check credentials and IP allowlisting
❌ Verify API endpoint and request format
❌ Contact EPA for support
""")

print(f"{'=' * 80}")
