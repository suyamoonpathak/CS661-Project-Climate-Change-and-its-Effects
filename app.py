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
        "Chaitanya's Task",
        "Kameshwor's Task",
        "Imran's Task",
        "Vijiyant and Garvit's Task",
        "Suyamoon's Task",
        "Insha's Task",     
        "Kirandeep's Task",
        "Anirban's Task",
    )
)

# Map app names to their run functions
app_cases = {
    "Imran's Task": imran_climate_trends.run,
    "Suyamoon's Task": suyamoon_bird_migration.run,
    "Chaitanya's Task": chaitanya.run,
    "Anirban's Task": anirban.run,
    "Vijiyant and Garvit's Task": garvit.run,
    "Kirandeep's Task": kirandeep.run,
    "Kameshwor's Task": kameshwor.run
    # Add more mappings here as needed
}

if app_choice == "Insha's Task":
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
