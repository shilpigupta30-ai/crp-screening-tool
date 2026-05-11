#!/usr/bin/env python3
"""
Test PRISM API + Brown & Foster R-factor conversion
Validates point-specific R-factor accuracy vs state-level averages
"""

import requests

# Test locations (lat, lon)
TEST_LOCATIONS = {
    "Boone, Iowa (High rainfall)": (41.875, -93.910),
    "Denver, Colorado (Dry)": (39.739, -104.990),
    "Miami, Florida (Very wet)": (25.762, -80.193),
    "Seattle, Washington (Moderate)": (47.609, -122.333),
    "Lubbock, Texas (Arid)": (33.579, -101.855),
}

# State-level R-factors for comparison
STATE_R_FACTORS = {
    "Iowa": 160,
    "Colorado": 50,
    "Florida": 350,
    "Washington": 30,
    "Texas": 125,
}

def get_prism_r_factor(lat, lon):
    """Query PRISM API and convert to R-factor using Brown & Foster equation"""
    try:
        url = f"https://prism.oregonstate.edu/api/v1/annual/{lat},{lon}/bil"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        precip_mm = data.get("ppt", None)

        if precip_mm and precip_mm > 0:
            # Brown & Foster: R ≈ 0.04887 × P^1.61
            r_factor = round(0.04887 * (precip_mm ** 1.61), 1)
            return r_factor, precip_mm
        return None, None
    except Exception as e:
        print(f"  ❌ PRISM API error: {str(e)}")
        return None, None

print("\n" + "="*80)
print("PRISM API + BROWN & FOSTER R-FACTOR VALIDATION")
print("="*80)

for location, (lat, lon) in TEST_LOCATIONS.items():
    print(f"\n{location}")
    print(f"  Coordinates: ({lat}, {lon})")

    # Get point-specific R via PRISM
    r_prism, precip = get_prism_r_factor(lat, lon)

    if r_prism:
        # Extract state for comparison
        state = location.split(",")[-1].strip()
        state_r = STATE_R_FACTORS.get(state, "N/A")

        # Calculate difference
        if state_r != "N/A":
            diff = abs(r_prism - state_r)
            pct_diff = (diff / state_r) * 100 if state_r > 0 else 0
            print(f"  🌧️  Annual Precipitation: {precip:.1f} mm")
            print(f"  📍 Point-specific R (PRISM): {r_prism}")
            print(f"  📊 State-level R (FOTG avg): {state_r}")
            print(f"  📈 Difference: {diff:.1f} ({pct_diff:.1f}%)")
        else:
            print(f"  🌧️  Annual Precipitation: {precip:.1f} mm")
            print(f"  📍 Point-specific R (PRISM): {r_prism}")
    else:
        print(f"  ❌ Could not fetch PRISM data")

print("\n" + "="*80)
print("VALIDATION COMPLETE")
print("="*80 + "\n")
