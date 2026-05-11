#!/usr/bin/env python3
"""
Test the wetland assessment logic with sample SSURGO data
Simulates what happens in the main app when results come back
"""

import sys
sys.path.insert(0, '/Users/vivekgupta/crp')

import pandas as pd
from wetland_features import combine_wetland_indicators

print("="*70)
print("TESTING WETLAND ASSESSMENT LOGIC")
print("="*70)

# Simulate SSURGO data that would come back from the API
# This includes the NEW columns we added: Drainage and WaterTable
sample_ssurgo_data = {
    "Soil Type": ["Soil A (5-10%)", "Soil B (10-15%)"],
    "Slope": [7.5, 12.0],
    "T-Fact": [3.5, 4.0],
    "K-Fact": [0.32, 0.28],
    "Hydric": ["Yes", "No"],
    "Drainage": ["Poorly Drained", "Well Drained"],
    "WaterTable": [25.0, 150.0]  # in cm
}

df = pd.DataFrame(sample_ssurgo_data)
print("\n1️⃣ SIMULATED SSURGO DATA:")
print(df)
print()

# Extract what the app would extract
hydric_count = (df["Hydric"].str.strip().str.lower() == "yes").sum()
hydric_pct = round(hydric_count / len(df) * 100) if len(df) > 0 else 0
has_hydric = hydric_count > 0

print(f"2️⃣ EXTRACTED VALUES:")
print(f"  - Hydric count: {hydric_count}/{len(df)}")
print(f"  - Hydric %: {hydric_pct}%")
print(f"  - Has hydric: {has_hydric}")
print()

# Extract drainage class
drainage_classes = df["Drainage"].dropna().unique()
dominant_drainage = drainage_classes[0] if len(drainage_classes) > 0 else None
print(f"  - Drainage classes found: {list(drainage_classes)}")
print(f"  - Dominant drainage: {dominant_drainage}")
print()

# Extract water table depth
watertab_values = df["WaterTable"].dropna()
watertab_depth = watertab_values.mean() if len(watertab_values) > 0 else None
print(f"  - Water table values: {list(watertab_values)}")
print(f"  - Mean water table depth: {watertab_depth} cm")
print()

# Test bounds extraction (simulating what the app does)
current_bounds = [[41.87, -93.91], [41.88, -93.90]]  # [[lat_min, lon_min], [lat_max, lon_max]]
bounds = None
if current_bounds:
    bounds_list = current_bounds
    if len(bounds_list) >= 2:
        bounds = [bounds_list[0][0], bounds_list[0][1], bounds_list[1][0], bounds_list[1][1]]

print(f"3️⃣ BOUNDS EXTRACTION:")
print(f"  - current_bounds: {current_bounds}")
print(f"  - extracted bounds: {bounds}")
print()

# Simulate the wetland assessment
print(f"4️⃣ WETLAND ASSESSMENT TEST:")
print(f"  - WETLAND_FEATURES_AVAILABLE: True (simulated)")
print(f"  - bounds extracted: {bounds is not None}")
print(f"  - will run: {True and bounds}")
print()

if True and bounds:
    print("  ✅ Assessment WOULD RUN")

    # Extract centroid
    polygon_center_lat = (bounds[0] + bounds[2]) / 2
    polygon_center_lon = (bounds[1] + bounds[3]) / 2
    print(f"  - Centroid: lat={polygon_center_lat}, lon={polygon_center_lon}")
    print()

    # Test combine_wetland_indicators with our data
    print("5️⃣ CALLING combine_wetland_indicators():")
    assessment = combine_wetland_indicators(
        hydric_rating="yes" if has_hydric else "no",
        drainage_class=dominant_drainage,
        vegetation=None,  # Would come from NLCD API
        hydrology_ssurgo={"has_hydrology": watertab_depth and watertab_depth <= 60, "watertab_depth_cm": watertab_depth, "hydrology_signal": "Strong" if watertab_depth and watertab_depth <= 30 else ("Possible" if watertab_depth and watertab_depth <= 60 else "None")},
        hydrology_nhd=None  # Would come from NHD API
    )

    print(f"  ✅ Assessment returned successfully!")
    print(f"  - Wetland type: {assessment['wetland_type']}")
    print(f"  - Confidence: {assessment['confidence']}")
    print(f"  - Is likely wetland: {assessment['is_likely_wetland']}")
    print(f"  - Recommendation: {assessment['recommendation']}")
    print()
    print("  Indicators:")
    for indicator, value in assessment['indicators'].items():
        status = "✓" if value else "✗"
        print(f"    {status} {indicator}: {value}")
else:
    print("  ❌ Assessment would NOT RUN")
    print(f"     WETLAND_FEATURES_AVAILABLE: True")
    print(f"     bounds: {bounds}")

print()
print("="*70)
print("TEST COMPLETE")
print("="*70)
