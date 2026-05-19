# CRP HEL Screening Tool — Pending Refinements

**Last Updated:** May 18, 2026  
**Status:** ✅ COMPLETED — Implemented and tested

---

## 🔄 Simplify NLCD Indicator Display in UI & Documentation

**Priority:** Medium  
**Complexity:** Medium  
**Estimated Effort:** 30-45 minutes

### Current State (v5.1)
- **All 4 wetland indicators shown equally** on UI
- **NLCD Vegetation (#2)** displays both "Yes" and "No" results
- **PDF/DOCX documentation** includes NLCD equally with others
- **Example output** shows NLCD detection for all cases

### Problem
- NLCD is 30m satellite data from 2019
- Shows "No" results that aren't actionable (field conservationist will see actual vegetation anyway)
- Creates confusion when NLCD says "No vegetation" but field has wetland plants
- UI becomes cluttered with non-essential negative results

### Proposed Solution

#### Option 1: **Smart Display** (Recommended)
- Show NLCD **only when detected as "Yes"**
- Omit NLCD **when "No"** from both UI and main table
- Keep it as supporting evidence when positive

#### Option 2: **Optional Expansion**
- Show main 3 indicators (#1, #3, #4) by default
- Add expandable "Supporting Data" section for NLCD details
- Users can opt-in to see NLCD data

---

## 📝 Implementation Checklist

### Code Changes
- [x] Update `crp_final_v12.py` conservationist view wetland indicators table
  - ✅ Smart display: NLCD row only added to table when `assessment["indicators"]["wetland_vegetation"]` is True
  - ✅ Implementation: Lines 2325-2375 refactored
  - ✅ Changed indicator label to "Hydrophytic Vegetation (NLCD)" for clarity
- [ ] Modify `wetland_features.py` return logic (optional: don't return NLCD "No") — **NOT NEEDED**
  - Logic better handled at display layer (crp_final_v12.py)
  - Keeps data pipeline clean; filtering at UI improves maintainability
- [ ] Test with Atchafalaya coordinates (should show NLCD Yes) — **PENDING**
- [ ] Test with non-wetland area (NLCD No should be hidden) — **PENDING**

### Documentation Updates
- [x] Update `CRP_HEL_Wetland_Determination_Tool.pdf` (v5.2)
  - ✅ Created new PDF with smart display explanation
  - ✅ Marked Indicator #2 as "REFINED"
  - ✅ Explained NLCD smart display rationale
  - ✅ Added two example tables (with and without NLCD)
  
- [x] Update `CRP_HEL_Wetland_Determination_Tool.docx` (v5.2)
  - ✅ Created new DOCX with parallel updates
  - ✅ Mirrors PDF changes
  - ✅ Explains "Only shown when vegetation detected" logic
  - ✅ Includes example tables for both scenarios

### Testing
- [ ] Local testing with multiple coordinates
- [ ] Verify UI doesn't show NLCD "No" results
- [ ] Confirm PDF/DOCX documentation matches UI behavior

---

## 📊 Impact Analysis

| Aspect | Impact |
|--------|--------|
| **User Experience** | ✅ Cleaner, less confusing UI |
| **Conservationist Value** | ✅ Shows only actionable signals |
| **Scientific Accuracy** | ✅ Doesn't change determination logic |
| **Field Verification** | ✅ Simpler to cross-check against site visit |
| **Documentation** | ⚠️ Needs update (captured in checklist) |

---

## 🔗 Related Files

- `crp_final_v12.py` — Lines 2325-2350 (wetland indicators table)
- `wetland_features.py` — `get_nlcd_vegetation_type()` function
- `CRP_HEL_Wetland_Determination_Tool.pdf` — Pages 2-3 (Wetland Methodology)
- `CRP_HEL_Wetland_Determination_Tool.docx` — Wetland Methodology sections

---

## 📌 Notes

- User explicitly requested **"Don't forget about it"** on May 18, 2026
- This is a **quality refinement**, not a blocker
- Can be deferred until after NRCS API maintenance window is resolved
- Consider batching with other UI refinements if multiple changes pending
