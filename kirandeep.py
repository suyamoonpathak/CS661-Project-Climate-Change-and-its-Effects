import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import scipy.stats as stats

def run():
    # Streamlit page configuration
    st.set_page_config(page_title="Climate and Disease Analytics", layout="wide")

    # Custom CSS for styling
    st.markdown("""
        <style>
        .main { padding: 20px; }
        .stButton > button { background-color: #3b82f6; color: white; padding: 8px 16px; border-radius: 4px; }
        .stButton > button:hover { background-color: #1d4ed8; }
        .stSelectbox, .stSlider { background-color: #f3f4f6; padding: 10px; border-radius: 4px; }
        h1, h2 { font-weight: bold; }
        .plotly-chart-container { width: 100% !important; max-width: 1200px; margin: auto; }
        .disease-select { max-width: 300px; margin: auto; }
        </style>
    """, unsafe_allow_html=True)

    # Calculate Pearson correlation
    def calculate_correlation(x, y):
        if len(x) != len(y) or len(x) == 0:
            return 0
        return np.corrcoef(x, y)[0, 1]

    # Load and clean data
    @st.cache_data
    def load_and_clean_data():
        file_path = Path("climate_disease_dataset.csv")
        try:
            if not file_path.exists():
                st.error(f"Error: The file '{file_path}' was not found. Please ensure it exists in '/Users/kirandeep/Documents/myProject@IITK/'.")
                return None
            df = pd.read_csv(file_path)
            df = df.rename(columns=lambda x: x.strip().replace('"', ''))
            df = df.apply(lambda x: x.str.strip().replace('"', '') if x.dtype == "object" else x)
            
            numeric_columns = ['year', 'month', 'avg_temp_c', 'precipitation_mm', 'air_quality_index', 
                            'uv_index', 'malaria_cases', 'dengue_cases', 'population_density', 'healthcare_budget']
            for col in numeric_columns:
                if col not in df.columns:
                    st.error(f"Missing column: {col}. Check CSV structure.")
                    return None
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            if df[numeric_columns].isna().any().any():
                st.warning("Some values in numeric columns were set to NaN. Check your CSV for invalid data.")
            
            df = df.astype({
                'year': 'int32',
                'month': 'int32',
                'avg_temp_c': 'float32',
                'precipitation_mm': 'float32',
                'air_quality_index': 'float32',
                'uv_index': 'float32',
                'malaria_cases': 'int32',
                'dengue_cases': 'int32',
                'population_density': 'int32',
                'healthcare_budget': 'int32'
            }, errors='ignore')
            
            df = df.dropna()
            df = df[(df['year'] >= 2000) & (df['year'] <= 2023) & (df['month'].between(1, 12)) &
                    (df['malaria_cases'] >= 0) & (df['dengue_cases'] >= 0)]
            if df.empty:
                st.error("No valid data remains after cleaning. Ensure the CSV has valid data for 2000–2023.")
                return None
            return df
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return None

    # Aggregate seasonal data
    def aggregate_seasonal_data(df):
        monthly_data = df.groupby('month').agg({
            'malaria_cases': 'mean',
            'dengue_cases': 'mean',
            'avg_temp_c': 'mean',
            'precipitation_mm': 'mean'
        }).reset_index()
        return monthly_data

    # Compute correlation matrix
    def compute_correlation_matrix(df):
        variables = ['avg_temp_c', 'precipitation_mm', 'air_quality_index', 'uv_index', 'malaria_cases', 'dengue_cases']
        labels = ['Temperature', 'Precipitation', 'AQI', 'UV Index', 'Malaria', 'Dengue']
        corr_matrix = pd.DataFrame(index=labels, columns=labels)
        for i, v1 in enumerate(variables):
            for j, v2 in enumerate(variables):
                corr_matrix.iloc[i, j] = calculate_correlation(df[v1], df[v2])
        return corr_matrix.astype(float)

    # Country coordinates
    country_coordinates = {
        'Palestinian Territory': {'lat': 31.9522, 'lon': 35.2332},
        'India': {'lat': 20.5937, 'lon': 78.9629},
        'Brazil': {'lat': -14.2350, 'lon': -51.9253},
        'Nigeria': {'lat': 9.0820, 'lon': 8.6753},
        'Thailand': {'lat': 15.8700, 'lon': 100.9925},
        # Add other countries from your dataset if needed
    }


    st.title("Climate and Disease Analytics")
    st.markdown("Analyze climate-disease relationships across countries (2000–2023).")

    # Disease selection at top middle
    st.markdown("<div class='disease-select'>", unsafe_allow_html=True)
    disease = st.selectbox("Select Disease", ["malaria", "dengue"], key="global_disease")
    st.markdown("</div>", unsafe_allow_html=True)

    # Load data
    df = load_and_clean_data()
    if df is None:
        return

    # Get unique countries
    countries = sorted(df['country'].unique().tolist())

    # 3D Time-Series Surface Plot
    st.subheader("3D Time-Series Surface Plot")
    with st.expander("Controls", expanded=True):
        surface_country = st.selectbox("Country", countries, key="surface_country")
        surface_year_range = st.slider("Year Range", 2000, 2023, (2000, 2023), key="surface_years")
    surface_df = df[(df['year'].between(surface_year_range[0], surface_year_range[1])) & (df['country'] == surface_country)]
    if surface_df.empty:
        st.warning(f"No data for {surface_country} in selected year range.")
    else:
        pivot_data = surface_df.pivot_table(index='year', columns='month', values=f'{disease}_cases', aggfunc='mean')
        if pivot_data.empty:
            st.warning(f"No {disease} case data for {surface_country} in selected years.")
        else:
            fig_surface = go.Figure(data=[go.Surface(z=pivot_data.values, x=pivot_data.columns, y=pivot_data.index, colorscale='Viridis')])
            fig_surface.update_layout(
                scene=dict(
                    xaxis_title='Month',
                    yaxis_title='Year',
                    zaxis_title=f'{disease.capitalize()} Cases',
                    aspectratio=dict(x=1, y=1, z=0.7)
                ),
                height=600,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(fig_surface, use_container_width=True)

    # 3D Climate-Disease Correlation Plot
    st.subheader("3D Climate-Disease Correlation")
    with st.expander("Controls", expanded=True):
        scatter_countries = st.multiselect("Countries (up to 4)", countries, max_selections=4, key="scatter_countries")
        scatter_year_range = st.slider("Year Range", 2000, 2023, (2000, 2023), key="scatter_years")
    scatter_df = df[(df['year'].between(scatter_year_range[0], scatter_year_range[1]))]
    if scatter_countries:
        scatter_df = scatter_df[scatter_df['country'].isin(scatter_countries)]
    if scatter_df.empty:
        st.warning("No data for selected countries and year range.")
    else:
        fig_scatter = px.scatter_3d(
            scatter_df,
            x='avg_temp_c',
            y='precipitation_mm',
            z=f'{disease}_cases',
            color='country',
            size=f'{disease}_cases',
            size_max=20,
            title="Temperature vs Precipitation vs Disease Cases",
            hover_data=['year', 'month']
        )
        fig_scatter.update_layout(
            scene=dict(
                xaxis_title='Temperature (°C)',
                yaxis_title='Precipitation (mm)',
                zaxis_title=f'{disease.capitalize()} Cases',
                aspectratio=dict(x=1, y=1, z=0.7)
            ),
            height=600,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Correlation Matrix
    st.subheader("Correlation Matrix")
    with st.expander("Controls", expanded=True):
        corr_countries = st.multiselect("Countries (up to 4)", countries, max_selections=4, key="corr_countries")
        corr_year_range = st.slider("Year Range", 2000, 2023, (2000, 2023), key="corr_years")
    corr_df = df[(df['year'].between(corr_year_range[0], corr_year_range[1]))]
    if corr_countries:
        corr_df = corr_df[corr_df['country'].isin(corr_countries)]
    if corr_df.empty:
        st.warning("No data for selected countries and year range.")
    else:
        corr_matrix = compute_correlation_matrix(corr_df)
        fig_corr, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax)
        st.pyplot(fig_corr)

    # Seasonal Patterns (Polar)
    st.subheader("Seasonal Patterns (Polar)")
    with st.expander("Controls", expanded=True):
        polar_country = st.selectbox("Country", countries, key="polar_country")
        polar_year_range = st.slider("Year Range", 2000, 2023, (2000, 2023), key="polar_years")
        seasonal_plot_type = st.selectbox("Plot Type", ["Cases vs. Cases", "Climate vs. Climate"], key="seasonal_plot")
    polar_df = df[(df['year'].between(polar_year_range[0], polar_year_range[1])) & (df['country'] == polar_country)]
    if polar_df.empty:
        st.warning(f"No data for {polar_country} in selected year range.")
    else:
        seasonal_data = aggregate_seasonal_data(polar_df)
        if seasonal_plot_type == "Cases vs. Cases":
            malaria_norm = (seasonal_data['malaria_cases'] - seasonal_data['malaria_cases'].min()) / (seasonal_data['malaria_cases'].max() - seasonal_data['malaria_cases'].min() + 1e-10)
            dengue_norm = (seasonal_data['dengue_cases'] - seasonal_data['dengue_cases'].min()) / (seasonal_data['dengue_cases'].max() - seasonal_data['dengue_cases'].min() + 1e-10)
            fig_polar = go.Figure()
            fig_polar.add_trace(go.Scatterpolar(
                r=malaria_norm,
                theta=seasonal_data['month'] * 30,
                name='Malaria Cases (Normalized)',
                customdata=seasonal_data[['malaria_cases', 'dengue_cases']],
                hovertemplate='Month: %{theta}<br>Malaria: %{customdata[0]:.2f}<br>Dengue: %{customdata[1]:.2f}<extra></extra>'
            ))
            fig_polar.add_trace(go.Scatterpolar(
                r=dengue_norm,
                theta=seasonal_data['month'] * 30,
                name='Dengue Cases (Normalized)',
                customdata=seasonal_data[['malaria_cases', 'dengue_cases']],
                hovertemplate='Month: %{theta}<br>Malaria: %{customdata[0]:.2f}<br>Dengue: %{customdata[1]:.2f}<extra></extra>'
            ))
            fig_polar.update_layout(
                title="Malaria vs. Dengue Cases (Normalized)",
                polar=dict(radialaxis=dict(visible=True, range=[0, 1]), angularaxis=dict(tickvals=list(range(0, 360, 30)), ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])),
                height=600
            )
        else:
            temp_norm = (seasonal_data['avg_temp_c'] - seasonal_data['avg_temp_c'].min()) / (seasonal_data['avg_temp_c'].max() - seasonal_data['avg_temp_c'].min() + 1e-10)
            precip_norm = (seasonal_data['precipitation_mm'] - seasonal_data['precipitation_mm'].min()) / (seasonal_data['precipitation_mm'].max() - seasonal_data['precipitation_mm'].min() + 1e-10)
            fig_polar = go.Figure()
            fig_polar.add_trace(go.Scatterpolar(
                r=temp_norm,
                theta=seasonal_data['month'] * 30,
                name='Temperature (Normalized)',
                customdata=seasonal_data[['avg_temp_c', 'precipitation_mm']],
                hovertemplate='Month: %{theta}<br>Temperature: %{customdata[0]:.2f}°C<br>Precipitation: %{customdata[1]:.2f}mm<extra></extra>'
            ))
            fig_polar.add_trace(go.Scatterpolar(
                r=precip_norm,
                theta=seasonal_data['month'] * 30,
                name='Precipitation (Normalized)',
                customdata=seasonal_data[['avg_temp_c', 'precipitation_mm']],
                hovertemplate='Month: %{theta}<br>Temperature: %{customdata[0]:.2f}°C<br>Precipitation: %{customdata[1]:.2f}mm<extra></extra>'
            ))
            fig_polar.update_layout(
                title="Temperature vs. Precipitation (Normalized)",
                polar=dict(radialaxis=dict(visible=True, range=[0, 1]), angularaxis=dict(tickvals=list(range(0, 360, 30)), ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])),
                height=600
            )
        st.plotly_chart(fig_polar, use_container_width=True)

    # Isocontour Plot
    st.subheader(f"{disease.capitalize()} Cases Isocontour (Temperature vs. Precipitation)")
    with st.expander("Controls", expanded=True):
        iso_countries = st.multiselect("Countries (up to 2)", countries, max_selections=2, key="iso_countries")
        iso_year_range = st.slider("Year Range", 2000, 2023, (2000, 2023), key="iso_years")
    iso_df = df[(df['year'].between(iso_year_range[0], iso_year_range[1]))]
    if iso_countries:
        iso_df = iso_df[iso_df['country'].isin(iso_countries)]
    if iso_df.empty:
        st.warning("No data for selected countries and year range.")
    else:
        iso_data = iso_df[['avg_temp_c', 'precipitation_mm', f'{disease}_cases']]
        x = np.linspace(iso_data['avg_temp_c'].min(), iso_data['avg_temp_c'].max(), 100)
        y = np.linspace(iso_data['precipitation_mm'].min(), iso_data['precipitation_mm'].max(), 100)
        X, Y = np.meshgrid(x, y)
        Z = stats.gaussian_kde([iso_data['avg_temp_c'], iso_data['precipitation_mm']])([X.ravel(), Y.ravel()]).reshape(X.shape)
        Z = Z * iso_data[f'{disease}_cases'].mean()
        fig_iso = go.Figure(data=go.Contour(
            x=x,
            y=y,
            z=Z,
            colorscale='Viridis',
            contours=dict(showlabels=True, labelfont=dict(size=12)),
            hoverinfo='x+y+z',
            colorbar_title=f'{disease.capitalize()} Cases (Scaled)'
        ))
        fig_iso.update_layout(
            title=f"{disease.capitalize()} Cases Isocontour",
            xaxis_title="Temperature (°C)",
            yaxis_title="Precipitation (mm)",
            height=600
        )
        st.plotly_chart(fig_iso, use_container_width=True)

