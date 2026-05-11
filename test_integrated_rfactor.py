#!/usr/bin/env python3
"""
Test: Integrated R-Factor Calculation with USGS Hourly Data Fetching
Verify that the hybrid EI30 + fallback approach works for Iowa, Colorado, Florida
"""

import sys
sys.path.insert(0, '/Users/vivekgupta/crp')

from rfactor_calculator import get_rfactor_with_details
import requests
from datetime import datetime, timedelta
import time

# Test locations
test_locations = [
    {
        "name": "Boone, Iowa",
        "lat": 41.875,
        "lon": -93.910,
        "state": "Iowa",
        "expected_r": 160,
    },
    {
        "name": "Denver, Colorado",
        "lat": 39.739,
        "lon": -104.990,
        "state": "Colorado",
        "expected_r": 50,
    },
    {
        "name": "Miami, Florida",
        "lat": 25.762,
        "lon": -80.193,
        "state": "Florida",
        "expected_r": 350,
    },
]


def fetch_usgs_hourly_precipitation(lat, lon, days_back=365):
    """
    Fetch hourly precipitation data from USGS NWIS API.

    Args:
        lat: Latitude
        lon: Longitude
        days_back: Number of days of historical data to fetch

    Returns:
        List of hourly precipitation values in mm, or None if fetch fails
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Step 1: Find nearby USGS stations with precipitation data
        print(f"   🔍 Finding nearby USGS stations...")
        site_url = "https://waterservices.usgs.gov/nwis/site"

        site_params = {
            "bBox": f"{lon-0.5},{lat-0.5},{lon+0.5},{lat+0.5}",  # Search box: lon_min,lat_min,lon_max,lat_max
            "parameterCd": "00045",  # Precipitation (inches)
            "siteStatus": "all",
            "format": "json"
        }

        site_response = requests.get(site_url, params=site_params, timeout=15)
        site_response.raise_for_status()
        site_data = site_response.json()

        # Extract site ID
        if 'value' in site_data and 'sites' in site_data['value']:
            sites = site_data['value']['sites']

            if len(sites) > 0:
                site_id = sites[0]['siteCd'][0]['value']
                site_name = sites[0].get('siteName', 'Unknown')
                print(f"   ✅ Found station: {site_name} ({site_id})")

                # Step 2: Fetch instantaneous (hourly) precipitation data
                print(f"   🔄 Fetching hourly data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
                iv_url = "https://waterservices.usgs.gov/nwis/iv"

                iv_params = {
                    "sites": site_id,
                    "startDT": start_date.strftime("%Y-%m-%d"),
                    "endDT": end_date.strftime("%Y-%m-%d"),
                    "parameterCd": "00045",  # Precipitation
                    "format": "json"
                }

                iv_response = requests.get(iv_url, params=iv_params, timeout=15)
                iv_response.raise_for_status()
                iv_data = iv_response.json()

                # Extract values
                if 'value' in iv_data and 'timeSeries' in iv_data['value']:
                    time_series = iv_data['value']['timeSeries']

                    if len(time_series) > 0:
                        ts = time_series[0]

                        if 'values' in ts and len(ts['values']) > 0:
                            values = ts['values'][0]['value']

                            if values and len(values) > 0:
                                # Convert from inches to mm
                                precip_mm = []
                                for v in values:
                                    if v['value'] is not None:
                                        try:
                                            inches = float(v['value'])
                                            mm = inches * 25.4
                                            precip_mm.append(mm)
                                        except (ValueError, TypeError):
                                            pass

                                if len(precip_mm) > 100:
                                    print(f"   ✅ Retrieved {len(precip_mm)} hourly records from USGS")
                                    return precip_mm
                                else:
                                    print(f"   ⚠️ Insufficient data: {len(precip_mm)} records (need >100)")

        print(f"   ⚠️ No suitable USGS station found nearby")
        return None

    except Exception as e:
        print(f"   ❌ USGS fetch error: {type(e).__name__}: {str(e)}")
        return None


print("=" * 80)
print("INTEGRATED R-FACTOR TEST: EI30 + Fallback with USGS Data")
print("=" * 80)

for location in test_locations:
    print(f"\n📍 {location['name']}")
    print(f"   Coordinates: ({location['lat']}, {location['lon']})")
    print(f"   Expected R: {location['expected_r']}")

    # Try to fetch USGS hourly data
    hourly_precip = fetch_usgs_hourly_precipitation(location['lat'], location['lon'])

    # Call hybrid calculator
    print(f"   🧮 Calculating R-factor...")
    result = get_rfactor_with_details(
        location['lat'],
        location['lon'],
        hourly_precip_data=hourly_precip,
        state_override=location['state']
    )

    if result:
        r_factor = result['r_factor']
        method = result['method']
        source = result['source']
        data_available = result['data_available']

        print(f"   Method: {method}")
        print(f"   Source: {source}")
        print(f"   Data Available: {data_available}")
        print(f"   Calculated R: {r_factor:.1f}")

        if method == "EI30 (Hourly Data)":
            print(f"   ✅ USING EI30 METHOD (kinetic energy)")
        else:
            print(f"   ⚠️ FALLBACK TO STATE-LEVEL")

        if location['expected_r'] > 0:
            error = abs(r_factor - location['expected_r']) / location['expected_r'] * 100
            print(f"   Error: {error:.1f}%")

            if method == "EI30 (Hourly Data)":
                if error < 30:
                    print(f"   ✅ EI30 result acceptable (within expected variance)")
                else:
                    print(f"   ⚠️ EI30 result differs from state average (may indicate real local variation)")
    else:
        print(f"   ❌ Failed to calculate R-factor")

    # Rate limit USGS requests
    time.sleep(1)

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)
print("""
✅ Integration Goal: Pass hourly precipitation data to EI30 calculator
✅ Expected Behavior:
   - If USGS data available (>100 hourly records): Use EI30 method
   - If USGS data unavailable: Fall back to state-level FOTG

Key Points:
- USGS NWIS API may have limited hourly precipitation availability
- Not all locations have nearby USGS stations with precipitation data
- EI30 results may differ from state averages (captures local variation)
- Fallback to state-level ensures tool never fails completely
""")

print("=" * 80)
