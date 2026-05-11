# SSURGO Field Research

## What we need:
1. Drainage class field name
2. Water table depth field name

## NRCS SSURGO Documentation:
- Main source: https://www.nrcs.usda.gov/resources/data-and-reports/soil-survey-geographic-database-ssurgo
- Soil Data Access (SDA) API: https://sdmdataaccess.sc.egov.usda.gov/

## SSURGO Table Structure:
- Component (c) table: soil component properties
- Comonth (comonth) table: component monthly water table data  
- Copmgrp (copmgrp) table: component map unit group data
- Chorizon (ch) table: component horizon (layer) data

## Known Field Names:
### Component (c) table:
- `compname` - component name
- `majcompflag` - major component flag
- `hydricrating` - ✅ hydric rating (we're using this)
- `drainagecl` - ✅ **CONFIRMED VALID** - Returns values like "Somewhat poorly drained", "Well drained", etc.
- `loamyclay_h`, `silt_h`, etc. - horizon percentages

### Comonth (comonth) table:
- `comonthkey` - comonth key
- `cokey` - component key
- `monsymbol` - month symbol
- `watertab_l` - water table depth low (cm)
- `watertab_h` - water table depth high (cm)
- `watertab_r` - water table depth representative (cm) ⚠️ Exists but SDA join syntax needs work
  - Joining to component table causes 400 errors
  - May require different SDA endpoint or query structure
  - Currently: set to None for stability

### Component horizon (chorizon) table:
- `hzdept_r` - horizon depth top
- `hzdepb_r` - horizon depth bottom

## Status Update (May 11, 2026):
- **Drainage class**: ✅ **WORKING** - Field `drainagecl` is valid and returning proper values
  - Issue found and fixed: Code was only checking first drainage value, not all components
  - Now checks if ANY component has poor drainage keywords
  - Indicator now displays correctly with specific drainage class value
  
- **Water table depth**: ⚠️ **NEEDS SDA QUERY FIX** - Field exists but comonth joins cause 400 errors
  - Possible solutions:
    1. Use different SDA endpoint/format for comonth data
    2. Use component-level hydric rating as proxy instead
    3. Implement separate API call for water table data
    4. Use NHD proximity as alternative hydrology signal

## Completed Action Items:
1. ✅ Confirmed drainagecl field is valid and returns values like "Somewhat poorly drained"
2. ✅ Fixed logic to check ALL drainage classes, not just first one
3. ✅ Added debug logging to track drainage classes found
4. ✅ Enhanced UI display to show specific drainage class value

## Remaining Action Items:
1. Implement comonth table query (water table depth) - requires SDA syntax research
2. Consider using hydric rating thresholds as alternative hydrology proxy
3. Verify NHD proximity works as fallback hydrology indicator
4. Deploy updated code to HuggingFace Spaces
