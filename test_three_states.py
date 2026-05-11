#!/usr/bin/env python3
"""
Test R-factor integration for 3 new states: Georgia, Kansas, Oregon
"""

import sys
sys.path.insert(0, '/Users/vivekgupta/crp')

from rfactor_calculator import get_rfactor_with_details

test_locations = [
    {
        "name": "Atlanta, Georgia",
        "lat": 33.749,
        "lon": -84.388,
        "state": "Georgia",
        "expected_r": 300,
    },
    {
        "name": "Wichita, Kansas",
        "lat": 37.688,
        "lon": -97.336,
        "state": "Kansas",
        "expected_r": 100,
    },
    {
        "name": "Portland, Oregon",
        "lat": 45.523,
        "lon": -122.676,
        "state": "Oregon",
        "expected_r": 50,
    },
]

print("=" * 70)
print("R-FACTOR TEST: Georgia, Kansas, Oregon")
print("=" * 70)

all_pass = True
for loc in test_locations:
    print(f"\n📍 {loc['name']}")
    print(f"   Coordinates: ({loc['lat']}, {loc['lon']})")
    print(f"   Expected R (NRCS FOTG): {loc['expected_r']}")

    result = get_rfactor_with_details(
        loc['lat'], loc['lon'],
        hourly_precip_data=None,  # Simulate current state (no USGS data)
        state_override=loc['state']
    )

    if result:
        r = result['r_factor']
        method = result['method']
        source = result['source']
        error = abs(r - loc['expected_r']) / loc['expected_r'] * 100

        print(f"   Calculated R: {r:.1f}")
        print(f"   Method: {method}")
        print(f"   Source: {source}")
        print(f"   Error vs expected: {error:.1f}%")

        if error == 0:
            print(f"   ✅ EXACT MATCH (state-level lookup working)")
        elif error < 20:
            print(f"   ✅ PASS (within 20% tolerance)")
        else:
            print(f"   ❌ FAIL (>{20}% error)")
            all_pass = False
    else:
        print(f"   ❌ Failed to get R-factor")
        all_pass = False

print("\n" + "=" * 70)
print("RESULT:", "✅ ALL PASS" if all_pass else "❌ SOME FAILED")
print("=" * 70)
