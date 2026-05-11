import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
from folium.plugins import Draw, LocateControl
import time
import re

# --- 1. USDA API Logic (Stable Engine) ---
def fetch_nrcs_data(wkt):
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
        # FIX #4: Increased timeout to 60s for large polygons
        response = requests.post(url, data=payload, timeout=60)
        response.raise_for_status()  # FIX #5: Raise on HTTP errors
        data = response.json()
        # FIX #5: Validate response structure
        if not isinstance(data, dict):
            return {"error": "Unexpected API response format"}
        return data
    except requests.exceptions.Timeout:
        return {"error": "USDA API timed out. Please try a smaller area or try again later."}
    except requests.exceptions.HTTPError as e:
        return {"error": f"USDA API returned an error: {e.response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Unable to connect to USDA API. Check your internet connection."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

# FIX #2: Input validation helper
def validate_bounds(lt_min, lt_max, ln_min, ln_max):
    errors = []
    if lt_min >= lt_max:
        errors.append("Lat Min must be less than Lat Max")
    if ln_min >= ln_max:
        errors.append("Lon Min must be less than Lon Max")
    if not (-90 <= lt_min <= 90 and -90 <= lt_max <= 90):
        errors.append("Latitude values must be between -90 and 90")
    if not (-180 <= ln_min <= 180 and -180 <= ln_max <= 180):
        errors.append("Longitude values must be between -180 and 180")
    if (lt_max - lt_min) > 1.0 or (ln_max - ln_min) > 1.0:
        errors.append("Area too large — please select a smaller area (max ~1 degree)")
    return errors

# FIX #6: Stable WKT comparison using rounded coordinates
def normalize_wkt(wkt):
    """Round coordinates to 6 decimal places to prevent duplicate API calls"""
    def round_coord(m):
        return str(round(float(m.group()), 6))
    return re.sub(r'-?\d+\.\d+', round_coord, wkt)

# FIX #10: Rate limiting — track last request time
def can_make_request():
    last = st.session_state.get("last_request_time", 0)
    return (time.time() - last) >= 3  # 3 second cooldown

# --- 2. State Initialization ---
if "map_center" not in st.session_state:
    st.session_state["map_center"] = [41.875, -93.910]
if "analysis_results" not in st.session_state:
    st.session_state["analysis_results"] = None
if "current_bounds" not in st.session_state:
    st.session_state["current_bounds"] = None
if "last_wkt" not in st.session_state:
    st.session_state["last_wkt"] = None
if "last_request_time" not in st.session_state:
    st.session_state["last_request_time"] = 0
if "is_loading" not in st.session_state:
    st.session_state["is_loading"] = False

# --- 3. UI Configuration ---
st.set_page_config(page_title="CRP National Master Tool", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #1e2129; padding: 15px; border-radius: 10px; border: 1px solid #3d414b; }
    [data-testid="stSidebar"] { background-color: #0e1117; }
    .disclaimer { font-size: 10px; color: #888; line-height: 1.2; }
    .indicative-note { font-size: 11px; color: #F59E0B; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ CRP National Eligibility & Precision Tool")

# --- 4. Sidebar Layout ---
with st.sidebar:
    st.header("🌎 National Search")
    LOCATIONS = {
        "Boone, IA (High Erosion)": [41.875, -93.910],
        "Ames, IA (Flat)": [42.053, -93.633],
        "The Palouse, WA (Extreme)": [46.735, -117.175],
        "Driftless Area, WI": [43.500, -91.000],
        "Panhandle, TX": [35.210, -101.830],
        "Mississippi Delta, MS": [33.450, -90.680]
    }
    selected_region = st.selectbox("Choose Region:", list(LOCATIONS.keys()))

    if st.button("Jump to Region"):
        st.session_state["map_center"] = LOCATIONS[selected_region]
        st.session_state["analysis_results"] = None
        st.session_state["current_bounds"] = None
        st.session_state["last_wkt"] = None  # FIX #3: prevent stale shape match
        st.rerun()

    st.divider()
    st.header("🎯 Precision Entry (x,y)")
    col_lat = st.columns(2)
    lt_min = col_lat[0].number_input("Lat Min", value=41.875, format="%.5f")
    lt_max = col_lat[1].number_input("Lat Max", value=41.885, format="%.5f")

    col_lon = st.columns(2)
    ln_min = col_lon[0].number_input("Lon Min", value=-93.915, format="%.5f")
    ln_max = col_lon[1].number_input("Lon Max", value=-93.905, format="%.5f")

    btn_col = st.columns(2)

    # FIX #10: Disable button while loading
    analyze_disabled = st.session_state["is_loading"] or not can_make_request()

    if btn_col[0].button("🚀 Analyze", disabled=analyze_disabled):
        # FIX #2: Validate inputs before calling API
        errors = validate_bounds(lt_min, lt_max, ln_min, ln_max)
        if errors:
            for e in errors:
                st.error(e)
        else:
            p1 = f"{ln_min} {lt_min}"
            p2 = f"{ln_min} {lt_max}"
            p3 = f"{ln_max} {lt_max}"
            p4 = f"{ln_max} {lt_min}"
            wkt = f"POLYGON(({p1}, {p2}, {p3}, {p4}, {p1}))"
            normalized = normalize_wkt(wkt)  # FIX #2: normalize manual entry too

            st.session_state["current_bounds"] = [[lt_min, ln_min], [lt_max, ln_max]]
            st.session_state["map_center"] = [(lt_min + lt_max) / 2, (ln_min + ln_max) / 2]
            st.session_state["last_wkt"] = normalized  # FIX #2: keep state consistent
            st.session_state["is_loading"] = True
            st.session_state["last_request_time"] = time.time()

            # FIX #8: Show spinner during API call
            with st.spinner("Fetching soil data from USDA..."):
                st.session_state["analysis_results"] = fetch_nrcs_data(wkt)

            st.session_state["is_loading"] = False
            st.rerun()

    if btn_col[1].button("🗑️ Clear"):
        st.session_state["analysis_results"] = None
        st.session_state["current_bounds"] = None
        st.session_state["last_wkt"] = None
        st.rerun()

    # --- REQUIRED ATTRIBUTION & DISCLAIMER ---
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<div class="disclaimer">'
        '<b>Legal Disclaimer:</b> This product uses the NRCS Soil Data Access API but is not endorsed '
        'or certified by the USDA. Results are indicative only and must not be used for official '
        'CRP eligibility determinations without verification by a qualified NRCS conservationist.'
        '<br><br>'
        '<b>Erosion Index (EI) Notice:</b> The EI score shown is a simplified indicative calculation, '
        'not an official RUSLE2 or HEL determination. It must not be used as the basis for any '
        'CRP application or land management decision without verification by a qualified NRCS conservationist.'
        '<br><br>'
        '<b>Data Source:</b> Soil Survey Staff. Soil Survey Geographic (SSURGO) Database. '
        'United States Department of Agriculture, Natural Resources Conservation Service.'
        '</div>',
        unsafe_allow_html=True
    )

# --- 5. Main Content: Map & Results ---
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

    # FIX #6: Use normalized WKT for comparison + FIX #10: Rate limiting on drawn polygons
    if map_output.get('all_drawings') and can_make_request():
        last_draw = map_output['all_drawings'][-1]
        coords = last_draw['geometry']['coordinates'][0]
        pts = [f"{p[0]} {p[1]}" for p in coords]
        if pts[0] != pts[-1]:
            pts.append(pts[0])
        drawn_wkt = f"POLYGON(({', '.join(pts)}))"
        normalized = normalize_wkt(drawn_wkt)

        if normalized != st.session_state["last_wkt"]:
            st.session_state["last_wkt"] = normalized
            st.session_state["last_request_time"] = time.time()
            st.session_state["is_loading"] = True

            with st.spinner("Fetching soil data from USDA..."):
                st.session_state["analysis_results"] = fetch_nrcs_data(drawn_wkt)

            st.session_state["is_loading"] = False
            st.rerun()

with col_res:
    st.subheader("Field Analysis")

    if st.session_state["analysis_results"]:
        res = st.session_state["analysis_results"]

        # FIX #5: Handle error responses cleanly
        if "error" in res:
            st.error(f"⚠️ {res['error']}")
            st.info("Try a different area or check your connection.")

        elif "Table" in res and res["Table"]:
            df = pd.DataFrame(res["Table"], columns=["Soil Type", "Slope", "T-Fact", "K-Fact"])
            df[["Slope", "T-Fact", "K-Fact"]] = df[["Slope", "T-Fact", "K-Fact"]].apply(
                pd.to_numeric, errors='coerce'
            )
            df = df.dropna(subset=["Slope", "T-Fact", "K-Fact"])

            if df.empty:
                st.warning("Soil data returned but could not be parsed. Try a different area.")
            else:
                # FIX #3: Label EI as indicative, not official RUSLE2
                df["EI"] = round(
                    (df["K-Fact"] * (df["Slope"] ** 1.2 * 0.1)) / df["T-Fact"] * 10, 2
                )

                max_ei = df["EI"].max()
                st.metric("Erosion Index (EI) — Indicative", max_ei)

                # Placement 1: Directly under EI result — prominent warning box
                st.warning(
                    "⚠️ **EI Disclaimer:** This is a simplified indicative score only — "
                    "not an official RUSLE2 or HEL determination. Do not use for CRP "
                    "applications without verification by a qualified NRCS conservationist."
                )

                if max_ei >= 8.0:
                    st.success("✅ LIKELY ELIGIBLE (HEL — Indicative)")
                    # FIX #9: Label CP recommendations as suggested, not definitive
                    if max_ei > 25:
                        st.warning("💡 **Suggested Practice:** CP22 (Riparian Forest Buffer) — subject to state signup rules")
                    elif max_ei > 15:
                        st.warning("💡 **Suggested Practice:** CP42 (Pollinator Habitat) — subject to state signup rules")
                    else:
                        st.warning("💡 **Suggested Practice:** CP2 (Permanent Native Grasses) — subject to state signup rules")
                else:
                    st.error("❌ LIKELY INELIGIBLE (EI < 8.0 — Indicative)")

                st.divider()
                st.dataframe(df[["Soil Type", "Slope", "EI"]], use_container_width=True)
                st.caption("Data: USDA-NRCS Soil Data Access (SDA) | Results indicative only")

        else:
            st.error("No soil components found. Try drawing a larger area or a different location.")

    else:
        st.info("💡 Draw a polygon on the map or enter coordinates to analyze soil eligibility.")
