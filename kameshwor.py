import streamlit as st 
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

def run():
    # Set layout
    st.set_page_config(page_title="Climate Dashboard", layout="wide")
    # Load dataset
    df = pd.read_csv('climate_change_dataset.csv')
    # Prepare grouped data(avg and Max)
    df_sorted = df.sort_values(by=['Country', 'Year'])
    df_avg = df_sorted.groupby(['Country', 'Year']).mean(numeric_only=True).reset_index()
    df_agg = df_sorted.groupby(['Country', 'Year']).max(numeric_only=True).reset_index()

    # Interpolation for Sea Level (filled_data)
    all_years = pd.Series(range(df_avg['Year'].min(), df_avg['Year'].max() + 1))
    numeric_cols = df_avg.columns.drop(['Country', 'Year'])

    filled_data = pd.DataFrame()
    for country in df_avg['Country'].unique():
        country_data = df_avg[df_avg['Country'] == country].set_index('Year')
        country_data = country_data.reindex(all_years)
        country_data['Country'] = country
        country_data[numeric_cols] = country_data[numeric_cols].interpolate()
        country_data = country_data.reset_index().rename(columns={'index': 'Year'})
        filled_data = pd.concat([filled_data, country_data], ignore_index=True)

    filled_data = filled_data.sort_values(by=['Country', 'Year']).reset_index(drop=True)

    #Interpolation for Population (filled_data1)
    all_years = pd.Series(range(df_agg['Year'].min(), df_agg['Year'].max() + 1))
    numeric_cols = df_agg.columns.drop(['Country', 'Year'])

    filled_data1 = pd.DataFrame()
    for country in df_agg['Country'].unique():
        country_data = df_agg[df_agg['Country'] == country].set_index('Year')
        country_data = country_data.reindex(all_years)
        country_data['Country'] = country
        country_data[numeric_cols] = country_data[numeric_cols].interpolate()
        country_data = country_data.reset_index().rename(columns={'index': 'Year'})
        filled_data1 = pd.concat([filled_data1, country_data], ignore_index=True)

    filled_data1 = filled_data1.sort_values(by=['Country', 'Year']).reset_index(drop=True)

    # Update population growth rate
    filled_data1['Population Growth Rate (%)'] = filled_data1.groupby('Country')['Population'].pct_change() * 100

    # Setup 
    countries_sea = sorted(filled_data['Country'].unique())
    years_sea = sorted(filled_data['Year'].unique())

    countries_pop = sorted(filled_data1['Country'].unique())
    years_pop = sorted(filled_data1['Year'].unique())

    #Create Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Sea Level Rise", "Climate Correlation", "Population Growth", "Growth Rate (%)"])
    
    # Tab 1: Sea Level Rise 
    with tab1:
        st.header("Sea Level Rise Visualization")
        selected_country = st.selectbox("Select Country", countries_sea)

        #Bar Plot: Sea Level Rise by Year (for selected country)
        def plot_sea_level(country):
            data = filled_data[filled_data['Country'] == country]
            fig = px.bar(
                data, x='Year', y='Sea Level Rise (mm)', color='Sea Level Rise (mm)',
                color_continuous_scale=px.colors.sequential.Blues, range_color=[0, 6],
                title=f'Sea Level Rise in {country} Over Years',
                hover_data={'Year': True}
            )
            fig.update_layout(
                height=450,
                margin=dict(l=50, r=50, t=50, b=50),
                plot_bgcolor='#eeeeee',
                xaxis=dict(showgrid=False),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(180,180,180,0.4)',
                    zeroline=False
                ),
                hovermode='x unified',
                coloraxis_showscale=False,
                title_font=dict(size=18)
            )
            st.plotly_chart(fig)

        #Animated plot for Sea Level Rise by Country over Time
        def plot_animated_sea_level():
            fig = px.bar(
                filled_data,
                x='Country',
                y='Sea Level Rise (mm)',
                animation_frame='Year',
                range_y=[0, 6],
                color='Sea Level Rise (mm)',
                color_continuous_scale=px.colors.sequential.Blues,
                title="Sea Level Rise by Country Over Time",
            )

            fig.update_layout(
                height=450,
                plot_bgcolor='#f5f5f5',
                margin=dict(l=50, r=50, t=50, b=50),
                hovermode='x unified',
                xaxis=dict(showgrid=False),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(180,180,180,0.3)',
                    zeroline=False
                ),
                coloraxis_showscale=False,
                font=dict(size=12),
                title_font=dict(size=18)
            )
            st.plotly_chart(fig)
        plot_sea_level(selected_country)
        plot_animated_sea_level()

        def plot_sea_level_by_decade():
            df_decade = filled_data.copy()
            df_decade['Decade'] = (df_decade['Year'] // 10) * 10
            decade_avg = df_decade.groupby('Decade')['Sea Level Rise (mm)'].mean().reset_index()

            fig = px.bar(
                decade_avg,
                x='Decade',
                y='Sea Level Rise (mm)',
                text='Sea Level Rise (mm)',
                color='Sea Level Rise (mm)',
                color_continuous_scale='Blues',
                title='Average Global Sea Level Rise by Decade',
            )

            fig.update_traces(
                marker_line_width=1.2,
                marker_line_color="gray",
                width=0.3,  # narrower bars
                texttemplate='%{text:.2f}',
                textposition='outside'
            )

            fig.update_layout(
                height=350,
                width=650,
                xaxis=dict(tickmode='linear'),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(200,200,200,0.3)',
                    zeroline=False
                ),
                plot_bgcolor='#f5f5f5',
                margin=dict(l=50, r=50, t=50, b=50),
                hovermode='x unified',
                coloraxis_showscale=False,
                title_font=dict(size=18),
                font=dict(size=12),
            )

            st.plotly_chart(fig)
        plot_sea_level_by_decade()




    #Tab2:Correlation Heatmap
    with tab2:
        st.header("Correlation Heatmap of Climate Indicators")

        numeric_data = filled_data.select_dtypes(include='number')
        correlation_matrix = numeric_data.corr()

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.heatmap(
            correlation_matrix, annot=True, fmt=".2f", cmap="YlGnBu",
            linewidths=0.5, linecolor="gray", ax=ax
        )
        st.pyplot(fig)
    #Tab:3
    with tab3:
        st.header("Population Growth Visualization")

        #Dropdown  Select Country
        selected_country_pop = st.selectbox("Select Country", countries_pop, key='pop')

        #Line Plot for Country-wise Population Growth Over Time
        def plot_population_growth(country):
            data = filled_data1[filled_data1['Country'] == country]
            fig = px.line(
                data, x='Year', y='Population', markers=True,
                title=f'Population Growth in {country}',
                labels={'Population': 'Population (billions)'},
                color_discrete_sequence=['#1f77b4']
            )
            fig.update_layout(
                height=500,
                plot_bgcolor='#eeeeee',
                hovermode='x unified',
                margin=dict(l=50, r=50, t=50, b=50),
                xaxis=dict(showgrid=False),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(180,180,180,0.4)',
                    zeroline=False
                ),
                coloraxis_showscale=False,
                title_font=dict(size=18)
            )
            st.plotly_chart(fig)

        # Animated Bar Plot for population by Country Over Time
        def plot_population_animated():
            fig = px.bar(
                filled_data1,
                x='Country',
                y='Population',
                animation_frame='Year',
                color='Population',
                color_continuous_scale=px.colors.sequential.YlGnBu,
                range_y=[0, 1.6e9],
                title="Population by Country Over Time"
            )
            fig.update_layout(
                height=500,
                plot_bgcolor='#f5f5f5',
                margin=dict(l=50, r=50, t=50, b=50),
                xaxis=dict(showgrid=False),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(180,180,180,0.3)',
                    zeroline=False
                ),
                hovermode='x unified',
                coloraxis_showscale=False,
                title_font=dict(size=18),
                font=dict(size=12)
            )
            st.plotly_chart(fig)
        plot_population_growth(selected_country_pop)
        plot_population_animated()


    #Tab4 Growth Rate
    with tab4:
        st.header("Population Growth Rate (%) Over Time")

        selected_country_rate = st.selectbox("Select Country", countries_pop, key='rate')

        def plot_population_growth_rate(country):
            data = filled_data1[filled_data1['Country'] == country]
            fig = px.line(
                data, x='Year', y='Population Growth Rate (%)',
                title=f'Population Growth Rate in {country}',
                labels={'Population Growth Rate (%)': 'Growth Rate (%)'},
                line_shape='linear', markers=True,
                color_discrete_sequence=['#1f77b4']
            )
            fig.update_layout(
                height=500, plot_bgcolor='#eeeeee', hovermode='x unified',
                margin=dict(l=50, r=50, t=50, b=50), xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(180,180,180,0.4)', zeroline=False),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig)

        plot_population_growth_rate(selected_country_rate)
