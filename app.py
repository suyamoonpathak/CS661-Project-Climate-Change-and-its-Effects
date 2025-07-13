import streamlit as st
import suyamoon_bird_migration
import imran_climate_trends
import chaitanya
import anirban
import garvit
import kirandeep
import kameshwor
import streamlit.components.v1 as components  # Only needed for iframe embedding

st.set_page_config(layout="wide", page_title="Combined Multi-App Explorer")

st.sidebar.title("Select App")
app_choice = st.sidebar.radio(
    "",
    (
        "Chaitanya's App",
        "Kameshwor's App",
        "Imran's App",
        "Garvit's App",
        "Suyamoon's App",
        "Insha's App",     
        "Kirandeep's App",
        "Anirban's App",
    )
)

# Map app names to their run functions
app_cases = {
    "Imran's App": imran_climate_trends.run,
    "Suyamoon's App": suyamoon_bird_migration.run,
    "Chaitanya's App": chaitanya.run,
    "Anirban's App": anirban.run,
    "Garvit's App": garvit.run,
    "Kirandeep's App": kirandeep.run,
    "Kameshwor's App": kameshwor.run
    # Add more mappings here as needed
}

if app_choice == "Insha's App":
    # Option 1: Open in a new tab (recommended)
    st.markdown(
        """
        <a href="http://localhost:3000/main.html" target="_blank">
            <button style='font-size:20px;padding:10px 24px;'>Open Insha's App</button>
        </a>
        """,
        unsafe_allow_html=True
    )

else:
    app_func = app_cases.get(app_choice)
    if app_func:
        app_func()
    else:
        st.error("Selected app is not available.")
