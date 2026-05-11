#!/usr/bin/env python3
"""
Live test of get_state_r_factor() as called in crp_final_v12.py
Simulates what happens when user draws a polygon for Georgia, Kansas, Oregon
"""

import sys
sys.path.insert(0, '/Users/vivekgupta/crp')

import importlib.util
import requests
from rfactor_calculator import get_rfactor_with_details
from datetime import datetime, timedelta

# Replicate fetch_usgs_hourly_precipitation exactly as in crp_final_v12.py
def fetch_usgs_hourly_precipitation(lat, lon, days_back=365):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        url = "https://waterservices.usgs.gov/nwis/site"
        params = {
            "bBox": f"{lon-0.5},{lat-0.5},{lon+0.5},{lat+0.5}",
            "parameterCd": "00045",
            "siteStatus": "all",
            "format": "json"
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        site_data = response.json()
        if 'value' in site_data and 'sites' in site_data['value']:
            sites = site_data['value']['sites']
            if len(sites) > 0:
                site_id = sites[0]['siteCd'][0]['value']
                iv_params = {
                    "sites": site_id,
                    "startDT": start_date.strftime("%Y-%m-%d"),
                    "endDT": end_date.strftime("%Y-%m-%d"),
                    "parameterCd": "00045",
                    "format": "json"
                }
                iv_response = requests.get("https://waterservices.usgs.gov/nwis/iv", params=iv_params, timeout=15)
                iv_response.raise_for_status()
                iv_data = iv_response.json()
                if 'value' in iv_data and 'timeSeries' in iv_data['value']:
                    ts_list = iv_data['value']['timeSeries']
                    if len(ts_list) > 0:
                        values = ts_list[0]['values'][0]['value']
                        if values:
                            precip_mm = [float(v['value']) * 25.4 for v in values if v['value'] is not None]
                            if len(precip_mm) > 100:
                                return precip_mm
        return None
    except Exception:
        return None


def get_state_r_factor(lat, lon):
    """Exact replica of get_state_r_factor() from crp_final_v12.py (after fix)"""
    # Detect state first (Nominatim)
    detected_state = None
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=10"
        headers = {"User-Agent": "CRP_Conservation_Tool_v16_NRCS"}
        geo_resp = requests.get(url, headers=headers, timeout=5)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
        addr = geo_data.get("address", {})
        detected_state = addr.get("state") or addr.get("STATE") or addr.get("province")
    except Exception as e:
        print(f"   ⚠️ Nominatim failed: {e}")

    hourly_precip = fetch_usgs_hourly_precipitation(lat, lon)
    result = get_rfactor_with_details(lat, lon, hourly_precip_data=hourly_precip, state_override=detected_state)
    if result and 'r_factor' in result:
        r_factor = result['r_factor']
        method = result['method']
        source = result['source']
        source_label = f"{method} - {source}"
        return r_factor, source_label, method
    return None, None, None


# Three new test states
tests = [
    {"name": "Atlanta, Georgia",    "lat": 33.749, "lon": -84.388, "expected": 300},
    {"name": "Wichita, Kansas",     "lat": 37.688, "lon": -97.336, "expected": 100},
    {"name": "Portland, Oregon",    "lat": 45.523, "lon": -122.676, "expected": 50},
]

print("=" * 70)
print("LIVE INTERNAL TEST — Georgia, Kansas, Oregon")
print("(Exact replica of crp_final_v12.py get_state_r_factor() call)")
print("=" * 70)

all_ok = True
for t in tests:
    print(f"\n📍 {t['name']}")
    r, label, method = get_state_r_factor(t['lat'], t['lon'])
    if r is not None:
        err = abs(r - t['expected']) / t['expected'] * 100
        status = "✅ PASS" if err < 25 else "❌ FAIL"
        if err >= 25:
            all_ok = False
        print(f"   R-factor:  {r:.1f}  (expected {t['expected']})")
        print(f"   Method:    {method}")
        print(f"   Source:    {label}")
        print(f"   Error:     {err:.1f}%  {status}")
    else:
        print(f"   ❌ Failed to retrieve R-factor")
        all_ok = False

print("\n" + "=" * 70)
print("OVERALL:", "✅ ALL PASS" if all_ok else "❌ SOME FAILED")
print("=" * 70)
