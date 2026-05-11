import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
from folium.plugins import Draw

# --- 1. USDA API Logic (Horizon Join Version) ---
def fetch_nrcs_data(wkt):
    url = "https://sdmdataaccess.nrcs.usda.gov/Tabular/post.rest"
    query = f"""
    SELECT mu.muname, c.slope_r, c.tfact, ch.kwfact
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
        return response.json() if response.status_code == 200 else {"error": response.status_code}
    except Exception as e:
        return {"error": str(e)}

# --- 2. UI Configuration & Navigation ---
st.set_page_config(page_title="NRCS Eligibility Prototype", layout="wide")
st.title("CRP Automation Prototype")

IOWA_FARM = [42.053, -93.633] 
HEL_HOTSPOT = [41.875, -93.910] 

if "map_center" not in st.session_state:
    st.session_state["map_center"] = IOWA_FARM

with st.sidebar:
    st.header("Navigation Tools")
    if st.button("📍 Find HEL Hotspots"):
        st.session_state["map_center"] = HEL_HOTSPOT
    if st.button("🚜 Go to Flat Farmland"):
        st.session_state["map_center"] = IOWA_FARM
    if st.button("🔄 Reset Map"):
        st.session_state["map_center"] = IOWA_FARM
        st.rerun()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Field Boundary Selection")
    m = folium.Map(location=st.session_state["map_center"], zoom_start=14)
    Draw(export=True).add_to(m)
    map_output = st_folium(m, width=800, height=550, key=f"map_{st.session_state['map_center']}")

# --- 3. Analysis & Results Logic ---
with col2:
    st.subheader("Analysis Results")
    
    if map_output.get('all_drawings'):
        last_draw = map_output['all_drawings'][-1]
        raw_coords = last_draw['geometry']['coordinates'][0]
        pts = [f"{float(p[0]):.6f} {float(p[1]):.6f}" for p in raw_coords]
        if pts[0] != pts[-1]: pts.append(pts[0])
        wkt_polygon = f"POLYGON(({', '.join(pts)}))"

        with st.status("Analyzing Soil Data...", expanded=True) as status:
            results = fetch_nrcs_data(wkt_polygon)
            
            if "Table" in results and results["Table"]:
                rows = []
                for row in results["Table"]:
                    try:
                        k_val = float(row[3]) if row[3] else 0.0
                        t_val = float(row[2]) if row[2] else 1.0
                        slope = float(row[1]) if row[1] else 0.0
                        
                        # Standard EI Calculation: (R * K * LS) / T
                        # Using 1.0 for R and 0.28 for LS as standard prototype constants
                        ei_score = round((1.0 * k_val * 0.28) / t_val, 4)
                    except:
                        ei_score = 0.0
                    
                    rows.append({
                        "Soil Type": row[0],
                        "EI Score": ei_score,
                        "HEL Status": "Eligible" if ei_score >= 8.0 else "Ineligible"
                    })
                
                df = pd.DataFrame(rows)
                max_ei = df["EI Score"].max()
                
                # Display the raw scientific output
                st.metric("Maximum Erosion Index (EI)", f"{max_ei}")
                
                st.dataframe(df, use_container_width=True)
                
                # --- Dynamic Recommendations based on raw EI ---
                st.markdown("---")
                st.subheader("💡 Suggested CRP Practices")
                
                if max_ei >= 8.0:
                    st.success("**Field Eligible for CRP**")
                    if max_ei >= 15.0:
                        st.info("**Recommended:** Riparian Forest Buffer (CP22) for extreme slopes.")
                    else:
                        st.info("**Recommended:** Native Grasses (CP2) for standard erodibility.")
                    st.balloons()
                else:
                    st.warning("**Field Ineligible for HEL-based CRP**")
                    st.write("Current EI score is below the 8.0 threshold required for erodibility-based contracts.")
            else:
                status.update(label="No Data Found", state="error")
    else:
        st.write("Draw a boundary on the map to begin.")