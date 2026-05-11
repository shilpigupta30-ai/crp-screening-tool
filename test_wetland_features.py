#!/usr/bin/env python3
"""
Test wetland feature detection locally before deployment
"""

import sys
sys.path.insert(0, '/Users/vivekgupta/crp')

from wetland_features import (
    get_nlcd_vegetation_type,
    get_nhd_proximity,
    detect_wetland_hydrology_from_ssurgo,
    combine_wetland_indicators
)

print("=" * 70)
print("WETLAND FEATURE DETECTION TEST")
print("=" * 70)

# Test 3 locations: known wetland, non-wetland, mixed
test_locations = [
    {
        "name": "Boone, Iowa (test location)",
        "lat": 41.875,
        "lon": -93.910,
        "expected": "Possibly wetland (hydric soils in area)"
    },
    {
        "name": "Denver, Colorado (dry)",
        "lat": 39.739,
        "lon": -104.990,
        "expected": "Non-wetland (semi-arid)"
    },
    {
        "name": "Miami, Florida (subtropical)",
        "lat": 25.762,
        "lon": -80.193,
        "expected": "Likely wetland (high water table, wetland vegetation)"
    },
]

for location in test_locations:
    print(f"\n{'='*70}")
    print(f"📍 {location['name']}")
    print(f"   Expected: {location['expected']}")
    print("-" * 70)

    lat, lon = location['lat'], location['lon']

    # Test 1: NLCD Vegetation
    print("\n1️⃣ NLCD VEGETATION:")
    vegetation = get_nlcd_vegetation_type(lat, lon)
    if vegetation:
        print(f"   ✅ Result: {vegetation['class_name']}")
        print(f"      Is wetland vegetation: {vegetation['is_wetland_vegetation']}")
    else:
        print(f"   ⚠️ No NLCD data or API unavailable")

    # Test 2: NHD Proximity
    print("\n2️⃣ NHD PROXIMITY (to streams/water):")
    nhd = get_nhd_proximity(lat, lon, search_radius_km=5.0)
    if nhd:
        print(f"   ✅ Result: {nhd['hydrology_signal']} hydrology signal")
        if nhd['nearest_distance_m']:
            print(f"      Distance to water: {nhd['nearest_distance_m']:.0f} meters")
        print(f"      Water body type: {nhd['water_body_type']}")
    else:
        print(f"   ⚠️ No NHD data or API unavailable")

    # Test 3: SSURGO Watertab
    print("\n3️⃣ SSURGO WATERTAB (water table depth):")
    # Using test values - in real app, would fetch from SSURGO
    test_watertab = 25 if "Iowa" in location['name'] else (150 if "Denver" in location['name'] else 50)
    ssurgo_hydro = detect_wetland_hydrology_from_ssurgo(test_watertab)
    print(f"   ✅ Test watertab: {test_watertab} cm")
    print(f"      Hydrology signal: {ssurgo_hydro['hydrology_signal']}")

    # Test 4: Combined Assessment
    print("\n4️⃣ COMBINED ASSESSMENT:")
    assessment = combine_wetland_indicators(
        hydric_rating="yes" if "Iowa" in location['name'] else "no",
        drainage_class="Poorly Drained" if "Iowa" in location['name'] else "Well Drained",
        vegetation=vegetation,
        hydrology_ssurgo=ssurgo_hydro,
        hydrology_nhd=nhd
    )

    print(f"   ✅ Wetland assessment: {assessment['wetland_type']}")
    print(f"      Confidence: {assessment['confidence']}")
    print(f"      Is likely wetland: {assessment['is_likely_wetland']}")
    print(f"      Recommendation: {assessment['recommendation']}")

    # Show indicators
    indicators = assessment['indicators']
    print(f"\n   Indicators:")
    print(f"      Hydric soils: {'✓' if indicators['hydric_soils'] else '✗'}")
    print(f"      Poor drainage: {'✓' if indicators['poor_drainage'] else '✗'}")
    print(f"      Wetland vegetation: {'✓' if indicators['wetland_vegetation'] else '✗'}")
    print(f"      Hydrology (SSURGO): {'✓' if indicators['hydrology_ssurgo'] else '✗'}")
    print(f"      Hydrology (NHD): {'✓' if indicators['hydrology_nhd'] else '✗'}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
