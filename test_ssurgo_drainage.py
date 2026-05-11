#!/usr/bin/env python3
"""
Test what SSURGO actually returns for drainage class
"""

import requests
import json

# Test WKT polygon (Boone, IA)
wkt = "POLYGON((-93.915 41.875, -93.915 41.885, -93.905 41.885, -93.905 41.875, -93.915 41.875))"

url = "https://sdmdataaccess.nrcs.usda.gov/Tabular/post.rest"

# Test 1: Current query with drainagecl
print("="*70)
print("TEST 1: SSURGO Query with drainagecl")
print("="*70)

query1 = f"""
SELECT mu.muname, c.slope_h, c.tfact, ch.kwfact, c.hydricrating, c.drainagecl
FROM mapunit mu
INNER JOIN component c ON mu.mukey = c.mukey
INNER JOIN chorizon ch ON c.cokey = ch.cokey
WHERE mu.mukey IN (
    SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt}')
)
AND c.majcompflag = 'yes'
AND ch.hzdept_r = 0
"""

payload = {"query": query1, "format": "json"}

try:
    response = requests.post(url, data=payload, timeout=60)
    response.raise_for_status()
    data = response.json()

    if "Table" in data and data["Table"]:
        print(f"\n✅ Query succeeded! Returned {len(data['Table'])} rows")
        print(f"\nColumn headers: {data.get('Columns', [])}")
        print(f"\nFirst 3 rows:")
        for i, row in enumerate(data["Table"][:3]):
            print(f"  Row {i}: {row}")

        # Extract drainage values specifically
        if data.get("Columns"):
            drain_col_idx = None
            for idx, col in enumerate(data["Columns"]):
                if "drainage" in col.lower():
                    drain_col_idx = idx
                    print(f"\n🔍 Found drainage column at index {idx}: '{col}'")
                    break

            if drain_col_idx is not None:
                drainage_values = []
                for row in data["Table"]:
                    if len(row) > drain_col_idx:
                        drainage_values.append(row[drain_col_idx])

                print(f"\n📊 All drainage values returned:")
                for i, val in enumerate(drainage_values):
                    print(f"  {i}: {repr(val)}")

                # Check for None/empty
                none_count = sum(1 for v in drainage_values if v is None)
                print(f"\n⚠️ None count: {none_count}/{len(drainage_values)}")
            else:
                print("\n❌ No drainage column found!")
    else:
        print(f"\n❌ Query failed or returned no data")
        print(f"Response keys: {list(data.keys())}")
        if "Message" in data:
            print(f"Message: {data['Message']}")
        print(f"\nFull response: {json.dumps(data, indent=2)[:500]}")

except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")

# Test 2: Try alternate column name drainagecl vs other possibilities
print("\n" + "="*70)
print("TEST 2: Checking available drainage-related fields")
print("="*70)

query2 = """
SELECT COUNT(*) as table_count
FROM component
WHERE drainagecl IS NOT NULL
LIMIT 1
"""

payload2 = {"query": query2, "format": "json"}

try:
    response = requests.post(url, data=payload2, timeout=60)
    response.raise_for_status()
    data = response.json()

    if "Table" in data:
        print(f"\n✅ Component table has drainagecl field: {data['Table']}")
    else:
        print(f"\n❌ Component table query failed: {data}")

except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
