#!/usr/bin/env python3
"""
Deep analysis: Why does the formula work perfectly for Iowa but fail for Colorado?
"""

import requests
import math

NOAA_CDO_TOKEN = "pyhBbWOmnzTdfSJUCpLhDBafxwfCxCbW"

def analyze_location(lat, lon, location_name, expected_r):
    """Deep analysis of NOAA data vs expected R-factor"""

    print(f"\n{'='*80}")
    print(f"ANALYZING: {location_name}")
    print(f"{'='*80}")

    try:
        # Get NOAA data
        extent = f"{lat - 0.5},{lon - 0.5},{lat + 0.5},{lon + 0.5}"
        stations_url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
        stations_params = {"extent": extent, "datasetid": "GHCND", "limit": 100}
        headers = {"token": NOAA_CDO_TOKEN}

        stations_response = requests.get(stations_url, params=stations_params, headers=headers, timeout=10)
        stations_data = stations_response.json()

        selected_station = None
        for station in stations_data["results"]:
            if station.get("maxdate", "")[:4] >= "2023":
                selected_station = station
                break
        if not selected_station:
            selected_station = stations_data["results"][0]

        station_id = selected_station["id"]
        station_name = selected_station.get("name", "Unknown")

        print(f"Station: {station_name}")
        print(f"Expected R-factor: {expected_r}")

        # Get precipitation
        data_url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
        data_params = {
            "datasetid": "GHCND",
            "stationid": station_id,
            "startdate": "2023-01-01",
            "enddate": "2023-12-31",
            "datatypeid": "PRCP",
            "limit": 365
        }

        data_response = requests.get(data_url, params=data_params, headers=headers, timeout=10)
        data = data_response.json()

        precip_records = data["results"]
        total_raw = sum([r["value"] for r in precip_records if r.get("value")])
        precip_mm = total_raw / 10.0
        days_with_precip = len(precip_records)
        avg_daily = precip_mm / 365  # Average daily precipitation including zero days
        avg_precip_days = precip_mm / days_with_precip if days_with_precip > 0 else 0

        print(f"\nPrecipitation Analysis:")
        print(f"  Total annual: {precip_mm:.1f} mm")
        print(f"  Days with data: {days_with_precip}")
        print(f"  Average daily (all days): {avg_daily:.2f} mm/day")
        print(f"  Average on rainy days: {avg_precip_days:.2f} mm/day")
        print(f"  Data coverage: {days_with_precip/365*100:.0f}%")

        # Test different approaches
        print(f"\n🧪 Testing different formulas/approaches:")

        # Approach 1: Direct formula with annual precip
        r1 = 0.004934 * (precip_mm ** 1.61)
        print(f"\n1. Annual precipitation direct:")
        print(f"   R = 0.004934 × {precip_mm:.1f}^1.61 = {r1:.1f}")
        print(f"   Error: {abs(r1 - expected_r) / expected_r * 100:.1f}%")

        # Approach 2: What if formula expects complete year data?
        # Maybe missing days matter?
        full_year_precip = precip_mm * (365 / days_with_precip)
        r2 = 0.004934 * (full_year_precip ** 1.61)
        print(f"\n2. Extrapolate to full year:")
        print(f"   Assume missing days have same avg: {full_year_precip:.1f} mm")
        print(f"   R = 0.004934 × {full_year_precip:.1f}^1.61 = {r2:.1f}")
        print(f"   Error: {abs(r2 - expected_r) / expected_r * 100:.1f}%")

        # Approach 3: What if it's monthly data?
        monthly_avg = precip_mm / 12
        r3 = 0.004934 * (monthly_avg ** 1.61)
        print(f"\n3. Monthly average (annual/12):")
        print(f"   Monthly avg: {monthly_avg:.1f} mm")
        print(f"   R = 0.004934 × {monthly_avg:.1f}^1.61 = {r3:.1f}")
        print(f"   Error: {abs(r3 - expected_r) / expected_r * 100:.1f}%")

        # Approach 4: Reverse - what precipitation would give expected R?
        # R = 0.004934 × P^1.61
        # P = (R / 0.004934)^(1/1.61)
        p_needed = (expected_r / 0.004934) ** (1/1.61)
        print(f"\n4. Reverse calculation - what P gives expected R?")
        print(f"   If R = {expected_r}, then P should be: {p_needed:.1f} mm")
        print(f"   Actual P: {precip_mm:.1f} mm")
        print(f"   Ratio (actual/needed): {precip_mm / p_needed:.2f}x")

        # Approach 5: Check if exponent varies by climate
        # Solve for exponent: expected_r = 0.004934 × precip_mm^exp
        # exp = log(R / 0.004934) / log(P)
        if precip_mm > 0 and expected_r > 0:
            exp_needed = math.log(expected_r / 0.004934) / math.log(precip_mm)
            print(f"\n5. What exponent would work?")
            print(f"   If constant = 0.004934 and P = {precip_mm:.1f}")
            print(f"   Then exponent needed: {exp_needed:.3f}")
            print(f"   Current exponent: 1.610")
            print(f"   Difference: {exp_needed - 1.61:.3f}")

        # Approach 6: Check precipitation against state average
        print(f"\n6. Precipitation vs State Average:")
        state_avg = {
            "Iowa": 850,
            "Colorado": 380,  # Much drier
        }
        for state, avg in state_avg.items():
            if state in location_name:
                print(f"   Typical {state}: {avg} mm/year")
                print(f"   Our NOAA data: {precip_mm:.1f} mm/year")
                print(f"   Difference: {abs(precip_mm - avg)} mm ({abs(precip_mm - avg)/avg*100:.0f}%)")

        return precip_mm, days_with_precip, r1

    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None, None


print("=" * 80)
print("DEEP ANALYSIS: Why does the formula work for Iowa but fail for Colorado?")
print("=" * 80)

iowa_p, iowa_days, iowa_r = analyze_location(41.875, -93.910, "Boone, Iowa", 160)
colorado_p, colorado_days, colorado_r = analyze_location(39.739, -104.990, "Denver, Colorado", 50)

# Compare the two
print(f"\n{'='*80}")
print("COMPARATIVE ANALYSIS")
print(f"{'='*80}")

print(f"\nIowa:")
print(f"  Precipitation: {iowa_p:.1f} mm/year")
print(f"  Data coverage: {iowa_days}/365 days")
print(f"  R-factor result: {iowa_r:.1f} (expected 160)")

print(f"\nColorado:")
print(f"  Precipitation: {colorado_p:.1f} mm/year")
print(f"  Data coverage: {colorado_days}/365 days")
print(f"  R-factor result: {colorado_r:.1f} (expected 50)")

if iowa_p and colorado_p:
    print(f"\nDifference Analysis:")
    print(f"  Colorado precip / Iowa precip: {colorado_p / iowa_p:.2f}x")
    print(f"  Colorado R / Iowa R: {50 / 160:.2f}x")
    print(f"  Should ratio be: {(50/160)**(1/1.61):.2f}x for exponent 1.61")
    print(f"  Actual ratio: {colorado_p / iowa_p:.2f}x")

print(f"\n{'='*80}")
print("HYPOTHESIS")
print(f"{'='*80}")
print("""
The formula might be calibrated specifically for humid continental climates
(like Iowa) where the relationship between precipitation and erosivity
follows the 1.61 exponent pattern.

For dry climates (like Colorado):
- The relationship between P and R might be different
- Different exponent might be needed
- Or different constant

The fact that it works PERFECTLY for Iowa (0% error) suggests:
1. The constant 0.004934 is correct for humid regions
2. But the exponent 1.61 might be region-specific
3. Or there are other variables (seasonality, intensity) we're missing

For Colorado's drier climate, precipitation is more concentrated in
intense summer storms, which might have higher erosivity than the
formula accounts for.
""")

print(f"{'='*80}")
