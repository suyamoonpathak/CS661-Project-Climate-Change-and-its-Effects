import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp

def run():
    # Streamlit page configuration
    st.set_page_config(layout="wide", page_title="Climate Trends")


    # Load Dataset 
    dataset_path = "imran_df_filled.csv"
    df = pd.read_csv(dataset_path)
    df = df.dropna(subset=["Country", "Year"])
    df["Year"] = pd.to_numeric(df["Year"], errors='coerce')  # Convert Year to numeric; if invalid, set as NaN (missing)
    df = df[df["Year"].between(2000, 2023)]


    # Streamlit tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Animated CO₂ Emissions Map",
        "Country-wise CO₂ Trend",
        "Forest Area vs Climate",
        "Global Avg Temperature"
    ])


    # Tab-1: Animated CO₂ Map

    with tab1:
        st.title("Global CO₂ Emissions Per Capita (2000–2023)")
        st.markdown("An animated globe showing yearly CO₂ emissions per person for each country.")

    
        df_co2 = df.dropna(subset=["CO2 Emissions (Tons/Capita)"])
        df_co2["Year"] = df_co2["Year"].astype(str)

        #Creatin an animated scatter plot using built-in color scale
        fig1 = px.scatter_geo(
            df_co2,
            locations="Country",
            locationmode="country names",
            color="CO2 Emissions (Tons/Capita)",
            size="CO2 Emissions (Tons/Capita)",
            animation_frame="Year",
            
            projection="natural earth",
            color_continuous_scale="Reds",  # Use built-in color scale for simplicity
            size_max=50,
            range_color=[df_co2["CO2 Emissions (Tons/Capita)"].min(), df_co2["CO2 Emissions (Tons/Capita)"].max()],
            title="Yearly CO₂ Emissions per Person by Country"
        )

        # Clean up plot layout for a better view
        fig1.update_layout(
            geo=dict(showframe=False, showcoastlines=True),
            margin=dict(l=0, r=0, t=40, b=0),
            height=600
        )

        st.plotly_chart(fig1, use_container_width=True)



    # Tab-2: CO₂ Dropdown by Country

    with tab2:
        st.title("Per Capita CO₂ Emissions Trend (2000–2023)")
        st.markdown("Choose a country to see how its per-person CO₂ emissions have changed over the years.")

        
        df_trend = df.dropna(subset=["CO2 Emissions (Tons/Capita)"])
        df_trend = df_trend[df_trend["Year"].between(2000, 2023)]
        country_avg = df_trend.groupby(["Country", "Year"], as_index=False)["CO2 Emissions (Tons/Capita)"].mean()

        country_list = sorted(country_avg["Country"].unique())
        fig2 = go.Figure()

        # Add a line for each country 
        for idx, country in enumerate(country_list):
            country_data = country_avg[country_avg["Country"] == country]
            fig2.add_trace(go.Scatter(
                x=country_data["Year"],
                y=country_data["CO2 Emissions (Tons/Capita)"],
                mode="lines+markers",
                name=country,
                visible=(idx == 0)
            ))

        # Dropdown for country selection
        dropdown_options = []
        for i, country in enumerate(country_list):
            visibility = [False] * len(country_list)
            visibility[i] = True
            dropdown_options.append(dict(
                label=country,
                method="update",
                args=[{"visible": visibility}, {"title": f"CO₂ Emissions for {country}"}]
            ))

        
        fig2.update_layout(
            updatemenus=[dict(
                buttons=dropdown_options,
                direction="down",
                x=1.05,
                xanchor="left",
                y=1.1,
                showactive=True
            )],
            title=f"CO₂ Emissions for {country_list[0]}",
            xaxis_title="Year",
            yaxis_title="Tons of CO₂ per Person",
            height=500
        )

        
        st.plotly_chart(fig2, use_container_width=True)



    # Tab-3:Forest Area vs Climate
    with tab3:
        st.title("Impact of Forest Area on Climate Metrics")
        st.markdown("Choose a country to view how forest coverage relates to key climate indicators over time.")

        grouped_df = df.groupby(['Country', 'Year'], as_index=False).mean(numeric_only=True)

        selected_country = st.selectbox("Select a Country", sorted(grouped_df["Country"].unique()), key="country_selector_tab3")
        country_df = grouped_df[grouped_df["Country"] == selected_country]

        climate_factors = [
            ("Sea Level Rise (mm)", "Sea Level", "blue"),
            ("Avg Temperature (°C)", "Temperature", "crimson"),
            ("Rainfall (mm)", "Rainfall", "teal"),
            ("Extreme Weather Events", "Extreme Events", "orange")
        ]

        fig3 = sp.make_subplots(
            rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.07,
            subplot_titles=[f"{label} vs Forest Area" for _, label, _ in climate_factors],
            specs=[[{"secondary_y": True}]] * 4
        )

        for idx, (column, label, color) in enumerate(climate_factors):
            row_num = idx + 1

            # Climate indicator
            fig3.add_trace(go.Scatter(
                x=country_df["Year"],
                y=country_df[column],
                mode="lines+markers",
                name=f"{label} ({column})",
                line=dict(color=color)
            ), row=row_num, col=1, secondary_y=False)

            # Forest area
            fig3.add_trace(go.Scatter(
                x=country_df["Year"],
                y=country_df["Forest Area (%)"],
                mode="lines+markers",
                name=f"Forest Area (%) – {label}",
                line=dict(color="darkgreen", dash="dot"),
                showlegend = (idx==0)
            ), row=row_num, col=1, secondary_y=True)

            fig3.update_yaxes(title_text=label, row=row_num, col=1, secondary_y=False)
            fig3.update_yaxes(title_text="Forest Area (%)", row=row_num, col=1, secondary_y=True)

        fig3.update_layout(
            height=1400,
            title_text=f"Climate Trends vs Forest Area in {selected_country}",
            showlegend=True,  # <== Enable the legend
            margin=dict(t=80, l=60, r=60, b=60),
            xaxis=dict(tickmode="linear", dtick=1)
        )

        st.plotly_chart(fig3, use_container_width=True)

    # Tab-4: Animated Global Temperature Map

    with tab4:
        st.title("Global Average Temperature (2000–2023)")
        st.markdown("An animated world map showing how average temperatures have changed across countries each year.")

        
        df_temp = df.dropna(subset=["Avg Temperature (°C)", "Year"])
        df_temp["Year"] = df_temp["Year"].astype(int)

        # Calculate global fixed min/max for consistent color scaling
        temp_min = df_temp["Avg Temperature (°C)"].min()
        temp_max = df_temp["Avg Temperature (°C)"].max()

        # Group by country and year to get average temperature
        temp_grouped = df_temp.groupby(["Country", "Year"], as_index=False)["Avg Temperature (°C)"].mean()

    
        temp_grouped["Year"] = temp_grouped["Year"].astype(str)

        # Create animated choropleth
        fig4 = px.choropleth(
            temp_grouped,
            locations="Country",
            locationmode="country names",
            color="Avg Temperature (°C)",
            animation_frame="Year",
            color_continuous_scale="thermal",
            range_color=[temp_min, temp_max],
            projection="natural earth",
            title="Yearly Average Temperature by Country"
        )

        fig4.update_geos(showframe=False, showcoastlines=True)
        fig4.update_layout(
            margin=dict(l=0, r=0, t=60, b=0),
            height=600,
            coloraxis_colorbar=dict(title="Average Temp (°C)")
        )

        st.plotly_chart(fig4, use_container_width=True)

