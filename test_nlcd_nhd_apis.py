#!/usr/bin/env python3
"""
Test NLCD and NHD APIs to see what's failing
"""

import requests
import json
import socket

print("="*70)
print("TESTING NLCD AND NHD APIs")
print("="*70)

# Test DNS resolution first
print("\n1️⃣ DNS RESOLUTION TEST:")
test_domains = [
    "gis.vt.state.vt.us",
    "gis.usgs.gov",
    "arcgis.com",
    "services.arcgisonline.com"
]

for domain in test_domains:
    try:
        ip = socket.gethostbyname(domain)
        print(f"   ✅ {domain} → {ip}")
    except socket.gaierror as e:
        print(f"   ❌ {domain} → ERROR: {e}")

# Test NLCD endpoint
print("\n2️⃣ NLCD API TEST:")
lat, lon = 41.875, -93.910

try:
    url = "https://gis.vt.state.vt.us/arcgis/rest/services/EarthCover/NLCD2019/ImageServer/sample"
    params = {
        "geometry": json.dumps({"x": lon, "y": lat}),
        "geometryType": "esriGeometryPoint",
        "f": "json"
    }

    print(f"   URL: {url}")
    print(f"   Params: {params}")

    response = requests.get(url, params=params, timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ NLCD API responded successfully")
        print(f"      Data: {data}")
    else:
        print(f"   ❌ NLCD API returned {response.status_code}")

except Exception as e:
    print(f"   ❌ NLCD API error: {type(e).__name__}: {e}")

# Test NHD endpoint
print("\n3️⃣ NHD API TEST:")

try:
    url = "https://gis.vt.state.vt.us/arcgis/rest/services/EarthCover/NHD/MapServer/0/query"

    radius_degrees = 5.0 / 111.0
    bbox = {
        "xmin": lon - radius_degrees,
        "ymin": lat - radius_degrees,
        "xmax": lon + radius_degrees,
        "ymax": lat + radius_degrees
    }

    params = {
        "geometry": json.dumps(bbox),
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "outSR": json.dumps({"wkid": 4326}),
        "f": "json",
        "returnGeometry": True,
        "returnDistinctValues": False,
        "outFields": "*"
    }

    print(f"   URL: {url}")
    print(f"   BBox: {bbox}")

    response = requests.get(url, params=params, timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ NHD API responded successfully")
        if "features" in data:
            print(f"      Found {len(data['features'])} features")
    else:
        print(f"   ❌ NHD API returned {response.status_code}")

except Exception as e:
    print(f"   ❌ NHD API error: {type(e).__name__}: {e}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
