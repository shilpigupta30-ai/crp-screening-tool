#!/usr/bin/env python3
"""
Deep analysis: Why is DEM-based LS 2.3x higher than old formula?
"""

import numpy as np
from scipy import ndimage
import matplotlib.pyplot as plt

print("=" * 80)
print("ANALYSIS: DEM-Based LS vs Old Formula Discrepancy")
print("=" * 80)

# Generate same DEM as before
lat, lon = 41.875, -93.910
size = 37
dem = np.zeros((size, size))

np.random.seed(int((lat + lon) * 1000) % (2**31))
for i in range(size):
    for j in range(size):
        dem[i, j] = 350 + (i * 0.5) + (j * 0.3) + np.random.normal(0, 0.2)

print(f"\n📊 DEM Statistics:")
print(f"  Elevation range: {dem.min():.1f}m to {dem.max():.1f}m")
print(f"  Mean elevation: {dem.mean():.1f}m")
print(f"  Cell size: 30m × 30m")

# ============================================================================
# STEP 1: Calculate Slope Steepness (S Factor)
# ============================================================================
print(f"\n" + "=" * 80)
print("STEP 1: Calculate Slope Steepness (S Factor)")
print("=" * 80)

grad_x = ndimage.sobel(dem, axis=1) / (2 * 30)
grad_y = ndimage.sobel(dem, axis=0) / (2 * 30)
slope_rad = np.arctan(np.sqrt(grad_x**2 + grad_y**2))
slope_pct = np.tan(slope_rad) * 100

print(f"\nSlope percentages:")
print(f"  Min: {np.min(slope_pct):.2f}%")
print(f"  Max: {np.max(slope_pct):.2f}%")
print(f"  Mean: {np.mean(slope_pct):.2f}%")
print(f"  Median: {np.median(slope_pct):.2f}%")

# S factor calculation
s_factor = np.where(
    slope_pct < 10.2,
    0.43 + 0.30 * (slope_pct/100) + 0.043 * (slope_pct/100)**2,
    16.8 * np.sin(slope_rad) - 0.50
)

print(f"\nS Factor (steepness):")
print(f"  Min: {np.min(s_factor):.3f}")
print(f"  Max: {np.max(s_factor):.3f}")
print(f"  Mean: {np.mean(s_factor):.3f}")
print(f"  Median: {np.median(s_factor):.3f}")

# ============================================================================
# STEP 2: Calculate Slope Length (L Factor)
# ============================================================================
print(f"\n" + "=" * 80)
print("STEP 2: Calculate Slope Length (L Factor) from Flow Accumulation")
print("=" * 80)

flow_accum = np.ones((size, size))
for i in range(1, size-1):
    for j in range(1, size-1):
        neighbors = [
            dem[i-1, j-1], dem[i-1, j], dem[i-1, j+1],
            dem[i, j-1], dem[i, j+1],
            dem[i+1, j-1], dem[i+1, j], dem[i+1, j+1]
        ]
        higher_neighbors = sum(1 for n in neighbors if n > dem[i, j])
        flow_accum[i, j] += higher_neighbors * 0.5

print(f"\nFlow Accumulation (number of contributing cells):")
print(f"  Min: {np.min(flow_accum):.0f}")
print(f"  Max: {np.max(flow_accum):.0f}")
print(f"  Mean: {np.mean(flow_accum):.2f}")
print(f"  Median: {np.median(flow_accum):.2f}")

# L factor formula: L = (flow_accum × cell_size / 22.13)^0.4
l_factor = (flow_accum * 30 / 22.13) ** 0.4

print(f"\nL Factor (slope length):")
print(f"  Min: {np.min(l_factor):.3f}")
print(f"  Max: {np.max(l_factor):.3f}")
print(f"  Mean: {np.mean(l_factor):.3f}")
print(f"  Median: {np.median(l_factor):.3f}")

# ============================================================================
# STEP 3: Combine into LS Factor
# ============================================================================
print(f"\n" + "=" * 80)
print("STEP 3: Combine L × S into LS Factor")
print("=" * 80)

ls_factor_pixel = l_factor * s_factor

print(f"\nLS Factor (L × S) per pixel:")
print(f"  Min: {np.min(ls_factor_pixel):.3f}")
print(f"  Max: {np.max(ls_factor_pixel):.3f}")
print(f"  Mean: {np.mean(ls_factor_pixel):.3f}")
print(f"  Median: {np.median(ls_factor_pixel):.3f}")
print(f"  Std Dev: {np.std(ls_factor_pixel):.3f}")

# Different aggregation methods
ls_mean = np.mean(ls_factor_pixel)
ls_median = np.median(ls_factor_pixel)
ls_max = np.max(ls_factor_pixel)

print(f"\n📊 Different Aggregation Methods:")
print(f"  Area-weighted average: {ls_mean:.3f}")
print(f"  Median: {ls_median:.3f}")
print(f"  Maximum (conservative): {ls_max:.3f}")

# ============================================================================
# STEP 4: Compare with Old Formula
# ============================================================================
print(f"\n" + "=" * 80)
print("STEP 4: Compare with Old Formula (Slope^1.2 × 0.1)")
print("=" * 80)

# Old formula applied to each pixel
old_ls_pixel = (slope_pct ** 1.2) * 0.1

print(f"\nOld LS Formula (Slope^1.2 × 0.1) per pixel:")
print(f"  Min: {np.min(old_ls_pixel):.3f}")
print(f"  Max: {np.max(old_ls_pixel):.3f}")
print(f"  Mean: {np.mean(old_ls_pixel):.3f}")
print(f"  Median: {np.median(old_ls_pixel):.3f}")

# ============================================================================
# STEP 5: Root Cause Analysis
# ============================================================================
print(f"\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS")
print("=" * 80)

print(f"""
❓ WHY IS DEM LS 2.3x HIGHER?

Current Implementation:
  We use: LS = np.max(l_factor * s_factor) = {ls_max:.3f}
  This is the MAXIMUM LS across all pixels (conservative)

If we used mean instead:
  LS = np.mean(l_factor * s_factor) = {ls_mean:.3f}
  This is 2.3x LOWER than max

Old Formula gives:
  LS = mean(slope^1.2 × 0.1) = {np.mean(old_ls_pixel):.3f}

EXPLANATION:
1. L Factor (slope length) = {np.mean(l_factor):.3f} (mostly 1.1-1.7)
   This comes from flow accumulation and adds VOLUME

2. S Factor (steepness) = {np.mean(s_factor):.3f}
   This is multiplicative on top of L

3. Old formula has implicit scaling: 0.1 multiplier
   New formula: L × S has no scaling factor

4. We use MAX pixel value, not mean
   Max LS occurs where high flow + steep slope meet
   This is conservative for HEL determination

COMPARISON:
Old method: {np.mean(old_ls_pixel):.3f} (mean across all pixels)
New method - MEAN: {ls_mean:.3f}
New method - MAX: {ls_max:.3f}

Ratio (max/old): {ls_max / np.mean(old_ls_pixel):.2f}x higher
Ratio (mean/old): {ls_mean / np.mean(old_ls_pixel):.2f}x higher
""")

print("\n" + "=" * 80)
print("POTENTIAL ISSUES & SOLUTIONS")
print("=" * 80)

issues = [
    {
        "issue": "We use MAX LS, not MEAN",
        "impact": f"Overshoots true field LS by picking worst pixel (max={ls_max:.3f} vs mean={ls_mean:.3f})",
        "solution": "Use area-weighted MEAN or MEDIAN instead of MAX"
    },
    {
        "issue": "Missing scaling factor in DEM approach",
        "impact": "Old formula has ×0.1 scaling, new formula is raw L×S (no scaling)",
        "solution": "Check if RUSLE2 spec includes a scaling constant"
    },
    {
        "issue": "Old formula might be TOO SIMPLE",
        "impact": "Slope^1.2 × 0.1 ignores actual flow paths and accumulation",
        "solution": "This could actually be CORRECT improvement (not a bug)"
    },
    {
        "issue": "L factor calculation might be wrong",
        "impact": f"L={np.mean(l_factor):.3f} seems high; flow_accum={np.mean(flow_accum):.2f}",
        "solution": "Validate against official RUSLE2 L factor examples"
    }
]

for i, item in enumerate(issues, 1):
    print(f"\n{i}. {item['issue']}")
    print(f"   Impact: {item['impact']}")
    print(f"   Solution: {item['solution']}")

print(f"\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

print(f"""
🔍 DIAGNOSIS: The discrepancy is likely due to:
   1. Using MAX pixel LS instead of area-weighted mean
   2. Lack of scaling factor in DEM approach (0.1 multiplier)
   3. L factor calculation is picking up real slope accumulation

✅ CORRECT APPROACH:
   Switch from np.max() to np.mean() or np.median()
   This would give LS ≈ {ls_mean:.3f} instead of {ls_max:.3f}
   Much closer to old formula {np.mean(old_ls_pixel):.3f}

⚠️  BEFORE DEPLOYING:
   1. Change: ls_factor = np.max(...) → ls_factor = np.mean(...)
   2. Retest and verify EI values are reasonable
   3. Validate against RUSLE2 reference data
   4. Get Kristie's review
""")

print("\n" + "=" * 80)
