#!/usr/bin/env python3
"""
Validation script for CRP HEL Screening prototype
Tests EI calculation logic with known coordinates
"""

import requests
import pandas as pd

# R-Factor for Iowa (Midwest)
R_FACTOR_IOWA = 160

def fetch_ssurgo_data(wkt):
    """Query USDA SSURGO for soil data"""
    url = "https://sdmdataaccess.nrcs.usda.gov/Tabular/post.rest"
    query = f"""
    SELECT mu.muname, c.slope_h, c.tfact, ch.kwfact, c.hydricrating
    FROM mapunit mu
    INNER JOIN component c ON mu.mukey = c.mukey
    INNER JOIN chorizon ch ON c.cokey = ch.cokey
    WHERE mu.mukey IN (
        SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt}')
    )
    AND c.majcompflag = 'yes'
    AND ch.hzdept_r = 0
    """
    payload = {"query": query, "format": "json"}
    response = requests.post(url, data=payload, timeout=60)
    return response.json()

def calculate_ei(r, k, slope, t):
    """Calculate Erosion Index using RUSLE2 formula"""
    if t == 0 or slope == 0:
        return 0
    ls = slope ** 1.2 * 0.1
    ei = (r * k * ls) / t
    return round(ei, 2)

def validate_case(name, lat_min, lat_max, lon_min, lon_max, expected_hel):
    """Run validation for a test case"""
    print(f"\n{'='*70}")
    print(f"TEST CASE: {name}")
    print(f"{'='*70}")
    print(f"Coordinates: Lat [{lat_min}, {lat_max}], Lon [{lon_min}, {lon_max}]")

    # Create WKT polygon
    p1 = f"{lon_min} {lat_min}"
    p2 = f"{lon_min} {lat_max}"
    p3 = f"{lon_max} {lat_max}"
    p4 = f"{lon_max} {lat_min}"
    wkt = f"POLYGON(({p1}, {p2}, {p3}, {p4}, {p1}))"

    print(f"Fetching SSURGO data...")
    data = fetch_ssurgo_data(wkt)

    if "Table" not in data or len(data["Table"]) == 0:
        print("❌ No soil data returned from SSURGO")
        return False

    # Process soil data
    results = []
    for row in data["Table"]:
        soil_name = row[0] or "Unknown"
        slope = float(row[1]) if row[1] else 0
        t_fact = float(row[2]) if row[2] else 0.5
        k_fact = float(row[3]) if row[3] else 0.3
        hydric = row[4] if row[4] else "No"

        ei = calculate_ei(R_FACTOR_IOWA, k_fact, slope, t_fact)
        results.append({
            "Soil Type": soil_name,
            "Slope": slope,
            "K-Fact": k_fact,
            "T-Fact": t_fact,
            "EI": ei,
            "Hydric": hydric
        })

    df = pd.DataFrame(results)
    print(f"\n{df.to_string(index=False)}")

    # HEL determination
    max_ei = df["EI"].max()
    is_hel = max_ei >= 8.0

    print(f"\nMax Erosion Index: {max_ei}")
    print(f"HEL Status: {'🟢 LIKELY HEL' if is_hel else '🔴 INELIGIBLE'} (EI {'≥' if is_hel else '<'} 8.0)")

    # Validation
    result = "✓ PASS" if is_hel == expected_hel else "✗ FAIL"
    print(f"Expected: {expected_hel} | Result: {result}")

    return is_hel == expected_hel

# Run validation tests
if __name__ == "__main__":
    print("\n" + "="*70)
    print("CRP HEL SCREENING PROTOTYPE - VALIDATION TEST SUITE")
    print("="*70)

    results = []

    # Test 1: High-erosion Iowa cropland (should be HEL)
    results.append(validate_case(
        name="HIGH EROSION: Boone, IA Cropland",
        lat_min=41.875,
        lat_max=41.885,
        lon_min=-93.915,
        lon_max=-93.905,
        expected_hel=True  # High slope, erodible soil
    ))

    # Test 2: Low-erosion flat area (should NOT be HEL)
    results.append(validate_case(
        name="LOW EROSION: Ames, IA (Flat)",
        lat_min=42.053,
        lat_max=42.063,
        lon_min=-93.633,
        lon_max=-93.623,
        expected_hel=False  # Gentle slopes
    ))

    # Summary
    print(f"\n{'='*70}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*70}")
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Status: {'✓ ALL TESTS PASSED' if passed == total else '✗ SOME TESTS FAILED'}")
    print(f"{'='*70}\n")
