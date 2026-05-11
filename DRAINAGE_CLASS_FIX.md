# Drainage Class Detection Fix

## Problem
The drainage class indicator was not appearing in the wetland assessment, even though SSURGO was returning valid drainage class data.

## Root Cause
The original code only checked the **first** drainage class returned from SSURGO:
```python
dominant_drainage = drainage_classes[0]  # ❌ Only checks first value
```

When SSURGO returns multiple soil components with different drainage classes, this approach would miss poorly-drained soils if they weren't the first result. For example:
- If results are: `["Moderately well drained", "Somewhat poorly drained", "Well drained"]`
- Old code would only check "Moderately well drained" → no poor drainage detected
- But the field DOES contain "Somewhat poorly drained" soils

## Solution
Changed logic to check if **ANY** component has poor drainage:

### Step 1: Get all drainage values
```python
drainage_classes = df["Drainage"].dropna()
```

### Step 2: Calculate the mode (most common) for display
```python
dominant_drainage = drainage_classes.mode()[0] if len(drainage_classes.mode()) > 0 else drainage_classes.iloc[0]
```

### Step 3: Check if ANY has poor drainage keywords
```python
has_poor_drainage_component = False
for drain_val in drainage_classes:
    if drain_val and any(keyword in str(drain_val).lower() for keyword in ["poorly", "poor", "somewhat poor"]):
        has_poor_drainage_component = True
        break
```

### Step 4: Pass correct value to assessment
```python
drainage_for_assessment = dominant_drainage
if has_poor_drainage_component and dominant_drainage:
    if not any(keyword in str(dominant_drainage).lower() for keyword in ["poorly", "poor", "somewhat poor"]):
        drainage_for_assessment = "Poorly drained"  # Signal presence of poor drainage
```

## What Changed in the UI

### Before:
- Drainage class indicator often didn't show (if poorly-drained soils weren't first in results)
- Display text was generic: "✓ Poor drainage class"

### After:
- ✅ Drainage indicator shows correctly when ANY component is poorly drained
- ✅ Display shows actual value: "✓ Somewhat poorly drained (SSURGO)"
- ✅ Better debug logging tracks which drainage classes were found

## Test Results

With sample SSURGO data:
```
Drainage classes: ['Moderately well drained', 'Somewhat poorly drained', 'Well drained']
Dominant (mode): 'Moderately well drained'
Has poor drainage: True ✅

Result: poor_drainage indicator = True ✓
```

## Files Modified
- `/Users/vivekgupta/crp/crp_final_v12.py` - Wetland assessment section (lines ~1159-1295)

## Next Steps
1. Test locally by drawing a polygon over an area with poorly-drained soils
2. Verify the drainage class indicator now appears in the wetland assessment
3. Check that the indicator shows the specific drainage class value
4. Deploy to HuggingFace when verified
