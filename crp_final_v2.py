# --- 4. Dynamic Recommendation UI ---
if 'df' in locals() and not df.empty:
    st.markdown("---")
    st.subheader("💡 Suggested Conservation Practices")
    
    # Logic to determine the best practice based on the highest EI score found
    max_ei = df["EI Score"].max()
    
    # Define recommendation content
    if max_ei >= 20:
        rec_title = "Priority: Riparian Forest Buffer (CP22)"
        rec_desc = "Extreme erodibility detected. Planting deep-rooted trees and shrubs is the most effective way to stabilize these steep slopes and prevent massive topsoil loss."
        rec_color = "error" # Red
    elif max_ei >= 12:
        rec_title = "Priority: Pollinator Habitat (CP42)"
        rec_desc = "High erodibility risk. We recommend a diverse mix of native wildflowers and grasses. This provides excellent soil cover while maximizing biodiversity incentives."
        rec_color = "warning" # Amber
    elif max_ei >= 8:
        rec_title = "Priority: Permanent Native Grasses (CP2)"
        rec_desc = "Moderate erodibility risk. Establishing permanent native grass cover (like Big Bluestem) will anchor the soil and meet standard CRP eligibility requirements."
        rec_color = "info" # Blue
    else:
        rec_title = "Status: Stable Agricultural Land"
        rec_desc = "This field currently shows low erodibility risk. While it may not qualify for HEL-based CRP, you could consider Filter Strips (CP21) if it borders a waterway."
        rec_color = "success" # Green

    # Display the recommendation in a styled container
    with st.container(border=True):
        st.write(f"### {rec_title}")
        st.write(rec_desc)
        
        # Add a "Technical Justification" expander
        with st.expander("Why this practice?"):
            st.write(f"""
            Based on your analysis, the maximum **Erosion Index (EI)** is **{max_ei}**. 
            Standard USDA guidelines suggest that any score over **8.0** requires permanent 
            vegetative cover to stay within acceptable soil loss tolerances (T-Factor).
            """)