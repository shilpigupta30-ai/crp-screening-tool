import streamlit as st
import requests
import pandas as pd

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

# --- 2. Initialize "Sticky Note" (Session State) ---
if "analysis_results" not in st.session_state:
    st.session_state["analysis_results"] = None

st.title("🛡️ CRP Precision Tool - Steady Mode")

# Sidebar
with st.sidebar:
    st.header("Coordinates")
    lt_min = st.number_input("Lat Min", value=41.87500, format="%.5f")
    lt_max = st.number_input("Lat Max", value=41.88500, format="%.5f")
    ln_min = st.number_input("Lon Min", value=-93.91500, format="%.5f")
    ln_max = st.number_input("Lon Max", value=-93.90500, format="%.5f")
    
    if st.button("🚀 Run Analysis"):
        # Build the closed-loop polygon
        p1 = f"{ln_min} {lt_min}"
        p2 = f"{ln_min} {lt_max}"
        p3 = f"{ln_max} {lt_max}"
        p4 = f"{ln_max} {lt_min}"
        wkt_string = f"POLYGON(({p1}, {p2}, {p3}, {p4}, {p1}))"
        
        # Save results to the "Sticky Note"
        st.session_state["analysis_results"] = fetch_nrcs_data(wkt_string)

# --- 3. Display Results from Session State ---
if st.session_state["analysis_results"]:
    data = st.session_state["analysis_results"]
    
    if "Table" in data and data["Table"]:
        st.success("✅ Results Loaded and Locked")
        df = pd.DataFrame(data["Table"], columns=["Soil Name", "Slope", "T-Fact", "K-Fact"])
        
        # Simple math to prove it works
        df["EI Score"] = df.apply(lambda x: round((float(x[3]) * (float(x[1])**1.2 * 0.1)) / float(x[2]) * 10, 2), axis=1)
        
        st.dataframe(df, use_container_width=True)
        st.metric("Max EI", df["EI Score"].max())
    else:
        st.error("No data found or API error.")
        st.write(data)