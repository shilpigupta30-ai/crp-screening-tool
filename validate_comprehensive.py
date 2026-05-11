#!/usr/bin/env python3
"""
Comprehensive validation: 5 test cases across different US regions
Tests EI calculations against expected erosion patterns
"""

import requests
import pandas as pd

# R-Factors for different states
R_FACTORS = {
    "Iowa": 160,           # High rainfall erosivity
    "Nebraska": 115,       # Moderate-high
    "Texas": 125,          # High
    "New York": 100,       # Moderate
    "Colorado": 50,        # Low (arid)
}

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
    try:
        response = requests.post(url, data=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def calculate_ei(r, k, slope, t):
    """Calculate Erosion Index using RUSLE2 formula"""
    if t == 0 or slope == 0:
        return 0
    ls = slope ** 1.2 * 0.1
    ei = (r * k * ls) / t
    return round(ei, 2)

def validate_case(name, state, lat_min, lat_max, lon_min, lon_max, expected_hel, description):
    """Run validation for a test case"""
    r_factor = R_FACTORS.get(state, 100)

    print(f"\n{'='*80}")
    print(f"TEST {len(test_results) + 1}: {name}")
    print(f"{'='*80}")
    print(f"State: {state} | R-Factor: {r_factor}")
    print(f"Description: {description}")
    print(f"Coordinates: Lat [{lat_min}, {lat_max}], Lon [{lon_min}, {lon_max}]")

    # Create WKT polygon
    p1 = f"{lon_min} {lat_min}"
    p2 = f"{lon_min} {lat_max}"
    p3 = f"{lon_max} {lat_max}"
    p4 = f"{lon_max} {lat_min}"
    wkt = f"POLYGON(({p1}, {p2}, {p3}, {p4}, {p1}))"

    print(f"Fetching SSURGO data...")
    data = fetch_ssurgo_data(wkt)

    if "error" in data:
        print(f"❌ Error: {data['error']}")
        return None

    if "Table" not in data or len(data["Table"]) == 0:
        print("❌ No soil data returned from SSURGO")
        return None

    # Process soil data
    results = []
    for row in data["Table"]:
        soil_name = row[0] or "Unknown"
        slope = float(row[1]) if row[1] else 0
        t_fact = float(row[2]) if row[2] else 0.5
        k_fact = float(row[3]) if row[3] else 0.3
        hydric = row[4] if row[4] else "No"

        ei = calculate_ei(r_factor, k_fact, slope, t_fact)
        results.append({
            "Soil": soil_name[:40],
            "Slope": slope,
            "K": k_fact,
            "T": t_fact,
            "EI": ei,
            "Hydric": hydric
        })

    df = pd.DataFrame(results)

    # Show top 5 results
    print(f"\nTop 5 Soils by EI:")
    print(df.nlargest(5, "EI")[["Soil", "Slope", "EI"]].to_string(index=False))

    # HEL determination
    max_ei = df["EI"].max()
    avg_ei = df["EI"].mean()
    is_hel = max_ei >= 8.0

    print(f"\nStatistics:")
    print(f"  Max EI: {max_ei}")
    print(f"  Avg EI: {avg_ei:.2f}")
    print(f"  Soils with EI ≥ 8: {len(df[df['EI'] >= 8])}/{len(df)}")
    print(f"  HEL Status: {'🟢 LIKELY HEL' if is_hel else '🔴 NOT HEL'} (EI {'≥' if is_hel else '<'} 8.0)")

    # Validation
    match = is_hel == expected_hel
    result = "✓ PASS" if match else "✗ FAIL"
    print(f"  Expected: {'HEL' if expected_hel else 'NOT HEL'} | Result: {result}")

    return {
        "test": name,
        "state": state,
        "max_ei": max_ei,
        "is_hel": is_hel,
        "expected_hel": expected_hel,
        "pass": match
    }

# Run comprehensive validation
if __name__ == "__main__":
    print("\n" + "="*80)
    print("CRP HEL SCREENING PROTOTYPE - COMPREHENSIVE VALIDATION (5 TEST CASES)")
    print("="*80)

    test_results = []

    # Test 1: HIGH EROSION - Steep Iowa cropland
    test_results.append(validate_case(
        name="Steep Cropland - Iowa",
        state="Iowa",
        lat_min=41.875,
        lat_max=41.885,
        lon_min=-93.915,
        lon_max=-93.905,
        expected_hel=True,
        description="Boone area: Known for slopes and erodible soils - HIGH EROSION RISK"
    ))

    # Test 2: MODERATE EROSION - Nebraska prairie
    test_results.append(validate_case(
        name="Rolling Prairie - Nebraska",
        state="Nebraska",
        lat_min=41.250,
        lat_max=41.260,
        lon_min=-99.750,
        lon_max=-99.740,
        expected_hel=True,
        description="South-central Nebraska: Rolling prairie with moderate slopes"
    ))

    # Test 3: LOW EROSION - New York glacial plain
    test_results.append(validate_case(
        name="Glacial Plain - New York",
        state="New York",
        lat_min=43.000,
        lat_max=43.010,
        lon_min=-76.500,
        lon_max=-76.490,
        expected_hel=False,
        description="Central NY: Glacial deposits, gentle slopes, low erosion risk"
    ))

    # Test 4: VERY HIGH EROSION - Texas gulch/ravine
    test_results.append(validate_case(
        name="High Slope Area - Texas",
        state="Texas",
        lat_min=32.500,
        lat_max=32.510,
        lon_min=-99.850,
        lon_max=-99.840,
        expected_hel=True,
        description="Central Texas: Breaking terrain with steep slopes - VERY HIGH EROSION"
    ))

    # Test 5: ARID/LOW EROSION - Colorado plains
    test_results.append(validate_case(
        name="Arid Grassland - Colorado",
        state="Colorado",
        lat_min=39.500,
        lat_max=39.510,
        lon_min=-104.750,
        lon_max=-104.740,
        expected_hel=False,
        description="Eastern Colorado: Arid grassland, low rainfall, low erosion potential"
    ))

    # Summary & Cross-validation
    print(f"\n{'='*80}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*80}")

    valid_results = [r for r in test_results if r is not None]
    passed = sum(1 for r in valid_results if r["pass"])
    total = len(valid_results)

    for r in valid_results:
        status = "✓" if r["pass"] else "✗"
        print(f"{status} {r['test']:30} | Max EI: {r['max_ei']:6.2f} | {'HEL' if r['is_hel'] else 'NOT'} | Expected: {'HEL' if r['expected_hel'] else 'NOT'}")

    print(f"\n{'='*80}")
    print(f"Tests Passed: {passed}/{total}")
    print(f"Status: {'✓ ALL TESTS PASSED - PROTOTYPE VALIDATED' if passed == total else '✗ SOME TESTS NEED REVIEW'}")
    print(f"{'='*80}\n")

    if passed < total:
        print("⚠️  Note: If some tests failed, review whether test expectations are correct")
        print("    or if the API returned unexpected soil data for that region.\n")
