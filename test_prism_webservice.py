#!/usr/bin/env python3
"""
Test PRISM Web Services API for annual precipitation data
Using correct endpoint format: https://services.nacse.org/prism/data/get/us/{resolution}/{datatype}/{date}/
"""

import requests
import json

# Test locations (lat, lon)
TEST_LOCATIONS = {
    "Boone, Iowa": (41.875, -93.910),
    "Denver, Colorado": (39.739, -104.990),
    "Miami, Florida": (25.762, -80.193),
}

# Brown & Foster equation: R ≈ 0.04887 × P^1.61
def precip_to_r(precip_mm):
    """Convert precipitation (mm) to R-factor using Brown & Foster equation"""
    if precip_mm > 0:
        return round(0.04887 * (precip_mm ** 1.61), 1)
    return None

print("\n" + "="*80)
print("PRISM WEB SERVICES API TEST - CORRECT ENDPOINT FORMAT")
print("="*80)

# Test 1: Query annual precipitation endpoint
print("\n📍 Test 1: PRISM Annual Precipitation Web Service")
print("-" * 80)

# Try the correct endpoint format
# Format: https://services.nacse.org/prism/data/get/us/{resolution}/{datatype}/{date}/
endpoint = "https://services.nacse.org/prism/data/get/us/4km/ppt/2024an"

print(f"Endpoint: {endpoint}")
print("Testing endpoint availability...")

try:
    response = requests.head(endpoint, timeout=5)
    print(f"  Status Code: {response.status_code}")
    if response.status_code == 200:
        print("  ✅ Endpoint accessible")
    else:
        print(f"  ⚠️  Status {response.status_code} (may still be valid)")
except Exception as e:
    print(f"  ❌ Error: {str(e)}")

# Test 2: Try a simpler approach - check if PRISM has point query endpoints
print("\n📍 Test 2: Searching for PRISM Point-Specific Query API")
print("-" * 80)

# Try alternative endpoints that might support point queries
endpoints_to_try = [
    "https://prism.oregonstate.edu/api/v1/annual/41.875,-93.910/",  # REST-style
    "https://services.nacse.org/prism/v1/data?lat=41.875&lon=-93.910&type=ppt&period=annual",  # Query param style
    "https://prism.oregonstate.edu/normals/",  # Check normals endpoint
]

for ep in endpoints_to_try:
    print(f"\nTrying: {ep[:60]}...")
    try:
        r = requests.head(ep, timeout=5)
        print(f"  Status: {r.status_code}")
    except Exception as e:
        print(f"  Error: {type(e).__name__}")

# Test 3: Check PRISM documentation source
print("\n📍 Test 3: PRISM Data Formats")
print("-" * 80)
print("""
Note: Based on documentation, PRISM web services appear to:
  - Return gridded data (not point-specific)
  - Provide data in ASCII grid or BIL format
  - Require parsing geographic coordinates from grid files

Possible approach for point-specific data:
  1. Download the annual precipitation grid
  2. Parse lat/lon coordinates
  3. Find grid cell closest to target point
  4. Extract precipitation value
  5. Convert using Brown & Foster equation

However, this is complex and may be overkill for preliminary screening.
""")

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)
print("""
PRISM web services exist but are designed for bulk gridded data downloads,
not point-specific queries. This makes real-time integration complex.

Better alternatives for point-specific R-factors:
  ✅ NOAA CDO API (documented, point-specific)
  ✅ State-level R-factors (current working solution)
  ⏳ PRISM + local grid parsing (complex, slower)

Suggestion: Use state-level R-factors + NOAA CDO for Phase 2.
""")
print("="*80 + "\n")
