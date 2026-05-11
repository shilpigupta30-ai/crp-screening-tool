import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
from folium.plugins import Draw

# --- 1. USDA API Logic ---
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

# --- 2. UI Configuration & Navigation Registry ---
st.set_page_config(page_title="CRP Eligibility Tool", layout="wide")

# Privacy: Hide the "View Source" menu for shared use
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ National CRP Eligibility Tool")

# The Master List of all buttons/options we've created
LOCATIONS = {
    "Ames, IA (Flat)": [42.053, -93.633],
    "Boone, IA (Hotspot)": [41.875, -93.910],
    "The Palouse, WA (Extreme HEL)": [47.000, -117.100],
    "Driftless Area, WI (High HEL)": [43.500, -91.000],
    "Panhandle, TX (Wind Erosion)": [35.210, -101.830],
    "Mississippi Delta, MS (Runoff)": [33.450, -90.680],
    "Western Kansas, KS (Plains)": [38.500, -100.500],
    "Minnesota River, MN (Bluffs)": [44.500, -95.000]
}

if "map_center" not in st.session_state:
    st.session_state["map_center"] = LOCATIONS["Ames, IA (Flat)"]

with st.sidebar:
    st.header("📍 Iowa Quick Access")
    # RESTORED: Your original two buttons
    if st.button("🚜 Flat Farmland (Ames, IA)"):
        st.session_state["map_center"] = LOCATIONS["Ames, IA (Flat)"]
        st.rerun()
    if st.button("🚩 HEL Hotspot (Boone, IA)"):
        st.session_state["map_center"] = LOCATIONS["Boone, IA (Hotspot)"]
        st.rerun()

    st.divider()
    
    # COMBOBOX: All other states/options
    st.header("🌎 National Search")
    other_options = {k: v for k, v in LOCATIONS.items() if "IA" not in k}
    selected_name = st.selectbox("Select a region to analyze:", list(other_options.keys()))
    
    if st.button("Jump to Region"):
        st.session_state["map_center"] = other_options[selected_name]
        st.rerun()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Field Boundary Selection")
    m = folium.Map(location=st.session_state["map_center"], zoom_start=14)
    Draw(export=True).add_to(m)
    # Unique key allows the map to refresh instantly on button click
    map_output = st_folium(m, width=800, height=600, key=f"map_{st.session_state['map_center']}")

# --- 3. Analysis & Practices ---
with col2:
    st.subheader("Analysis Results")
    if map_output.get('all_drawings'):
        last_draw = map_output['all_drawings'][-1]
        raw_coords = last_draw['geometry']['coordinates'][0]
        pts = [f"{float(p[0]):.6f} {float(p[1]):.6f}" for p in raw_coords]
        if pts[0] != pts[-1]: pts.append(pts[0])
        wkt_polygon = f"POLYGON(({', '.join(pts)}))"

        with st.status("Analyzing Soil Data...", expanded=True):
            results = fetch_nrcs_data(wkt_polygon)
            if "Table" in results and results["Table"]:
                rows = []
                for row in results["Table"]:
                    try:
                        k, t, slope = float(row[3]), float(row[2]), float(row[1])
                        # High-Resolution Formula
                        ls = (slope ** 1.2) * 0.1
                        ei = round((k * ls) / t * 10, 2)
                    except: ei = 0.0
                    rows.append({"Soil Type": row[0], "Slope %": row[1], "EI Score": ei, "Status": "Eligible" if ei >= 8.0 else "Ineligible"})
                
                df = pd.DataFrame(rows)
                max_ei = df["EI Score"].max()
                
                st.metric("Max Erosion Index (EI)", f"{max_ei}")
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 Export CSV", df.to_csv().encode('utf-8'), "crp_data.csv", "text/csv")

                st.divider()
                st.subheader("💡 Recommended Practices")
                if max_ei >= 8.0:
                    st.success("**✅ HEL ELIGIBLE**")
                    if max_ei >= 18: st.info("**Practice:** CP22 (Riparian Forest Buffer)")
                    elif max_ei >= 12: st.info("**Practice:** CP42 (Pollinator Habitat)")
                    else: st.info("**Practice:** CP2 (Native Grasses)")
                    st.balloons()
                else:
                    st.warning("**❌ INELIGIBLE**")
                    st.write("Score is below 8.0 threshold.")
            else:
                st.error("No USDA data found here.")
    else:
        st.info("Select a region, then draw a polygon on the map.")