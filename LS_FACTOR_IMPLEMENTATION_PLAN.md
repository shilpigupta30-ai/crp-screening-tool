# LS-Factor Improvement Plan
## Using USGS 3DEP Elevation Data for Slope Length & Steepness

---

## Current State (v15)
- **Formula:** LS = Slope^1.2 × 0.1
- **Data:** SSURGO slope_h field only (steepness, no length)
- **Error:** ±23% (documented limitation)
- **Issue:** Does not account for actual slope length, only steepness approximation

---

## Target State
- **Formula:** LS = L × S
  - **L** = Slope length factor (from 3DEP elevation flow paths)
  - **S** = Slope steepness factor (from 3DEP elevation gradients)
- **Data:** USGS 3DEP (3D Elevation Program) 30m DEM
- **Error:** ±5% (goal)
- **Benefit:** Real topographic calculation instead of approximation

---

## Implementation Steps

### Phase 1: Data Acquisition
1. **Source:** USGS 3DEP API / OpenTopography API
2. **Resolution:** 30m DEM (standard for US)
3. **Area:** Polygon bounding box + buffer
4. **Format:** GeoTIFF or Cloud Optimized GeoTIFF (COG)

### Phase 2: Slope Calculation
1. **Slope Steepness (S):**
   - Calculate from elevation gradient
   - Use 3×3 pixel neighborhood (Zevenbergen-Thorne method)
   - Output: Percent slope at each pixel
   - Formula: S = tan(slope_angle)^0.8

2. **Slope Length (L):**
   - Calculate flow accumulation from DEM
   - Trace downslope flow paths using D8 algorithm
   - Sum contributing area upstream
   - Formula: L = (flow_accumulation × cell_size / 22.13)^0.4

### Phase 3: LS Factor Combination
- **Per-pixel LS:** L × S
- **Polygon-wide LS:** Area-weighted average across all pixels in polygon
- **Conservative:** Use maximum LS (worst-case) for HEL determination

### Phase 4: Integration
1. Modify `fetch_nrcs_data()` to call new LS calculation
2. Replace hardcoded `LS = Slope^1.2 × 0.1` with dynamic calculation
3. Add graceful fallback to old formula if 3DEP API unavailable
4. Update debug logging to show L, S, and combined LS separately

---

## Data Sources

| Component | Source | API | Rate Limit | Cost |
|-----------|--------|-----|------------|------|
| **3DEP DEM** | USGS | OpenTopography REST API | Generous | Free |
| **Alternative** | USGS | 3DEP Cloud Optimized GeoTIFF | - | Free |
| **Backup** | GEBCO | Global bathymetry/topography | 100 req/min | Free |

**Recommended:** OpenTopography API (easiest, no registration required)

---

## Expected Improvements

| Metric | Before | After | Gain |
|--------|--------|-------|------|
| **LS Error** | ±23% | ±5% | **78% reduction** |
| **Total EI Error** | ~±30% | ~±8% | **73% reduction** |
| **HEL Confidence** | Medium | High | **More reliable** |

### Example Impact
**Field with 12% slope, 150m slope length:**
- Old: LS = 12^1.2 × 0.1 = 0.14
- New: LS = L × S = 2.1 × 0.53 = 1.11
- Difference: **692% more accurate representation**

---

## Technical Challenges

1. **DEM Coverage Gaps:** Voids/missing data in some areas
   - Solution: Fill using interpolation

2. **Flow Path Calculation:** CPU-intensive for large areas
   - Solution: Limit polygon size or pre-process in cloud

3. **Scale Sensitivity:** 30m resolution may miss microslopes
   - Solution: Use 10m resolution where available (higher cost)

4. **Streamlit Cloud Deployment:** May hit memory limits with large DEMs
   - Solution: Cache results, use tiling for big areas

---

## Implementation Timeline

- **Phase 1 (Data):** 1-2 hours — integrate OpenTopography API
- **Phase 2 (Calc):** 3-4 hours — slope & flow accumulation
- **Phase 3 (Combine):** 1 hour — LS factor calculation
- **Phase 4 (Integration):** 2 hours — code integration & testing
- **Testing:** 2-3 hours — validate across multiple regions
- **Total:** ~10-12 hours work

---

## Success Criteria

✅ LS factor calculated from actual elevation data (not approximation)
✅ Slope length AND steepness both reflected (not just slope^1.2)
✅ Error reduced from ±23% to ±5% or better
✅ Falls back gracefully if 3DEP API unavailable
✅ Tested on 5+ regions with different topography (flat, rolling, steep)
✅ Performance acceptable for Streamlit Cloud (~5 sec per query)

---

## Next Steps

1. Research OpenTopography API documentation
2. Write prototype to fetch DEM for test location
3. Implement slope & flow accumulation calculation
4. Test against known USLE/RUSLE2 results
5. Integrate into main application
6. Deploy and gather feedback

**Ready to start Phase 1?**
