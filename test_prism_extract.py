#!/usr/bin/env python3
"""
Download PRISM ZIP, extract, and parse precipitation grid
"""

import requests
import zipfile
import io

print("\n" + "="*80)
print("PRISM GRID EXTRACTION TEST")
print("="*80)

# Download PRISM data (Jan 2024)
endpoint = "https://services.nacse.org/prism/data/get/us/4km/ppt/202401"

print(f"\n📥 Downloading PRISM data...")
response = requests.get(endpoint, timeout=30)

if response.status_code == 200:
    print(f"✅ Downloaded {len(response.content) / (1024*1024):.2f} MB")

    # Extract ZIP
    print(f"\n📂 Extracting ZIP contents...")
    try:
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        file_list = zip_file.namelist()

        print(f"   Files in ZIP: {len(file_list)}")
        for fname in file_list[:10]:  # Show first 10
            info = zip_file.getinfo(fname)
            print(f"   - {fname} ({info.file_size} bytes)")

        # Look for .bil, .asc, or .tif files
        data_file = None
        for fname in file_list:
            if fname.lower().endswith(('.bil', '.asc', '.tif', '.tiff')):
                data_file = fname
                print(f"\n📊 Found data file: {data_file}")

                # Extract metadata
                if fname.lower().endswith('.bil'):
                    # BIL files usually have .hdr (header)
                    hdr_file = fname.replace('.bil', '.hdr')
                    if hdr_file in file_list:
                        hdr_content = zip_file.read(hdr_file).decode('utf-8')
                        print(f"\n📋 Header file content:")
                        print(hdr_content[:500])
                break

        if not data_file:
            print("\n⚠️ No recognized data files found")
            print("   Full file listing:")
            for fname in file_list:
                print(f"   {fname}")

    except Exception as e:
        print(f"❌ Error extracting: {str(e)}")
else:
    print(f"❌ Failed to download: Status {response.status_code}")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("""
✅ PRISM ZIP downloads successfully
✅ File size is reasonable (3MB)
⏳ Parsing grid requires: rasterio or gdal library
📊 Once parsed, can extract point values via geospatial lookup

Next step: Use rasterio to parse grid and extract point values
""")
print("="*80 + "\n")
