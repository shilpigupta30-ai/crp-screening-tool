import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
from folium.plugins import Draw, LocateControl

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
        # Timeout set to 30s per USDA policy
        response = requests.post(url, data=payload, timeout=30)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# --- 2. State Initialization ---
if "map_center" not in st.session_state:
    st.session_state["map_center"] = [41.875, -93.910] 
if "analysis_results" not in st.session_state:
    st.session_state["analysis_results"] = None
if "current_bounds" not in st.session_state:
    st.session_state["current_bounds"] = None
if "last_wkt" not in st.session_state:
    st.session_state["last_wkt"] = None

# --- 3. UI Configuration ---
st.set_page_config(page_title="CRP National Master Tool", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #1e2129; padding: 15px; border-radius: 10px; border: 1px solid #3d414b; }
    [data-testid="stSidebar"] { background-color: #0e1117; }
    .disclaimer { font-size: 10px; color: #888; line-height: 1.2; }
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
    if btn_col[0].button("🚀 Analyze"):
        p1 = f"{ln_min} {lt_min}"
        p2 = f"{ln_min} {lt_max}"
        p3 = f"{ln_max} {lt_max}"
        p4 = f"{ln_max} {lt_min}"
        wkt = f"POLYGON(({p1}, {p2}, {p3}, {p4}, {p1}))"
        
        st.session_state["current_bounds"] = [[lt_min, ln_min], [lt_max, ln_max]]
        st.session_state["analysis_results"] = fetch_nrcs_data(wkt)
        st.session_state["map_center"] = [(lt_min + lt_max)/2, (ln_min + ln_max)/2]
        st.rerun()

    if btn_col[1].button("🗑️ Clear"):
        st.session_state["analysis_results"] = None
        st.session_state["current_bounds"] = None
        st.rerun()

    # --- REQUIRED ATTRIBUTION & DISCLAIMER ---
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<div class="disclaimer">'
        '<b>Legal Disclaimer:</b> This product uses the NRCS Soil Data Access API but is not endorsed or certified by the USDA. '
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

    if map_output.get('all_drawings'):
        last_draw = map_output['all_drawings'][-1]
        coords = last_draw['geometry']['coordinates'][0]
        pts = [f"{p[0]} {p[1]}" for p in coords]
        if pts[0] != pts[-1]: pts.append(pts[0])
        drawn_wkt = f"POLYGON(({', '.join(pts)}))"
        
        if drawn_wkt != st.session_state["last_wkt"]:
            st.session_state["last_wkt"] = drawn_wkt
            st.session_state["analysis_results"] = fetch_nrcs_data(drawn_wkt)
            st.rerun()

with col_res:
    st.subheader("Field Analysis")
    if st.session_state["analysis_results"]:
        res = st.session_state["analysis_results"]
        if "Table" in res and res["Table"]:
            df = pd.DataFrame(res["Table"], columns=["Soil Type", "Slope", "T-Fact", "K-Fact"])
            df[["Slope", "T-Fact", "K-Fact"]] = df[["Slope", "T-Fact", "K-Fact"]].apply(pd.to_numeric)
            df["EI"] = round((df["K-Fact"] * (df["Slope"]**1.2 * 0.1)) / df["T-Fact"] * 10, 2)
            
            max_ei = df["EI"].max()
            st.metric("Max Erosion Index (EI)", max_ei)
            
            if max_ei >= 8.0:
                st.success("✅ FIELD ELIGIBLE (HEL)")
                if max_ei > 25:
                    st.warning("🎯 **Recommended:** CP22 (Riparian Forest Buffer)")
                elif max_ei > 15:
                    st.warning("🎯 **Recommended:** CP42 (Pollinator Habitat)")
                else:
                    st.warning("🎯 **Recommended:** CP2 (Permanent Native Grasses)")
            else:
                st.error("❌ INELIGIBLE (EI < 8.0)")
            
            st.divider()
            st.dataframe(df[["Soil Type", "Slope", "EI"]], use_container_width=True)
            
            # Additional attribution for data integrity
            st.caption("Data generated via USDA-NRCS Soil Data Access (SDA)")
        else:
            st.error("No soil components found. Try a different area.")
    else:
        st.info("💡 Draw a polygon on the map or enter coordinates to analyze soil eligibility.")