# Testing the Drainage Class Fix

## Summary of Fix
The drainage class indicator was not showing in wetland assessments because the code only checked the **first** drainage class from SSURGO. If poorly-drained soils weren't first in the results, they'd be missed.

**Fixed:** Now checks if **ANY** component has poor drainage keywords like "poorly", "somewhat poorly", etc.

---

## How to Test Locally

### Step 1: Start the Streamlit App
```bash
cd /Users/vivekgupta/crp
streamlit run crp_final_v12.py
```

The app will open at `http://localhost:8501`

### Step 2: Navigate to Test Location
In the sidebar, select one of these regions:
- **"Boone, IA (High Erosion)"** ← Recommended (known to have diverse drainage classes)
- "Ames, IA (Flat)"
- "Mississippi Delta, MS"

Click "Jump to Region"

### Step 3: Draw a Polygon
Use the map's Draw tool (toolbar button) to draw a rectangle over the region. A blue highlighted area will appear.

### Step 4: Check the Wetland Assessment Section
Once soil data loads, scroll down to find the wetland assessment box.

### What to Look For

#### Before Fix (❌ Would show):
```
💧 Wetland Soils Detected
No hydric soils detected...
```
(No drainage indicator visible)

#### After Fix (✅ Should now show):
```
🌊 Wetland (type unknown)
Confidence: Low

✓ Hydric soils (SSURGO)
✓ Somewhat poorly drained (SSURGO)    ← NEW! Shows specific drainage class
✓ High water table (SSURGO) [if present]
```

---

## Debug Info Available

Click the **"🔍 Wetland Assessment Debug Info"** expander to see:
- WETLAND_FEATURES_AVAILABLE: true/false
- bounds extracted: true/false  
- assessment will run: true/false

This helps diagnose if the assessment is running at all.

---

## Expected Behaviors by Region

### Boone, IA (High Erosion)
- Multiple soil types with mixed drainage classes
- Should detect: "Somewhat poorly drained" or "Poorly drained" soils
- ✅ Drainage indicator SHOULD show

### Mississippi Delta
- Known for hydric soils + poor drainage
- ✅ Should show both hydric AND drainage indicators

### Well-Drained Areas (Ames, IA)
- Mostly "Well drained" or "Moderately well drained"
- ✅ Drainage indicator should NOT show (correct)

---

## Key Test Cases

| Area | Expected Result | What It Tests |
|------|-----------------|----------------|
| Boone, IA | Drainage indicator shows | Detects any poorly-drained component |
| Mississippi Delta | Multiple indicators | Works with hydric + drainage combo |
| Ames, IA | No drainage indicator | Doesn't false-positive on well-drained |

---

## Debugging Steps If Still Not Showing

1. **Check if bounds are extracted:**
   - Look at debug info: `bounds extracted: true/false`
   - If false, ensure polygon is drawn (not just precision entry)

2. **Check debug logs:**
   - Look for: `Drainage classes found: [...]`
   - Should show all drainage values from SSURGO
   - Example: `['Somewhat poorly drained', 'Moderately well drained']`

3. **Check if any component has poor keywords:**
   - Debug should show: `Has poor drainage component: true/false`
   - If true, indicator SHOULD appear

4. **Verify wetland assessment runs:**
   - Debug should show: `assessment will run: true`
   - If false, check bounds and WETLAND_FEATURES_AVAILABLE

---

## Files Changed
- `crp_final_v12.py` - Wetland assessment logic (~lines 1159-1295)
- `research_ssurgo_fields.md` - Documentation updated
- `DRAINAGE_CLASS_FIX.md` - Detailed technical explanation

## Next Steps After Testing
1. Verify drainage indicator appears correctly
2. Test on 2-3 different regions
3. If working ✅ → Deploy to HuggingFace Spaces
4. Send to Kristie for expert feedback
