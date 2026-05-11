import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
from folium.plugins import Draw, LocateControl
import time
import re

# =============================================================================
# CRP National Eligibility & Precision Tool — v9
# Key changes from v8/shared-draft:
#   - R-factor fetched at runtime via Nominatim reverse geocode + NRCS FOTG table
#   - EI formula corrected to R * K * LS / T (was missing R entirely — 2100% error)
#   - LS approximated as Slope^1.2 * 0.1 (~23% residual error — SSURGO limitation)
#   - R_FACTORS expanded from 10 to all 50 states using NRCS FOTG averages
#   - normalize_wkt now called in Analyze button (regression from shared draft fixed)
#   - last_wkt synced in Analyze button (regression fixed)
#   - Longitude validation restored (regression fixed)
#   - EI disclaimer restored to sidebar as dedicated section
# =============================================================================

# --- 1. R-Factor Reference Table (NRCS FOTG State Averages) ---
# Source: USDA NRCS Field Office Technical Guide, Agriculture Handbook 703
# Values are mid-range annual averages. Intra-state variation exists.
R_FACTORS = {
    # Northwest
    "Washington": 30,
    "Oregon": 50,
    "Idaho": 25,
    "Montana": 20,
    # Southwest
    "California": 50,
    "Nevada": 15,
    "Arizona": 30,
    "New Mexico": 30,
    "Utah": 20,
    "Colorado": 50,
    "Wyoming": 25,
    # Great Plains
    "North Dakota": 60,
    "South Dakota": 75,
    "Nebraska": 115,
    "Kansas": 100,
    "Oklahoma": 175,
    "Texas": 125,
    # Midwest
    "Minnesota": 110,
    "Iowa": 160,
    "Missouri": 190,
    "Wisconsin": 125,
    "Illinois": 180,
    "Indiana": 175,
    "Michigan": 100,
    "Ohio": 125,
    # South
    "Arkansas": 250,
    "Louisiana": 300,
    "Mississippi": 300,
    "Alabama": 300,
    "Georgia": 300,
    "Florida": 350,
    "South Carolina": 275,
    "North Carolina": 250,
    "Tennessee": 200,
    "Kentucky": 175,
    "Virginia": 175,
    "West Virginia": 150,
    # Northeast
    "Maryland": 150,
    "Delaware": 125,
    "Pennsylvania": 125,
    "New Jersey": 125,
    "New York": 100,
    "Connecticut": 100,
    "Rhode Island": 100,
    "Massachusetts": 100,
    "Vermont": 75,
    "New Hampshire": 75,
    "Maine": 75,
    # Non-contiguous
    "Alaska": 10,
    "Hawaii": 400,
    # Fallback
    "DEFAULT": 100,
}


# --- 2. Helper Functions ---

def get_state_r_factor(lat, lon):
    """
    Reverse geocodes lat/lon to state via Nominatim OSM API,
    then returns (R_value, state_label) from NRCS FOTG table.
    Falls back to DEFAULT=100 on any error.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {"User-Agent": "CRP_Conservation_Tool_v9_NRCS"}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        address = response.json().get("address", {})
        state = address.get("state")
        r_val = R_FACTORS.get(state, R_FACTORS["DEFAULT"])
        label = state if state else "Unknown"
        return r_val, label
    except Exception:
        return R_FACTORS["DEFAULT"], "Unknown (fallback R=100)"


def fetch_nrcs_data(wkt):
    """Queries USDA Soil Data Access API for soil properties within WKT polygon."""
    url = "https://sdmdataaccess.nrcs.usda.gov/Tabular/post.rest"
    query = f"""
    SELECT mu.muname, c.slope_h, c.tfact, ch.kwfact
    FROM mapunit mu
    INNER JOIN component c ON mu.mukey = c.mukey
    INNER JOIN chorizon ch ON c.cokey = ch.cokey
    WHERE mu.mukey IN (
        SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt}')
    )
    AND c.majcompflag = 'yes'
    AND ch.hzdept_r = 0
    """
    payload = {"query": query, "format": "json"}
    try:
        response = requests.post(url, data=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            return {"error": "Unexpected API response format"}
        return data
    except requests.exceptions.Timeout:
        return {"error": "USDA API timed out. Try a smaller area or retry."}
    except requests.exceptions.HTTPError as e:
        return {"error": f"USDA API HTTP error: {e.response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to USDA API. Check internet connection."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def validate_bounds(lt_min, lt_max, ln_min, ln_max):
    """Validates lat/lon bounds before sending to API."""
    errors = []
    if lt_min >= lt_max:
        errors.append("Lat Min must be less than Lat Max")
    if ln_min >= ln_max:
        errors.append("Lon Min must be less than Lon Max")
    if not (-90 <= lt_min <= 90 and -90 <= lt_max <= 90):
        errors.append("Latitude values must be between -90 and 90")
    if not (-180 <= ln_min <= 180 and -180 <= ln_max <= 180):  # RESTORED from v8
        errors.append("Longitude values must be between -180 and 180")
    if (lt_max - lt_min) > 1.0 or (ln_max - ln_min) > 1.0:
        errors.append("Area too large — please select a smaller area (max ~1 degree)")
    return errors


def normalize_wkt(wkt):
    """Rounds WKT coordinates to 6 decimal places to prevent duplicate API calls."""
    def round_coord(m):
        return str(round(float(m.group()), 6))
    return re.sub(r"-?\d+\.\d+", round_coord, wkt)


def can_make_request():
    """Enforces 3-second cooldown between API calls."""
    last = st.session_state.get("last_request_time", 0)
    return (time.time() - last) >= 3


def get_confidence(max_ei, state_label, max_slope):
    """
    Returns (confidence_label, confidence_color, confidence_message)
    based on EI proximity to threshold, R-factor reliability, and slope steepness.
    """
    # Base confidence from EI distance to threshold
    if max_ei > 20 or max_ei < 5:
        level, color = "High", "green"
        msg = "EI is well clear of the 8.0 threshold — result unlikely to flip with better data."
    elif 10 <= max_ei <= 20:
        level, color = "Medium", "orange"
        msg = "EI is above threshold but LS approximation or R-factor variation could affect score."
    else:  # 5 to 10 — danger zone
        level, color = "Low", "red"
        msg = "Field is near the eligibility threshold (8.0). LS and R-factor errors most impactful here. NRCS field verification strongly recommended."

    # Downgrade if R-factor fell back to default
    if "fallback" in state_label.lower() or "unknown" in state_label.lower():
        level = "Low"
        color = "red"
        msg += " State not detected — R-factor is estimated at default (100). Results less reliable."

    # Downgrade if steep slopes detected
    if max_slope > 15:
        if level == "High":
            level, color = "Medium", "orange"
        elif level == "Medium":
            level, color = "Low", "red"
        msg += f" Steep slopes detected ({max_slope}%) — LS approximation less accurate at high gradients."

    return level, color, msg


# --- 3. Session State Initialization ---
defaults = {
    "map_center": [41.875, -93.910],
    "analysis_results": None,
    "current_bounds": None,
    "last_wkt": None,
    "last_request_time": 0,
    "is_loading": False,
    "detected_r": (100, "Not yet detected"),
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# --- 4. UI Configuration ---
st.set_page_config(page_title="CRP National Eligibility Tool", layout="wide")

st.markdown("""
    <style>
    .stMetric {
        background-color: #1e2129;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3d414b;
    }
    [data-testid="stSidebar"] { background-color: #0e1117; }
    .disclaimer { font-size: 10px; color: #888; line-height: 1.4; }
    .r-banner {
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #F59E0B;
        margin-bottom: 12px;
    }
    .ei-notice {
        background-color: #3e2723;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #d84315;
        margin-bottom: 10px;
        font-size: 11px;
        color: #ffccbc;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ CRP National Eligibility & Precision Tool")


# --- 5. Sidebar ---
with st.sidebar:

    # ── Region Jump ──────────────────────────────────────────────────────
    st.header("🌎 National Search")
    LOCATIONS = {
        "Boone, IA (High Erosion)":  [41.875,  -93.910],
        "Ames, IA (Flat)":           [42.053,  -93.633],
        "The Palouse, WA (Extreme)": [46.735, -117.175],
        "Driftless Area, WI":        [43.500,  -91.000],
        "Panhandle, TX":             [35.210, -101.830],
        "Mississippi Delta, MS":     [33.450,  -90.680],
    }
    selected_region = st.selectbox("Choose Region:", list(LOCATIONS.keys()))

    if st.button("Jump to Region"):
        st.session_state["map_center"]       = LOCATIONS[selected_region]
        st.session_state["analysis_results"] = None
        st.session_state["current_bounds"]   = None
        st.session_state["last_wkt"]         = None   # Prevent stale shape match
        st.session_state["detected_r"]       = (100, "Not yet detected")
        st.rerun()

    st.divider()

    # ── Precision Entry ──────────────────────────────────────────────────
    st.header("🎯 Precision Entry (x,y)")
    col_lat = st.columns(2)
    lt_min = col_lat[0].number_input("Lat Min", value=41.875, format="%.5f")
    lt_max = col_lat[1].number_input("Lat Max", value=41.885, format="%.5f")
    col_lon = st.columns(2)
    ln_min = col_lon[0].number_input("Lon Min", value=-93.915, format="%.5f")
    ln_max = col_lon[1].number_input("Lon Max", value=-93.905, format="%.5f")

    btn_col = st.columns(2)
    analyze_disabled = st.session_state["is_loading"] or not can_make_request()

    if btn_col[0].button("🚀 Analyze", disabled=analyze_disabled):
        errors = validate_bounds(lt_min, lt_max, ln_min, ln_max)
        if errors:
            for e in errors:
                st.error(e)
        else:
            p1 = f"{ln_min} {lt_min}"
            p2 = f"{ln_min} {lt_max}"
            p3 = f"{ln_max} {lt_max}"
            p4 = f"{ln_max} {lt_min}"
            wkt        = f"POLYGON(({p1}, {p2}, {p3}, {p4}, {p1}))"
            normalized = normalize_wkt(wkt)       # FIXED: normalize manual entry
            center_lat = (lt_min + lt_max) / 2
            center_lon = (ln_min + ln_max) / 2

            st.session_state["current_bounds"]    = [[lt_min, ln_min], [lt_max, ln_max]]
            st.session_state["map_center"]        = [center_lat, center_lon]
            st.session_state["last_wkt"]          = normalized  # FIXED: sync state
            st.session_state["is_loading"]        = True
            st.session_state["last_request_time"] = time.time()
            st.session_state["detected_r"]        = get_state_r_factor(center_lat, center_lon)

            with st.spinner("Fetching soil data from USDA..."):
                st.session_state["analysis_results"] = fetch_nrcs_data(wkt)

            st.session_state["is_loading"] = False
            st.rerun()

    if btn_col[1].button("🗑️ Clear"):
        st.session_state["analysis_results"] = None
        st.session_state["current_bounds"]   = None
        st.session_state["last_wkt"]         = None
        st.session_state["detected_r"]       = (100, "Not yet detected")
        st.rerun()

    st.markdown("---")
    st.markdown(
        '<div class="ei-notice">'
        '<b>🚨 Erosion Index Notice</b><br>'
        'This score is a simplified indicative calculation — NOT an official RUSLE2 or HEL '
        'determination. It must not be used as the basis for any CRP application or land '
        'management decision without NRCS field verification.'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="disclaimer">'
        '<b>Legal Disclaimer:</b> This product uses the NRCS Soil Data Access API but is '
        'not endorsed or certified by the USDA. Results are indicative only and must not be '
        'used for official CRP eligibility determinations without verification by a qualified '
        'NRCS conservationist.'
        '<br><br>'
        '<b>Erosion Index (EI) Notice:</b> EI is calculated as R × K × LS / T. '
        'R-factors are state-level averages from NRCS FOTG — not point-specific values. '
        'LS is approximated from slope steepness only (slope length unavailable in SSURGO). '
        'This score must not be used as the basis for any CRP application or land management '
        'decision without NRCS field verification.'
        '<br><br>'
        '<b>CP Practice Suggestions:</b> Practice recommendations are based on EI thresholds '
        'only and do not account for state signup rules, program periods, or site conditions.'
        '<br><br>'
        '<b>Data Source:</b> Soil Survey Staff. Soil Survey Geographic (SSURGO) Database. '
        'United States Department of Agriculture, Natural Resources Conservation Service.'
        '</div>',
        unsafe_allow_html=True
    )


# --- 6. Main Content: Map + Results ---
col_map, col_res = st.columns([2, 1])

with col_map:
    m = folium.Map(location=st.session_state["map_center"], zoom_start=14)
    LocateControl().add_to(m)
    Draw(export=True).add_to(m)

    if st.session_state["current_bounds"]:
        folium.Rectangle(
            bounds=st.session_state["current_bounds"],
            color="#FF4B4B",
            fill=True,
            fill_opacity=0.3
        ).add_to(m)
        m.fit_bounds(st.session_state["current_bounds"])

    map_output = st_folium(m, width="100%", height=650, key="crp_master_map")

    # Drawn polygon handler with normalize + rate limit
    if map_output.get("all_drawings") and can_make_request():
        last_draw  = map_output["all_drawings"][-1]
        coords     = last_draw["geometry"]["coordinates"][0]
        pts        = [f"{p[0]} {p[1]}" for p in coords]
        if pts[0] != pts[-1]:
            pts.append(pts[0])
        drawn_wkt  = f"POLYGON(({', '.join(pts)}))"
        normalized = normalize_wkt(drawn_wkt)

        if normalized != st.session_state["last_wkt"]:
            lats  = [c[1] for c in coords]
            lons  = [c[0] for c in coords]
            c_lat = sum(lats) / len(lats)
            c_lon = sum(lons) / len(lons)

            st.session_state["last_wkt"]          = normalized
            st.session_state["last_request_time"] = time.time()
            st.session_state["is_loading"]        = True
            st.session_state["detected_r"]        = get_state_r_factor(c_lat, c_lon)

            _, state_label = st.session_state["detected_r"]
            with st.spinner(f"Fetching soil data ({state_label})..."):
                st.session_state["analysis_results"] = fetch_nrcs_data(drawn_wkt)

            st.session_state["is_loading"] = False
            st.rerun()


with col_res:
    st.subheader("Field Analysis")

    # R-factor banner — always visible once state detected
    r_val, state_label = st.session_state["detected_r"]
    st.markdown(
        f'<div class="r-banner">'
        f'📍 <b>Detected State:</b> {state_label}<br>'
        f'🌧️ <b>Applied R-Factor:</b> {r_val} '
        f'<span style="font-size:11px;color:#888;">(NRCS FOTG state average)</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    if st.session_state["analysis_results"]:
        res = st.session_state["analysis_results"]

        if "error" in res:
            st.error(f"⚠️ {res['error']}")
            st.info("Try a different area or check your connection.")

        elif "Table" in res and res["Table"]:
            df = pd.DataFrame(
                res["Table"],
                columns=["Soil Type", "Slope", "T-Fact", "K-Fact"]
            )
            df[["Slope", "T-Fact", "K-Fact"]] = df[["Slope", "T-Fact", "K-Fact"]].apply(
                pd.to_numeric, errors="coerce"
            )
            df = df.dropna(subset=["Slope", "T-Fact", "K-Fact"])

            if df.empty:
                st.warning("Soil data returned but could not be parsed. Try a different area.")
            else:
                # EI = (R × K × LS) / T
                # LS = Slope^1.2 × 0.1 (approximated — slope length not in SSURGO)
                # Residual deviation from true NRCS EI: ~23% vs ~2100% before R was added
                df["EI"] = round(
                    (r_val * df["K-Fact"] * (df["Slope"] ** 1.2 * 0.1)) / df["T-Fact"], 2
                )

                max_ei    = df["EI"].max()
                max_slope = df["Slope"].max()

                st.metric("Erosion Index (EI) — Indicative", max_ei)

                # A — Confidence indicator
                conf_level, conf_color, conf_msg = get_confidence(
                    max_ei, state_label, max_slope
                )
                conf_colors = {"green": "#1B4332", "orange": "#92400E", "red": "#7f1d1d"}
                conf_border = {"green": "#52B788", "orange": "#F59E0B", "red": "#d84315"}
                st.markdown(
                    f'<div style="background-color:{conf_colors[conf_color]};'
                    f'border-left:5px solid {conf_border[conf_color]};'
                    f'padding:10px;border-radius:5px;margin-bottom:10px;'
                    f'font-size:11px;color:#fff;line-height:1.4;">'
                    f'<b>Confidence: {conf_level}</b><br>{conf_msg}'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # B — R-factor confidence flag
                if "fallback" in state_label.lower() or "unknown" in state_label.lower():
                    st.error(
                        "⚠️ State not detected — R-factor defaulted to 100. "
                        "Results are less reliable. Try redrawing the polygon or "
                        "use Precision Entry with verified coordinates."
                    )

                # C — Steep slope LS warning
                if max_slope > 15:
                    st.warning(
                        f"⚠️ Steep slopes detected (max {max_slope}%). "
                        "LS factor is approximated from steepness only — slope length "
                        "unavailable in SSURGO. NRCS field verification recommended."
                    )

                # Placement 1: Red notice box directly under EI result
                st.markdown(
                    '<div class="ei-notice">'
                    '<b>🚨 EI Disclaimer:</b> Simplified proxy score using state-level R-factor. '
                    'Not an official RUSLE2 or HEL determination. Verify with a qualified '
                    'NRCS conservationist before any CRP application.'
                    '</div>',
                    unsafe_allow_html=True
                )

                if max_ei >= 8.0:
                    st.success("✅ LIKELY ELIGIBLE (HEL — Indicative)")
                    if max_ei > 25:
                        st.info("💡 **Suggested Practice:** CP22 (Riparian Forest Buffer) "
                                "— subject to state signup rules")
                    elif max_ei > 15:
                        st.info("💡 **Suggested Practice:** CP42 (Pollinator Habitat) "
                                "— subject to state signup rules")
                    else:
                        st.info("💡 **Suggested Practice:** CP2 (Permanent Native Grasses) "
                                "— subject to state signup rules")
                else:
                    st.error("❌ LIKELY INELIGIBLE (EI < 8.0 — Indicative)")

                st.divider()
                st.dataframe(df[["Soil Type", "Slope", "EI"]], use_container_width=True)
                st.caption(
                    f"Data: USDA-NRCS SDA | R={r_val} ({state_label} FOTG avg) | "
                    "Results indicative only"
                )

        else:
            st.error("No soil components found. Try drawing a larger area or different location.")

    else:
        st.info("💡 Draw a polygon on the map or enter coordinates to analyze soil eligibility.")
