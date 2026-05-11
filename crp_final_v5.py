import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
from folium.plugins import Draw, LocateControl

# --- 1. USDA API Logic ---
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
        response = requests.post(url, data=payload, timeout=30)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# --- 2. Configuration & State ---
st.set_page_config(page_title="CRP National Master", layout="wide")

LOCATIONS = {
    "Ames, IA (Flat)": [42.053, -93.633],
    "Boone, IA (Hotspot)": [41.875, -93.910],
    "The Palouse, WA": [47.000, -117.100],
    "Driftless Area, WI": [43.500, -91.000],
    "Panhandle, TX": [35.210, -101.830],
    "Mississippi Delta, MS": [33.450, -90.680],
    "Western Kansas, KS": [38.500, -100.500],
    "Minnesota River, MN": [44.500, -95.000],
    "Sandhills, NE": [42.000, -101.000]
}

if "map_center" not in st.session_state:
    st.session_state["map_center"] = LOCATIONS["Boone, IA (Hotspot)"]
if "analysis_results" not in st.session_state:
    st.session_state["analysis_results"] = None
if "manual_wkt" not in st.session_state:
    st.session_state["manual_wkt"] = None

st.title("🛡️ CRP National Eligibility & Precision Tool")

# --- 3. Sidebar (Dropdown & Manual Entry) ---
with st.sidebar:
    st.header("🌎 National Search")
    selected_region = st.selectbox("Choose Region:", list(LOCATIONS.keys()))
    if st.button("Jump to Region"):
        st.session_state["map_center"] = LOCATIONS[selected_region]
        st.session_state["analysis_results"] = None
        st.session_state["manual_wkt"] = None
        st.rerun()

    st.divider()
    st.header("🎯 Precision Entry")
    lt_min = st.number_input("Lat Min", value=41.875, format="%.5f")
    lt_max = st.number_input("Lat Max", value=41.885, format="%.5f")
    ln_min = st.number_input("Lon Min", value=-93.915, format="%.5f")
    ln_max = st.number_input("Lon Max", value=-93.905, format="%.5f")
    
    col1, col2 = st.columns(2)
    if col1.button("🚀 Analyze"):
        # Build closed-loop WKT
        p1, p2, p3, p4 = f"{ln_min} {lt_min}", f"{ln_min} {lt_max}", f"{ln_max} {lt_max}", f"{ln_max} {lt_min}"
        wkt = f"POLYGON(({p1}, {p2}, {p3}, {p4}, {p1}))"
        st.session_state["manual_wkt"] = wkt
        st.session_state["analysis_results"] = fetch_nrcs_data(wkt)
        st.rerun()

    if col2.button("🗑️ Clear"):
        st.session_state["analysis_results"] = None
        st.session_state["manual_wkt"] = None
        st.rerun()

# --- 4. Main Layout ---
c_map, c_res = st.columns([2, 1])

with c_map:
    m = folium.Map(location=st.session_state["map_center"], zoom_start=14)
    LocateControl().add_to(m)
    Draw(export=True).add_to(m)
    
    # Show manual box if it exists
    if st.session_state["manual_wkt"]:
        folium.Rectangle(bounds=[[lt_min, ln_min], [lt_max, ln_max]], color="blue").add_to(m)

    # MAP INTERACTION LOGIC
    map_output = st_folium(m, width="100%", height=600, key="master_map")

    # If user draws on map, trigger analysis automatically
    if map_output.get('all_drawings'):
        last_draw = map_output['all_drawings'][-1]
        raw_coords = last_draw['geometry']['coordinates'][0]
        pts = [f"{p[0]} {p[1]}" for p in raw_coords]
        if pts[0] != pts[-1]: pts.append(pts[0])
        drawn_wkt = f"POLYGON(({', '.join(pts)}))"
        
        # Only rerun if it's a new drawing
        if drawn_wkt != st.session_state.get("last_drawn_wkt"):
            st.session_state["last_drawn_wkt"] = drawn_wkt
            st.session_state["analysis_results"] = fetch_nrcs_data(drawn_wkt)
            st.rerun()

with c_res:
    st.subheader("Analysis Results")
    if st.session_state["analysis_results"]:
        data = st.session_state["analysis_results"]
        if "Table" in data and data["Table"]:
            df = pd.DataFrame(data["Table"], columns=["Soil Type", "Slope", "T-Fact", "K-Fact"])
            
            # Practice Logic & EI Calculation
            df["EI"] = df.apply(lambda x: round((float(x[3]) * (float(x[1])**1.2 * 0.1)) / float(x[2]) * 10, 2), axis=1)
            max_ei = df["EI"].max()
            
            st.metric("Max Erosion Index", max_ei)
            
            if max_ei >= 8.0:
                st.success("**✅ ELIGIBLE (HEL)**")
                # PRACTICE SUGGESTIONS
                if max_ei > 20:
                    st.info("**Practice Suggestion:** CP22 (Riparian Forest Buffer)")
                elif max_ei > 12:
                    st.info("**Practice Suggestion:** CP42 (Pollinator Habitat)")
                else:
                    st.info("**Practice Suggestion:** CP2 (Native Grasses)")
            else:
                st.warning("**❌ INELIGIBLE**")
                
            st.dataframe(df[["Soil Type", "Slope", "EI"]], use_container_width=True)
        else:
            st.error("No data found for this selection.")
    else:
        st.info("Draw a shape or use 'Analyze' to begin.")