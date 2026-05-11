#!/usr/bin/env python3
"""
Test the complete drainage class detection flow
"""

import sys
sys.path.insert(0, '/Users/vivekgupta/crp')

import pandas as pd
from wetland_features import combine_wetland_indicators

print("="*70)
print("TESTING DRAINAGE CLASS DETECTION FLOW")
print("="*70)

# Simulate SSURGO data with multiple drainage classes
ssurgo_data = {
    "Soil Type": ["Spillville-Buckney complex, 2 to 5% slopes",
                  "Luther loam, 0 to 2% slopes",
                  "Kenyon silt loam, 5 to 10% slopes"],
    "Slope": [5, 2, 7],
    "T-Fact": [5, 5, 5],
    "K-Fact": [0.24, 0.28, 0.27],
    "Hydric": ["No", "No", "No"],
    "Drainage": ["Moderately well drained",
                 "Somewhat poorly drained",
                 "Well drained"]
}

df = pd.DataFrame(ssurgo_data)

print("\n1️⃣ SIMULATED SSURGO DATA:")
print(df)
print()

# Extract drainage classes the new way
drainage_classes = df["Drainage"].dropna()
print(f"\n2️⃣ ALL DRAINAGE CLASSES:")
for i, val in enumerate(drainage_classes):
    print(f"  {i}: {repr(val)}")

# Get mode (most common)
mode_val = drainage_classes.mode()[0] if len(drainage_classes.mode()) > 0 else drainage_classes.iloc[0]
print(f"\nMost common (mode): {repr(mode_val)}")

# Check if ANY has poor drainage
has_poor_drainage = False
for drain_val in drainage_classes:
    if drain_val and any(keyword in str(drain_val).lower() for keyword in ["poorly", "poor", "somewhat poor"]):
        has_poor_drainage = True
        print(f"✅ Found poor drainage indicator in: {repr(drain_val)}")
        break

print(f"\nHas poor drainage component: {has_poor_drainage}")
print()

# Now simulate what the app does
drainage_for_assessment = mode_val
if has_poor_drainage and mode_val:
    if not any(keyword in str(mode_val).lower() for keyword in ["poorly", "poor", "somewhat poor"]):
        drainage_for_assessment = "Poorly drained"
        print(f"⚠️ Mode doesn't have poor keywords, using 'Poorly drained' instead")
    else:
        print(f"✅ Mode itself has poor drainage keywords")

print(f"\nDrainage value for assessment: {repr(drainage_for_assessment)}")
print()

# Test combine_wetland_indicators
print(f"\n3️⃣ TESTING combine_wetland_indicators():")
assessment = combine_wetland_indicators(
    hydric_rating="no",
    drainage_class=drainage_for_assessment,
    vegetation=None,
    hydrology_ssurgo=None,
    hydrology_nhd=None
)

print(f"\nAssessment result:")
print(f"  - Is likely wetland: {assessment['is_likely_wetland']}")
print(f"  - Confidence: {assessment['confidence']}")
print(f"  - Wetland type: {assessment['wetland_type']}")
print(f"\nIndicators:")
for indicator, value in assessment['indicators'].items():
    status = "✓" if value else "✗"
    print(f"  {status} {indicator}: {value}")

print()
print("="*70)
print("TEST COMPLETE")
print("="*70)
