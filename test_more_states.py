#!/usr/bin/env python3
"""
Extended R-factor test: 10 more states across all US regions
"""

import sys, time
sys.path.insert(0, '/Users/vivekgupta/crp')

import requests
from rfactor_calculator import get_rfactor_with_details
from datetime import datetime, timedelta

def fetch_usgs_hourly_precipitation(lat, lon, days_back=365):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        params = {
            "bBox": f"{lon-0.5},{lat-0.5},{lon+0.5},{lat+0.5}",
            "parameterCd": "00045",
            "siteStatus": "all",
            "format": "json"
        }
        r = requests.get("https://waterservices.usgs.gov/nwis/site", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if 'value' in data and 'sites' in data['value'] and data['value']['sites']:
            site_id = data['value']['sites'][0]['siteCd'][0]['value']
            iv = requests.get("https://waterservices.usgs.gov/nwis/iv", params={
                "sites": site_id,
                "startDT": start_date.strftime("%Y-%m-%d"),
                "endDT": end_date.strftime("%Y-%m-%d"),
                "parameterCd": "00045", "format": "json"
            }, timeout=10)
            iv.raise_for_status()
            ts = iv.json().get('value', {}).get('timeSeries', [])
            if ts:
                vals = ts[0]['values'][0]['value']
                mm = [float(v['value']) * 25.4 for v in vals if v['value'] is not None]
                if len(mm) > 100:
                    return mm
        return None
    except Exception:
        return None

def get_r_factor(lat, lon):
    detected_state = None
    try:
        geo = requests.get(
            f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=10",
            headers={"User-Agent": "CRP_Conservation_Tool_v16_NRCS"}, timeout=5
        )
        geo.raise_for_status()
        addr = geo.json().get("address", {})
        detected_state = addr.get("state") or addr.get("STATE") or addr.get("province")
    except Exception:
        pass
    hourly = fetch_usgs_hourly_precipitation(lat, lon)
    result = get_rfactor_with_details(lat, lon, hourly_precip_data=hourly, state_override=detected_state)
    if result:
        return result['r_factor'], result['method'], result['source'], detected_state
    return None, None, None, None

# 10 states across all US regions
tests = [
    # Northeast
    {"name": "Philadelphia, Pennsylvania", "lat": 39.952, "lon": -75.165, "expected": 125},
    {"name": "Boston, Massachusetts",      "lat": 42.360, "lon": -71.059, "expected": 100},
    # Southeast
    {"name": "Nashville, Tennessee",       "lat": 36.174, "lon": -86.768, "expected": 200},
    {"name": "New Orleans, Louisiana",     "lat": 29.951, "lon": -90.071, "expected": 300},
    # Midwest
    {"name": "Minneapolis, Minnesota",     "lat": 44.977, "lon": -93.265, "expected": 110},
    {"name": "Columbus, Ohio",             "lat": 39.961, "lon": -82.999, "expected": 125},
    # Great Plains
    {"name": "Omaha, Nebraska",            "lat": 41.256, "lon": -95.934, "expected": 115},
    {"name": "Oklahoma City, Oklahoma",    "lat": 35.467, "lon": -97.516, "expected": 175},
    # West
    {"name": "Las Vegas, Nevada",          "lat": 36.175, "lon": -115.136, "expected": 15},
    {"name": "Salt Lake City, Utah",       "lat": 40.760, "lon": -111.891, "expected": 20},
]

print("=" * 72)
print("R-FACTOR TEST: 10 States Across All US Regions")
print("=" * 72)

passed = 0
for t in tests:
    r, method, source, state = get_r_factor(t['lat'], t['lon'])
    if r is not None:
        err = abs(r - t['expected']) / t['expected'] * 100
        ok = err < 25
        if ok:
            passed += 1
        status = "✅" if ok else "❌"
        print(f"\n{status} {t['name']}")
        print(f"   State detected: {state}")
        print(f"   R: {r:.0f}  (expected {t['expected']})  Error: {err:.0f}%")
        print(f"   Method: {method}")
    else:
        print(f"\n❌ {t['name']} — FAILED to retrieve")
    time.sleep(1)  # rate-limit Nominatim

print(f"\n{'=' * 72}")
print(f"RESULT: {passed}/{len(tests)} PASSED")
print("=" * 72)
