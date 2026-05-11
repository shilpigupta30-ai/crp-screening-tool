#!/usr/bin/env python3
"""
VALIDATION TEST: NOAA R-Factor Raster Data
Test if NOAA rasters give CORRECT R-factor values
for known locations before scaling to 2 lakh acres
"""

import os
import requests
from pathlib import Path
import rasterio

# Test locations with EXPECTED R-factors
test_locations = [
    {
        "name": "Boone, Iowa",
        "lat": 41.875,
        "lon": -93.910,
        "state": "Iowa",
        "expected_r": 160,
        "raster_file": "rfactor_iowa.tif"
    },
    {
        "name": "Miami, Florida",
        "lat": 25.762,
        "lon": -80.193,
        "state": "Florida",
        "expected_r": 350,
        "raster_file": "rfactor_florida.tif"
    },
    {
        "name": "Denver, Colorado",
        "lat": 39.739,
        "lon": -104.990,
        "state": "Colorado",
        "expected_r": 50,
        "raster_file": "rfactor_colorado.tif"
    },
]

print("=" * 80)
print("NOAA R-FACTOR RASTER VALIDATION TEST")
print("=" * 80)
print("\n📋 PURPOSE: Validate NOAA raster R-factors are CORRECT before full deployment")
print("⚠️  WARNING: We were burned before - must verify data accuracy first\n")

# Step 1: Check if rasters exist or try to get them
print("1️⃣ Checking for NOAA R-factor raster files...")
print("-" * 80)

rasters_dir = Path("/Users/vivekgupta/crp/noaa_rasters")
rasters_dir.mkdir(exist_ok=True)

# Note: NOAA rasters are large and may not be downloadable via simple HTTP
# For now, we'll note where they should be placed
print(f"📁 Raster directory: {rasters_dir}")
print("\n⚠️  IMPORTANT: NOAA R-factor rasters must be downloaded manually:")
print("   Source: https://www.fisheries.noaa.gov/inport/item/48224")
print("   Download: R-Factor for the Conterminous United States (GeoTIFF format)")
print("   Place downloaded files in:", rasters_dir)
print()

# Check which rasters exist
existing_rasters = list(rasters_dir.glob("*.tif"))
if existing_rasters:
    print(f"✅ Found {len(existing_rasters)} raster file(s):")
    for raster in existing_rasters:
        size_mb = raster.stat().st_size / 1024 / 1024
        print(f"   - {raster.name} ({size_mb:.1f} MB)")
else:
    print("⚠️  No raster files found in directory")
    print("   Skipping validation - please download rasters first\n")

print("\n2️⃣ Testing R-factor values at known locations...")
print("-" * 80)

results = []

for location in test_locations:
    print(f"\n📍 {location['name']}")
    print(f"   Coordinates: ({location['lat']}, {location['lon']})")
    print(f"   Expected R-factor: {location['expected_r']}")

    raster_path = rasters_dir / location['raster_file']

    if not raster_path.exists():
        print(f"   ⚠️  Raster not found: {raster_path.name}")
        results.append({
            "name": location['name'],
            "expected": location['expected_r'],
            "noaa": None,
            "error": None,
            "valid": False
        })
        continue

    try:
        # Open raster and query point value
        with rasterio.open(raster_path) as src:
            # Get pixel coordinates from lat/lon
            row, col = rasterio.transform.rowcol(src.transform, location['lon'], location['lat'])

            # Read the value at that pixel
            if 0 <= row < src.height and 0 <= col < src.width:
                data = src.read(1, window=((row, row+1), (col, col+1)))
                noaa_r = float(data[0, 0]) if data.size > 0 else None
            else:
                noaa_r = None

            if noaa_r is not None and noaa_r > 0:
                # Calculate error
                error_pct = abs(noaa_r - location['expected_r']) / location['expected_r'] * 100

                print(f"   NOAA Raster R: {noaa_r:.1f}")
                print(f"   Error: {error_pct:.1f}%")

                # Validation: <10% error = PASS, <20% = ACCEPTABLE, >20% = FAIL
                if error_pct < 10:
                    status = "✅ EXCELLENT (< 10% error)"
                elif error_pct < 20:
                    status = "⚠️ ACCEPTABLE (< 20% error)"
                else:
                    status = "❌ FAIL (> 20% error)"

                print(f"   Status: {status}")

                results.append({
                    "name": location['name'],
                    "expected": location['expected_r'],
                    "noaa": noaa_r,
                    "error": error_pct,
                    "valid": error_pct < 20
                })
            else:
                print(f"   ❌ Invalid raster value: {noaa_r}")
                results.append({
                    "name": location['name'],
                    "expected": location['expected_r'],
                    "noaa": noaa_r,
                    "error": None,
                    "valid": False
                })

    except Exception as e:
        print(f"   ❌ Error reading raster: {e}")
        results.append({
            "name": location['name'],
            "expected": location['expected_r'],
            "noaa": None,
            "error": None,
            "valid": False
        })

# Step 3: Summary
print("\n" + "=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)

valid_results = [r for r in results if r['noaa'] is not None]
if len(valid_results) > 0:
    passed = sum(1 for r in valid_results if r['valid'])
    total = len(valid_results)

    print(f"\nResults: {passed}/{total} tested locations PASSED validation\n")

    for r in valid_results:
        print(f"  {r['name']:<25} Expected: {r['expected']:>4}  NOAA: {r['noaa']:>6.1f}  Error: {r['error']:>5.1f}%")
        if r['valid']:
            print(f"                            ✅ PASS\n")
        else:
            print(f"                            ❌ FAIL\n")

    print("=" * 80)
    print("DECISION")
    print("=" * 80)

    if passed == total:
        print("""
✅ ALL LOCATIONS VALIDATED - NOAA RASTERS ARE ACCURATE
Ready to proceed with NOAA raster integration for 2 lakh acres.

Next steps:
1. Download rasters for all states in your project
2. Create lookup function using rasterio
3. Integrate into crp_final_v12.py
4. Deploy to Streamlit Cloud with raster files
""")
    elif passed > 0:
        print(f"""
⚠️ PARTIAL SUCCESS ({passed}/{total} validated)
NOAA rasters work for some locations but not all.
Need to investigate why certain states/regions fail.

Action: Check NOAA data quality for failing locations.
""")
    else:
        print("""
❌ VALIDATION FAILED - NOAA RASTERS NOT WORKING
Cannot proceed with NOAA approach.

Options:
1. Check if rasters are at different URL
2. Try different raster format/resolution
3. Contact NOAA directly
4. Revert to state-level R-factors (accept ±20-30% error)
""")
else:
    print("\n⚠️ No raster files to test. Download NOAA rasters first.")
    print("   Source: https://www.fisheries.noaa.gov/inport/item/48224")

print("=" * 80)
