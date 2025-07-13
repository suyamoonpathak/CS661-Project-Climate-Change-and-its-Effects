import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def run():
    @st.cache_data
    def load_and_process_data():
        loss_data = np.load('LossTRF.npz')
        loss_data = {
                'train_loss': loss_data['train_loss'],
                'val_loss': loss_data['val_loss'],
                'epochs' : np.arange(1, len(loss_data['val_loss']) + 1)
            }
        data = pd.read_csv("climate_disease_dataset.csv")
        df = data.copy()
        df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01')
        df['country'] = df['country'].astype(str) + ' (' + df['region'].astype(str) + ')'

        REGION = np.unique(df.region)
        COUNTRY_NAME = np.unique(df['country'].values)
        dic = {}
        for name in COUNTRY_NAME:
            dic[name] = df[df.country == name].drop(
                ['healthcare_budget', 'population_density', 'country', 'region', 'year'], axis=1)

        for reg in REGION:
            region_df = df[df['region'] == reg]
            numeric_cols = region_df.select_dtypes(include=np.number).columns.tolist()
            agg_cols = [col for col in
                        ['avg_temp_c', 'uv_index', 'air_quality_index', 'precipitation_mm', 'malaria_cases', 'dengue_cases',
                        'month'] if col in numeric_cols]
            dic[reg] = region_df.groupby('date', as_index=False)[agg_cols].mean()
            if 'month' in dic[reg]:
                dic[reg]['month'] = dic[reg]['month'].astype(int)

        df_dict = dic

        MONTHS = {i: name for i, name in enumerate(
            ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Whole Year'], 1)}

        box_df = {}
        for country in df_dict.keys():
            monthly_agg = df_dict[country].groupby('month').agg([
                ('min', 'min'), ('max', 'max'), ('mean', 'mean'), ('median', 'median'),
                ('q25', lambda x: x.quantile(0.25)), ('q75', lambda x: x.quantile(0.75))
            ])
            yearly_agg = df_dict[country].drop(columns=['date', 'month']).groupby(lambda x: True).agg([
                ('min', 'min'), ('max', 'max'), ('mean', 'mean'), ('median', 'median'),
                ('q25', lambda x: x.quantile(0.25)), ('q75', lambda x: x.quantile(0.75))
            ])
            yearly_agg.index = pd.Index([13], name='month')
            combined_df = pd.concat([monthly_agg, yearly_agg])
            combined_df = combined_df.reset_index()
            combined_df['month_name'] = combined_df['month'].apply(lambda x: MONTHS[x])
            box_df[country] = combined_df

        return df_dict, box_df, REGION, COUNTRY_NAME, loss_data

    df_dict, box_df, REGION, COUNTRY_NAME, loss_data = load_and_process_data()

    VARIABLE_LABELS = {
        'avg_temp_c': 'Avg Temp (°C)',
        'uv_index': 'UV Index',
        'air_quality_index': 'Air Quality Index',
        'precipitation_mm': 'Precipitation (mm)',
        'malaria_cases': 'Malaria Cases',
        'dengue_cases': 'Dengue Cases',
    }
    ALL_LOCATIONS = sorted(list(REGION)) + sorted(list(COUNTRY_NAME))
    VARIABLE_NAMES = list(VARIABLE_LABELS.keys())

    def format_location(location):
        if location in REGION:
            return f"{location} (Region)"
        return location

    st.set_page_config(page_title="Climate & Disease Dashboard", layout="wide")
    st.markdown("<h1>Interactive Climate and Disease Plot</h1>",unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<h2>Attribute Comparison</h2>", unsafe_allow_html=True)
        st.markdown(
            "<p>Select one location and up to two variables to visualize them over time.</p>",
            unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            selected_location1 = st.selectbox("Select a Location", options=ALL_LOCATIONS, index=15,
                                            placeholder="Choose a location...", key="loc1", format_func=format_location)
        with col2:
            selected_variables1 = st.multiselect("Select Variables", options=VARIABLE_NAMES,
                                            format_func=lambda x: VARIABLE_LABELS[x], max_selections=2,
                                            placeholder="Choose up to two variables...", key="var1",
                                            default=['avg_temp_c', 'malaria_cases'])

        if not selected_location1 or not selected_variables1:
            st.info("Please select a location and at least one variable to see the chart.")
        else:
            fig1 = make_subplots(specs=[[{"secondary_y": True}]])
            colors = ['#1f77b4', '#ff7f0e']
            val1 = selected_variables1[0]
            fig1.add_trace(go.Scatter(x=df_dict[selected_location1]['date'], y=df_dict[selected_location1][val1],
                                    name=VARIABLE_LABELS[val1], mode='lines+markers', marker=dict(color=colors[0])),
                        secondary_y=False)
            fig1.update_yaxes(title_text=VARIABLE_LABELS[val1], color=colors[0], secondary_y=False, fixedrange=True)

            if len(selected_variables1) == 2:
                val2 = selected_variables1[1]
                fig1.add_trace(go.Scatter(x=df_dict[selected_location1]['date'], y=df_dict[selected_location1][val2],
                                        name=VARIABLE_LABELS[val2], mode='lines+markers', marker=dict(color=colors[1])),
                            secondary_y=True)
                fig1.update_yaxes(title_text=VARIABLE_LABELS[val2], color=colors[1], secondary_y=True, fixedrange=True)

            title_text = f"{' vs. '.join([VARIABLE_LABELS[v] for v in selected_variables1])} in {selected_location1}"
            fig1.update_layout(
                title={'text': title_text, 'x': 0.5, 'xanchor': 'center'},
                template='plotly_white',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig1, use_container_width=True)

    # Plot 2
    with st.container(border=True):
        st.markdown("<h2>Location Comparison</h2>", unsafe_allow_html=True)
        st.markdown(
            "<p>Select one variable and up to four locations to compare them over time.</p>",
            unsafe_allow_html=True)

        col3, col4 = st.columns(2)
        with col3:
            selected_locations2 = st.multiselect("Select Locations", options=ALL_LOCATIONS, max_selections=4,
                                                placeholder="Choose up to four locations...", key="loc2", default = [ALL_LOCATIONS[28], ALL_LOCATIONS[32]],
                                                format_func=format_location)
        with col4:
            selected_variable2 = st.selectbox("Select a Variable", options=VARIABLE_NAMES,
                                            format_func=lambda x: VARIABLE_LABELS[x], index=3,
                                            placeholder="Choose a variable...", key="var2")

        if not selected_locations2 or not selected_variable2:
            st.info("Please select a variable and at least one location to see the chart.")
        else:
            fig2 = go.Figure()
            colors = ["#05adb0", "#edba00", "#4abf01", "#de0147"]
            for i, loc in enumerate(selected_locations2):
                fig2.add_trace(
                    go.Scatter(x=df_dict[loc]['date'], y=df_dict[loc][selected_variable2], name=loc, mode='lines+markers',
                            marker=dict(color=colors[i])))

            title_text = f"Comparing {VARIABLE_LABELS[selected_variable2]} Across Locations"
            fig2.update_layout(
                title={'text': title_text, 'x': 0.5, 'xanchor': 'center'},
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig2.update_yaxes(title_text=VARIABLE_LABELS[selected_variable2], fixedrange=True)
            st.plotly_chart(fig2, use_container_width=True)

    # Polt 3
    with st.container(border=True):
        st.markdown("<h2>Distribution by Month (Box Plot)</h2>", unsafe_allow_html=True)
        st.markdown("<p>Select one variable and one or more locations to compare their monthly distributions.</p>",
            unsafe_allow_html=True)

        col5, col6 = st.columns(2)
        with col5:
            selected_locations3 = st.multiselect("Select Locations", options=ALL_LOCATIONS, max_selections=5,
                                                placeholder="Choose up to five locations...", key="loc3",
                                                format_func=format_location,default = [ALL_LOCATIONS[28], ALL_LOCATIONS[32]])
        with col6:
            selected_variable3 = st.selectbox("Select a Variable", options=VARIABLE_NAMES,
                                            format_func=lambda x: VARIABLE_LABELS[x], index=5,
                                            placeholder="Choose a variable...", key="var3",)

        if not selected_locations3 or not selected_variable3:
            st.info("Please select a variable and at least one location to see the box plot.")
        else:
            fig3 = go.Figure()
            for loc in selected_locations3:
                if loc in box_df and selected_variable3 in box_df[loc].columns.get_level_values(0):
                    temp = box_df[loc][selected_variable3]
                    fig3.add_trace(go.Box(
                        name=loc, x=box_df[loc]['month_name'], q1=temp['q25'],
                        q3=temp['q75'], lowerfence=temp['min'], upperfence=temp['max'],
                        mean=temp['mean'], median=temp['median'], boxmean=True
                    ))

            title_text = f"Monthly Distribution of {VARIABLE_LABELS[selected_variable3]}"
            fig3.update_layout(
                title={'text': title_text, 'x': 0.5, 'xanchor': 'center'},
                yaxis_title=VARIABLE_LABELS[selected_variable3],
                boxmode='group',
                template='plotly_white',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig3, use_container_width=True)

    with st.container(border=True):
        st.markdown("<h2>Model Training & Validation Loss for Transformer Encoder</h2>",
                    unsafe_allow_html=True)
        st.markdown(
            "<p>This chart shows the training and validation loss of the model over epochs.</p>",
            unsafe_allow_html=True)
        colors = ['#1f77b4', '#ff7f0e']
        train_loss = loss_data['train_loss']
        val_loss = loss_data['val_loss']
        epochs = loss_data['epochs']

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=epochs, y=train_loss, mode='lines+markers', name='Training Loss',marker=dict(color=colors[0])))
        fig4.add_trace(go.Scatter(x=epochs, y=val_loss, mode='lines+markers', name='Validation Loss',marker=dict(color=colors[1])))
        fig4.update_yaxes(fixedrange=True)
        fig4.update_layout(
            title={'text': 'Model Loss per Epoch', 'x': 0.5, 'xanchor': 'center'},
            xaxis_title='Epoch',
            yaxis_title='Loss',
            xaxis_range=[-0.2,40.2],
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig4, use_container_width=True)