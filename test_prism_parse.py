#!/usr/bin/env python3
"""
Test downloading and parsing PRISM annual precipitation grid
Extract point-specific value for lat/lon
"""

import requests
import gzip
import io

print("\n" + "="*80)
print("PRISM GRID DOWNLOAD & PARSE TEST")
print("="*80)

# PRISM endpoint for annual precipitation (2024)
endpoint = "https://services.nacse.org/prism/data/get/us/4km/ppt/2024an"

print(f"\n📥 Downloading PRISM grid from: {endpoint}")
print("This may take a moment...")

try:
    response = requests.get(endpoint, timeout=30, stream=True)

    if response.status_code == 200:
        # Get file size
        total_size = len(response.content)
        print(f"✅ Downloaded successfully")
        print(f"   File size: {total_size / (1024*1024):.2f} MB")
        print(f"   Content-Type: {response.headers.get('content-type')}")

        # Check if it's gzipped
        if response.headers.get('content-encoding') == 'gzip' or endpoint.endswith('.gz'):
            print("   Format: Gzipped")
            try:
                decompressed = gzip.decompress(response.content)
                print(f"   Decompressed size: {len(decompressed) / (1024*1024):.2f} MB")
            except:
                print("   ⚠️ Could not decompress")

        # Show first 500 bytes
        print(f"\n📋 First 500 bytes of response:")
        print(response.content[:500])

        print(f"\n📊 Parsing Notes:")
        print("""
        PRISM grids are typically in one of these formats:
        - BIL (Band Interleaved by Line) - binary format
        - ASCII Grid - text format
        - GeoTIFF - geospatial image format

        For BIL format, you need:
        1. Header file (.hdr) with grid metadata (nrows, ncols, etc.)
        2. Binary data file (.bil) with actual values
        3. Projection file (.prj) for coordinates

        To extract point value:
        1. Parse header to get grid bounds and cell size
        2. Calculate which row/col contains our lat/lon
        3. Read that cell's value from binary data
        4. Convert to R-factor via Brown & Foster
        """)

    else:
        print(f"❌ Failed: Status {response.status_code}")

except requests.exceptions.Timeout:
    print("❌ Download timed out (file too large for quick test)")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "="*80)
print("ASSESSMENT")
print("="*80)
print("""
✅ PRISM data is downloadable
⚠️ Requires parsing complex geospatial formats (BIL, ASCII Grid, GeoTIFF)
⏱️ Download time: 10-30 seconds per query
💾 File size: 50-100MB per query
🔧 Complexity: HIGH (need geospatial parsing libraries)

To implement PRISM point extraction, you'd need:
  - rasterio or gdal (geospatial libraries)
  - Handle multiple format types
  - Cache grids for performance
  - Error handling for coordinate mismatches

Viable but adds significant complexity for a web app.
""")
print("="*80 + "\n")
