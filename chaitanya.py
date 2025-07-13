import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def run():
    # Load dataset
    data = pd.read_csv("chaitanya_climate_change_dataset.csv")

    st.title("Climate Impact Dashboard")
    st.markdown(
        """
        This dashboard provides an interactive platform to explore key global climate change indicators.

        Features include:
        - Analysis of temperature, CO₂ emissions, sea level rise, and extreme weather events over time.
        - Country-specific climate trends through dynamic visualizations.
        - Examination of the relationship between forest coverage, renewable energy adoption, and carbon emissions.
        """
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "Global Emissions and Temperature Over Time",
        "Global Trends: Temperature and CO₂",
        "Forest Area vs CO₂ Emissions",
        "Forest Cover vs Renewable Energy",
        
    ])

    latest_year = data["Year"].max()
    year_data = data[data["Year"] == latest_year]

    scatter_data = year_data.dropna(
        subset=[
            'Avg Temperature (°C)',
            'CO2 Emissions (Tons/Capita)',
            'Sea Level Rise (mm)',
            'Extreme Weather Events',
            'Population'
        ]
    )

    grouped = scatter_data.copy()
    grouped['Weighted CO2'] = grouped['CO2 Emissions (Tons/Capita)'] * grouped['Population']

    agg_data = grouped.groupby("Country").agg({
        'Avg Temperature (°C)': 'mean',
        'Weighted CO2': 'sum',
        'Population': 'sum',
        'Sea Level Rise (mm)': 'max',
        'Extreme Weather Events': 'max'
    }).reset_index()

    agg_data['CO2 Emissions (Tons/Capita)'] = agg_data['Weighted CO2'] / agg_data['Population']
    final_data = agg_data.drop(columns=['Weighted CO2'])

    with tab1:
        st.subheader("Global Emissions and Temperature Over Time")
        st.markdown(
            "Visualize the correlation between average temperature, carbon emissions, and sea level rise globally over the years."
        )

        anim_data = data.dropna(
            subset=[
                'Avg Temperature (°C)',
                'CO2 Emissions (Tons/Capita)',
                'Sea Level Rise (mm)',
                'Extreme Weather Events',
                'Population',
                'Country',
                'Year'
            ]
        )

        anim_data['Weighted CO2'] = anim_data['CO2 Emissions (Tons/Capita)'] * anim_data['Population']
        anim_grouped = anim_data.groupby(['Year', 'Country']).agg({
            'Avg Temperature (°C)': 'mean',
            'Weighted CO2': 'sum',
            'Population': 'sum',
            'Sea Level Rise (mm)': 'max',
            'Extreme Weather Events': 'max'
        }).reset_index()

        anim_grouped['CO2 Emissions (Tons/Capita)'] = anim_grouped['Weighted CO2'] / anim_grouped['Population']
        anim_final = anim_grouped.drop(columns=['Weighted CO2'])

        fig_anim = px.scatter(
            anim_final,
            x="CO2 Emissions (Tons/Capita)",
            y="Avg Temperature (°C)",
            animation_frame="Year",
            animation_group="Country",
            size="Sea Level Rise (mm)",
            color="Extreme Weather Events",
            hover_name="Country",
            range_x=[0, anim_final["CO2 Emissions (Tons/Capita)"].max() + 1],
            range_y=[anim_final["Avg Temperature (°C)"].min() - 1, anim_final["Avg Temperature (°C)"].max() + 1],
            labels={
                "CO2 Emissions (Tons/Capita)": "CO₂ per Capita",
                "Avg Temperature (°C)": "Average Temperature (°C)",
                "Extreme Weather Events": "Extreme Weather Events",
                "Sea Level Rise (mm)": "Sea Level Rise (mm)"
            },
            title="Climate Risk Evolution Over Time (Bubble Size = Sea Level Rise in mm)",
            height=600
        )
        fig_anim.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000
        fig_anim.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 300
        fig_anim.update_traces(marker=dict(opacity=0.8, line=dict(width=0.5, color='DarkSlateGrey')))
        st.plotly_chart(fig_anim)

    with tab2:
        st.subheader("Global Trends: Temperature and CO₂ Emissions")
        st.markdown(
            "Yearly global trends of temperature and population-weighted CO₂ emissions to highlight potential correlations."
        )

        data["Weighted CO2"] = data["CO2 Emissions (Tons/Capita)"] * data["Population"]
        co2_weighted = data.groupby("Year").agg({
            "Weighted CO2": "sum",
            "Population": "sum",
            "Avg Temperature (°C)": "mean"
        }).reset_index()
        co2_weighted["CO2 Emissions (Tons/Capita)"] = co2_weighted["Weighted CO2"] / co2_weighted["Population"]
        avg_per_year = co2_weighted[["Year", "Avg Temperature (°C)", "CO2 Emissions (Tons/Capita)"]]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=avg_per_year["Year"],
            y=avg_per_year["Avg Temperature (°C)"],
            name="Avg Temp (°C)",
            yaxis="y1",
            mode="lines+markers",
            marker=dict(symbol="circle", size=8, color="#FF5733"),
            line=dict(color="#FF5733", width=3),
            hovertemplate="Temp: %{y:.2f}°C<br>Year: %{x}<extra></extra>"
        ))

        fig.add_trace(go.Scatter(
            x=avg_per_year["Year"],
            y=avg_per_year["CO2 Emissions (Tons/Capita)"],
            name="CO₂ Emissions (Tons/Capita)",
            yaxis="y2",
            mode="lines+markers",
            marker=dict(symbol="diamond", size=8, color="#00BFFF"),
            line=dict(color="#00BFFF", width=3, dash="dot"),
            hovertemplate="CO₂: %{y:.2f} tons per capita<br>Year: %{x}<extra></extra>"
        ))

        fig.update_layout(
            title="Global Temperature and CO₂ Emissions Over Time",
            xaxis=dict(title="Year"),
            yaxis=dict(
                title="Average Temperature (°C)",
                titlefont=dict(color="#FF5733"),
                tickfont=dict(color="#FF5733"),
                showgrid=True,
                gridcolor='rgba(255, 87, 51, 0.1)'
            ),
            yaxis2=dict(
                title="CO₂ Emissions (tons per capita)",
                titlefont=dict(color="#00BFFF"),
                tickfont=dict(color="#00BFFF"),
                overlaying="y",
                side="right",
                showgrid=False
            ),
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font=dict(color="white"),
            hovermode="closest",
            template="plotly_dark",
            height=600,
            legend=dict(x=0.01, y=0.99)
        )

        st.plotly_chart(fig)

    with tab3:
        st.subheader("Forest Area vs CO₂ Emissions by Year")
        st.markdown(
            "Examining the relationship between forest coverage and carbon emissions across countries and years."
        )

        forest_data = data.dropna(subset=[
            'Forest Area (%)',
            'CO2 Emissions (Tons/Capita)',
            'Population',
            'Year',
            'Country'
        ]).copy()

        forest_data['Weighted CO2'] = forest_data['CO2 Emissions (Tons/Capita)'] * forest_data['Population']

        forest_grouped = forest_data.groupby(['Year', 'Country']).agg({
            'Forest Area (%)': 'max',
            'Weighted CO2': 'sum',
            'Population': 'sum'
        }).reset_index()

        forest_grouped['CO2 Emissions (Tons/Capita)'] = forest_grouped['Weighted CO2'] / forest_grouped['Population']
        forest_final = forest_grouped.drop(columns=['Weighted CO2'])

        forest_fig = px.scatter(
            forest_final,
            x="Forest Area (%)",
            y="CO2 Emissions (Tons/Capita)",
            animation_frame="Year",
            animation_group="Country",
            hover_name="Country",
            color_discrete_sequence=["#90ee90"],
            range_x=[forest_final["Forest Area (%)"].min() - 5, forest_final["Forest Area (%)"].max() + 5],
            range_y=[0, forest_final["CO2 Emissions (Tons/Capita)"].max() + 1],
            labels={
                "Forest Area (%)": "Forest Cover (%)",
                "CO2 Emissions (Tons/Capita)": "CO₂ per Capita"
            },
            title="Forest Area vs CO₂ Emissions by Year",
            height=650
        )
        forest_fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000
        forest_fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 300

        forest_fig.update_traces(marker=dict(size=12, opacity=0.75, line=dict(width=0.5, color='black')))
        forest_fig.update_layout(
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font=dict(color="white"),
            hovermode="closest",
            template="plotly_dark"
        )

        st.plotly_chart(forest_fig)

    with tab4:
        st.subheader("Forest Cover and Renewable Energy Over Time")
        st.markdown(
            "Explore the relationship between forest cover and renewable energy adoption. Bubble size represents carbon emissions per capita (weighted)."
        )

        forest_renew_data = data.dropna(subset=[
            'Forest Area (%)',
            'Renewable Energy (%)',
            'CO2 Emissions (Tons/Capita)',
            'Population',
            'Year',
            'Country'
        ]).copy()

        forest_renew_data['Weighted CO2'] = forest_renew_data['CO2 Emissions (Tons/Capita)'] * forest_renew_data['Population']

        forest_renew_grouped = forest_renew_data.groupby(['Year', 'Country']).agg({
            'Forest Area (%)': 'max',
            'Renewable Energy (%)': 'max',
            'Weighted CO2': 'sum',
            'Population': 'sum'
        }).reset_index()

        forest_renew_grouped['CO2 Emissions (Tons/Capita)'] = forest_renew_grouped['Weighted CO2'] / forest_renew_grouped['Population']
        forest_renew_grouped = forest_renew_grouped.drop(columns=["Weighted CO2"])

        bubble_fig = px.scatter(
            forest_renew_grouped,
            x="Forest Area (%)",
            y="Renewable Energy (%)",
            size="CO2 Emissions (Tons/Capita)",
            animation_frame="Year",
            animation_group="Country",
            hover_name="Country",
            color_discrete_sequence=["#2ecc71"],
            labels={
                "Forest Area (%)": "Forest Cover (%)",
                "Renewable Energy (%)": "Renewable Energy (%)",
                "CO2 Emissions (Tons/Capita)": "CO₂ Weighted per Capita"
            },
            title="Forest Cover vs Renewable Energy (Bubble = Weighted CO₂ per Capita)",
            height=650
        )
        bubble_fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000
        bubble_fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 300

        bubble_fig.update_traces(marker=dict(opacity=0.8, line=dict(width=0.5, color='black')))
        bubble_fig.update_layout(
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font=dict(color="white"),
            hovermode="closest",
            template="plotly_dark"
        )

        st.plotly_chart(bubble_fig)

    