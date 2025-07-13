import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import seaborn as sns
import warnings

def run():
    warnings.filterwarnings('ignore')

    st.set_page_config(
        page_title="Global Temperature Analysis Dashboard",
        layout="wide"
    )

    st.title("Global Temperature Analysis Dashboard")

    @st.cache_data
    def load_country_data():
        df = pd.read_csv("GlobalLandTemperaturesByCountry.csv")
        drop = ['Denmark', 'Antarctica', 'France', 'Europe', 'Netherlands', 
                'United Kingdom', 'Africa', 'South America']
        df = df[~df.Country.isin(drop)].replace({
            'Denmark (Europe)': 'Denmark',
            'France (Europe)': 'France',
            'Netherlands (Europe)': 'Netherlands',
            'United Kingdom (Europe)': 'United Kingdom'
        })
        df['Year'] = pd.to_datetime(df.dt).dt.year.astype(str)
        return df

    @st.cache_data
    def load_global_data():
        df = pd.read_csv("GlobalTemperatures.csv")
        df['Year'] = pd.to_datetime(df.dt).dt.year.astype(str)
        return df

    country_df = load_country_data()
    global_df = load_global_data()

    # 1. Global temperature map
    st.header("1) Average land temperature in countries")

    countries = country_df.Country.unique()
    mean_temp = [country_df[country_df.Country == c].AverageTemperature.mean() for c in countries]

    choropleth = dict(
        type="choropleth",
        locations=countries,
        z=mean_temp,
        locationmode="country names",
        text=countries,
        marker=dict(line=dict(color="rgb(0,0,0)", width=1)),
        colorbar=dict(title="# Average\nTemperature, °C")
    )

    layout_map = dict(
        title="Average land temperature in countries",
        geo=dict(
            showframe=False,
            showocean=True,
            oceancolor="rgb(0,255,255)",
            projection=dict(type="orthographic", rotation=dict(lon=60, lat=10)),
            lonaxis=dict(showgrid=True, gridcolor="rgb(102,102,102)"),
            lataxis=dict(showgrid=True, gridcolor="rgb(102,102,102)")
        )
    )

    fig_map = go.Figure(data=[choropleth], layout=layout_map)
    st.plotly_chart(fig_map, use_container_width=True)

    # 2. Country ranking bar chart
    st.subheader("2) Country ranking by Avg Temperature")

    sorted_data = sorted(zip(mean_temp, countries), reverse=True)
    mean_bar, countries_bar = zip(*sorted_data[:10])

    fig, ax = plt.subplots(figsize=(5, 5))
    palette = sns.color_palette("coolwarm", len(countries_bar))
    sns.barplot(x=list(mean_bar), y=list(countries_bar), palette=palette[::-1], ax=ax)

    ax.set_xlabel("Average temperature (°C)")
    ax.set_title("Top 10 Countries by Average Land Temperature", fontsize=8)
    ax.tick_params(labelsize=5)
    fig.tight_layout()

    st.pyplot(fig)

    # 3. Global average temperature trend
    st.header("3) Average land temperature in world")

    years = sorted(global_df.Year.unique())
    mean_world = [global_df[global_df.Year == y].LandAverageTemperature.mean() for y in years]
    unc_world = [global_df[global_df.Year == y].LandAverageTemperatureUncertainty.mean() for y in years]

    trace0 = go.Scatter(
        x=years,
        y=np.array(mean_world) + np.array(unc_world),
        mode="lines",
        name="Uncertainty top",
        line=dict(color="rgb(0,255,255)")
    )
    trace1 = go.Scatter(
        x=years,
        y=np.array(mean_world) - np.array(unc_world),
        fill="tonexty",
        mode="lines",
        name="Uncertainty bot",
        line=dict(color="rgb(0,255,255)")
    )
    trace2 = go.Scatter(
        x=years,
        y=mean_world,
        name="Average Temperature",
        line=dict(color="rgb(199,121,93)")
    )

    layout_world = go.Layout(
        xaxis=dict(title="Year"),
        yaxis=dict(title="Average Temperature (°C)"),
        title="Average Land Temperature in World",
        showlegend=True,
        margin=dict(l=50, r=50, t=50, b=50),
        height=500,
        width=900
    )

    fig_world = go.Figure(data=[trace0, trace1, trace2], layout=layout_world)
    st.plotly_chart(fig_world, use_container_width=False)

    # 4. Decadal temperature map
    st.header("4) Average temperature changes every 10 years")

    decade_years = sorted([str(y) for y in range(1750, 2014, 10)])
    selected_decade = st.selectbox("Select Decade", decade_years)

    df_decade = country_df[country_df['Year'] == selected_decade]
    mean_temp_decade = [df_decade[df_decade['Country'] == c]['AverageTemperature'].mean() for c in countries]

    choropleth_decade = dict(
        type="choropleth",
        locations=countries,
        z=mean_temp_decade,
        locationmode="country names",
        text=countries,
        marker=dict(line=dict(color="rgb(0,0,0)", width=1)),
        colorbar=dict(title="# Avg Temp, °C")
    )

    layout_decade = dict(
        title=f"Average Land Temperature in Countries ({selected_decade})",
        geo=dict(
            showframe=False,
            showocean=True,
            oceancolor="rgb(0,255,255)",
            projection=dict(type="equirectangular")
        )
    )

    fig_decade = go.Figure(data=[choropleth_decade], layout=layout_decade)
    st.plotly_chart(fig_decade, use_container_width=True)

    # 5. Annual temperature by continent
    st.header("5) Annual temperature changes on the continents")

    continent = ['Russia', 'United States', 'Niger', 'Greenland', 'Australia', 'Bolivia']
    years_all = sorted(country_df['Year'].unique())
    years_plot = years_all[70:]

    mean_temp_by_cont = np.zeros((len(continent), len(years_plot)))

    for j, c in enumerate(continent):
        sub = country_df[country_df['Country'] == c]
        for i, yr in enumerate(years_plot):
            vals = sub[sub['Year'] == yr]['AverageTemperature']
            mean_temp_by_cont[j, i] = vals.mean() if not vals.empty else np.nan

    colors = ['rgb(0,255,255)', 'rgb(255,0,255)', 'rgb(0,0,0)', 
            'rgb(255,0,0)', 'rgb(0,255,0)', 'rgb(0,0,255)']

    traces = [
        go.Scatter(
            x=years_plot,
            y=mean_temp_by_cont[i],
            mode='lines',
            name=continent[i],
            line=dict(color=colors[i])
        ) for i in range(len(continent))
    ]

    layout_cont = go.Layout(
        title="Average land temperature on the continents",
        xaxis=dict(title="Year"),
        yaxis=dict(title="Average Temperature (°C)")
    )

    fig_cont = go.Figure(data=traces, layout=layout_cont)
    st.plotly_chart(fig_cont, use_container_width=True)