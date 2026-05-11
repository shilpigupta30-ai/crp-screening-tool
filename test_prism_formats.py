#!/usr/bin/env python3
"""
Test different PRISM date format possibilities
"""

import requests

print("\n" + "="*80)
print("TESTING PRISM DATE FORMATS")
print("="*80)

base_url = "https://services.nacse.org/prism/data/get/us/4km/ppt"

# Try different date format variations
date_formats = [
    "202401",      # YYYYMM (January 2024)
    "202412",      # YYYYMM (December 2024 - end of year)
    "2024",        # Just year
    "2023",        # Previous year
    "202312",      # Last available (Dec 2023)
    "2022",        # 2022
]

for date_fmt in date_formats:
    url = f"{base_url}/{date_fmt}"
    print(f"\n🔍 Trying format: {date_fmt}")
    print(f"   URL: {url}")

    try:
        response = requests.head(url, timeout=5)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print(f"   ✅ SUCCESS!")
            # Try to get actual data
            data_response = requests.get(url, timeout=10)
            size_mb = len(data_response.content) / (1024*1024)
            print(f"   Size: {size_mb:.2f} MB")
            print(f"   Content-Type: {data_response.headers.get('content-type')}")
            break

    except Exception as e:
        print(f"   Error: {str(e)}")

print("\n" + "="*80)
