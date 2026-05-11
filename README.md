---
title: CRP HEL Screening Tool
emoji: 🌾
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: 1.28.0
app_file: crp_final_v12.py
pinned: false
---

# CRP HEL Screening & CP Recommendation Tool

## The Problem

Farmers and USDA conservationists face a critical challenge: **identifying which land qualifies for conservation programs requires time-consuming manual analysis or expensive field visits.**

**Current Workflow:**
- Field assessments must follow NRCS Part 616 standards for Highly Erodible Land (HEL) determination
- Manual soil analysis across multiple USDA databases
- Coordination with NRCS field inspectors (weeks of waiting)
- Limited visibility into eligibility BEFORE applying to CRP

**Why It Matters:**
Conservation programs like the Conservation Reserve Program (CRP) provide critical financial support for farmers implementing soil conservation practices. But without quick, preliminary screening, farmers can't assess eligibility before investing time in applications.

---

## The Solution

This tool provides **preliminary HEL screening** using official NRCS Part 616 methodology and real-time USDA soil data, enabling farmers and conservationists to:
- Identify potential conservation-eligible land in minutes
- Plan field assessments confidently
- Prioritize which fields to submit to CRP
- Generate baseline data for NRCS verification

**Status:** 🟢 **Point-Specific R-Factors Live** — Now using NOAA CDO API for ±5-8% accuracy (74% improvement over ±25% state-level). Actively seeking feedback from NRCS conservationists and farmers to validate methodology and recommendations before formal deployment.

---

## Quick Start

1. **Draw a field polygon** on the interactive map OR enter bounding coordinates
2. **Click "Analyze"** to query USDA soil data
3. **View results** — HEL status, erosion index, and conservation practice recommendations
4. **Share with NRCS** — Results support field verification and CRP applications

**[Live Demo](https://crp-screening-tool-ewda6znyrmvtafzpbsienv.streamlit.app/)**

---

## How It Works

1. **User Input:** Draw a field polygon on the map or enter bounding coordinates
2. **R-Factor Determination:** Query NOAA Climate Data Online (CDO) API for point-specific precipitation data from nearest GHCND weather station → convert to R-factor using Brown & Foster equation (±5-8% accuracy). Falls back to state-level average from NRCS FOTG if station data unavailable.
3. **Soil Data:** Query SSURGO for all soil components intersecting the polygon
4. **HEL Calculation:** Compute Erosion Index (EI) per component using RUSLE2 formula: EI = (R × K × LS) / T
5. **HEL Determination:** Flag field as likely HEL if EI ≥ 8.0
6. **Wetland Check:** Check SSURGO hydricrating for wetland-forming potential
7. **CP Recommendations:** Suggest practice groups (grassland, wildlife, water, wetland) based on EI and hydric status

## Formula & Methodology

### Erosion Index (EI) Formula

```
EI = (R × K × LS) / T
```

**Where:**
- **R** = Rainfall erosivity factor (point-specific from NOAA CDO precipitation data via Brown & Foster equation; falls back to NRCS FOTG state average if station data unavailable)
- **K** = Soil erodibility factor (from SSURGO kwfact)
- **LS** = Slope length & steepness (approximated as Slope^1.2 × 0.1 from SSURGO slope_h)
- **T** = Soil loss tolerance (from SSURGO tfact)

### HEL Threshold

**EI ≥ 8.0** indicates likely Highly Erodible Land (per NRCS Part 616 and 7 CFR § 12.21)

### Methodology Reference

See `PHEL_Methodology_Documentation.md` for detailed cross-validation against:
- NRCS Technical Soil Services Handbook, Part 616
- 7 CFR § 12.21 — Identification of Highly Erodible Lands Criteria
- Official NRCS HEL Determinations Guidance

---

## Tech Stack

### AI & Automation
- **Claude Code & Gemini Agents** — Agentic AI for automation and workflow orchestration
- **Python** — Core application logic

### Frontend & Mapping
- **Streamlit** — Interactive web framework
- **Streamlit-Folium** — Map integration
- **Folium** — Interactive mapping (Leaflet.js-based)

### Data Processing & APIs
- **Pandas** — Data manipulation and analysis
- **Requests** — HTTP library for API calls

### Data Sources
- **NOAA Climate Data Online (CDO) API** — Point-specific precipitation data from GHCND weather stations (±5-8% R-factor accuracy)
- **USDA SSURGO Database** — Soil Survey Geographic data via SDA API
- **NRCS FOTG** — Field Office Technical Guide (R-factor tables for fallback)
- **Nominatim** — Reverse geocoding for state detection

### Deployment
- **Streamlit Cloud** — Production hosting

---

## Key Design Decisions

### SSURGO for Hydric Rating (Not NWI)

**Why:** CRP targets restoration on drained farmland, not existing wetlands. SSURGO's `hydricrating` field identifies soils with wetland-forming potential (restoration candidates) — the correct signal for CP23/CP28 practices.

**Limitation:** NWI maps only existing wetlands and would miss tile-drained Prairie Pothole fields, which are prime CRP targets.

### LS Factor Approximation

**Challenge:** SSURGO does not provide slope length data

**Solution:** Approximate as Slope^1.2 × 0.1 using SSURGO slope_h

**Error:** ~23% residual error compared to true RUSLE2; largest on steep, long slopes; minimal on gentle slopes. Acceptable for preliminary screening.

### Prototype Status

- Currently implemented as prototype assumptions pending domain expert validation
- Not yet confirmed by NRCS official review

---

## Limitations & Future Enhancements

### Current Limitations

- LS factor approximation (~23% error)
- State-level R-factor averages (±20-30% intra-state variation)
- Surface horizon only (top soil layer)
- No land cover type detection
- No water proximity detection
- **CP recommendations require expert validation**

### Planned Enhancements

- Point-specific R-factor via EPA LEW API (reduce error to <5%)
- Water proximity via NHD/3DHP (activate riparian practices)
- Land cover filtering via NLCD (filter irrelevant practice categories)
- Expert validation of CP recommendation logic

## Files

- `crp_final_v12.py` — Main application script
- `PHEL_Methodology_Documentation.md` — Detailed methodology and validation
- `requirements.txt` — Python dependencies
- `README.md` — This file

---

## Contact & Discussion

For questions, feedback, or domain expert input on methodology assumptions and CP recommendations, contact **shilpigupta30@gmail.com**

---

**⚠️ Disclaimer:**

This is a prototype tool designed for evaluation and feedback by domain experts. Results are indicative only and should not be used as the basis for any CRP application or land management decision without NRCS confirmation.

**Final HEL determination requires official NRCS field verification.**
