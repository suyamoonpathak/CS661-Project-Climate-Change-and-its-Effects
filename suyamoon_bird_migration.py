import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def run():
    # Load and preprocess data
    @st.cache_data
    def load_data():
        df = pd.read_csv("bird_migration_with_country.csv")
        df['date_time'] = pd.to_datetime(df['date_time'], utc=True)
        return df

    st.set_page_config(layout="wide")

    birddata = load_data()

    bird_names = birddata['bird_name'].unique()
    bird_colors = {'Eric': 'red', 'Nico': 'blue', 'Sanne': 'green'}

    st.title("Bird Migration")

    birddata['color'] = birddata['bird_name'].map(bird_colors)
    birddata['Date'] = birddata['date_time'].dt.strftime('%Y-%m-%d')
    birddata['Time'] = birddata['date_time'].dt.strftime('%H:%M:%S')
    birddata['Altitude (m)'] = birddata['altitude'].astype(str) + " m"
    birddata['Speed (m/s)'] = birddata['speed_2d'].round(2).astype(str) + " m/s"

    def direction_arrow(deg):
        if pd.isna(deg):
            return 'N/A'
        arrows = ['↑','↗','→','↘','↓','↙','←','↖']
        idx = int(((deg + 360) % 360 + 22.5) // 45) % 8
        return arrows[idx]

    birddata['Direction Arrow'] = birddata['direction'].apply(direction_arrow)
    birddata['Direction (deg)'] = birddata['direction'].round(1).astype(str) + "°"

    hovertemplate = (
        "<span style='font-size:22px'><b>%{customdata[0]}</b></span><br><br>"
        "<span style='font-size:20px'>Date: <b>%{customdata[1]}</b></span><br><br>"
        "<span style='font-size:20px'>Time: <b>%{customdata[2]}</b> UTC</span><br><br>"
        "<span style='font-size:20px'>Altitude: <b>%{customdata[3]}</b></span><br><br>"
        "<span style='font-size:20px'>Speed: <b>%{customdata[4]}</b></span><br><br>"
        "<span style='font-size:20px'>Direction: "
        "<span style='font-size:32px; color:#c00'>%{customdata[5]}</span> "
        "<span style='font-size:22px'>%{customdata[6]}</span></span><br><br>"
        "<extra></extra>"
    )

    # Prepare data for plots
    birddata['date'] = birddata['date_time'].dt.date
    agg = (
        birddata.groupby(['bird_name', 'date'])
        .agg({
            'speed_2d': 'mean',
            'altitude': 'mean',
            'country': lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]
        })
        .reset_index()
    )
    birddata['hour'] = birddata['date_time'].dt.hour
    hourly_speed = (
        birddata.groupby(['bird_name', 'hour'])['speed_2d']
        .mean()
        .reset_index()
    )
    daily_counts = (
    birddata.groupby(['bird_name', 'date'])
    .agg(
        count=('bird_name', 'size'),
        country=('country', lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0])
    )
    .reset_index()
)


    # --- Tabs ---
    tab1, tab2, tab3 = st.tabs([
        "Trajectory Map",
        "Daily Mean Speed",
        "Hourly Mean Speed"
    ])
    

    with tab1:
        # Compute center of Eric's trajectory for zooming
        eric_data = birddata[birddata['bird_name'] == 'Eric']
        center_lat = eric_data['latitude'].mean()
        center_lon = eric_data['longitude'].mean()

        # Set visibility for birds
        default_visible_map = {'Eric': True, 'Nico': 'legendonly', 'Sanne': 'legendonly'}

        # Original Trajectory Plot
        st.subheader("Standard Bird Trajectory")
        fig = go.Figure()

        for bird in bird_names:
            data = birddata[birddata['bird_name'] == bird]
            fig.add_trace(go.Scattermapbox(
                lat=data['latitude'],
                lon=data['longitude'],
                mode='markers+lines',
                marker=dict(size=4, color=bird_colors[bird]),
                line=dict(width=2, color=bird_colors[bird]),
                name=bird,
                visible=default_visible_map[bird],
                customdata=np.stack([
                    data['bird_name'],
                    data['Date'],
                    data['Time'],
                    data['Altitude (m)'],
                    data['Speed (m/s)'],
                    data['Direction Arrow'],
                    data['Direction (deg)']
                ], axis=-1),
                hovertemplate=hovertemplate
            ))

        fig.update_layout(
            mapbox_style="carto-positron",
            mapbox=dict(
                center=dict(lat=center_lat, lon=center_lon),
                zoom=3
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            font=dict(size=20),
            legend=dict(
                x=0.01, y=0.99,
                bgcolor='black',
                bordercolor='black',
                borderwidth=1,
                font=dict(size=16),
                orientation='h',
                xanchor='left',
                yanchor='top'
            )
        )

        st.plotly_chart(fig, use_container_width=True, height=800)
        
        st.markdown("""
        - All birds follow a similar migration corridor: Belgium → France → Spain → Morocco → Senegal → The Gambia.
        - Migration begins mid-August, birds reach West Africa by October, spend the winter there, start returning back in mid-February and reach Belgium by end of April.
        - Coastal flyers: prefer flying along coastlines over inland regions.
        - Eric travels the shortest distance.
        - Paths for departure and arrival are different — flexible routing.
        """)


        # Speed Visualization Plot
        st.subheader("Bird Speed Visualization")

        fig_speed = go.Figure()

        for bird in bird_names:
            data = birddata[birddata['bird_name'] == bird]
            fig_speed.add_trace(go.Scattermapbox(
                lat=data['latitude'],
                lon=data['longitude'],
                mode='markers',
                marker=dict(
                    size=6,
                    color=data['speed_2d'],
                    colorscale='Turbo',
                    cmin=birddata['speed_2d'].min(),
                    cmax=birddata['speed_2d'].max(),
                    colorbar=dict(
                        title=dict(
                            text="Speed (m/s)",
                            side="right",
                            font=dict(size=16, color="black")
                        ),
                        tickfont=dict(size=14, color="black"),
                        x=0.98,
                        xanchor='right',
                        len=0.75,
                        bgcolor='rgba(255,255,255,0.7)',
                        outlinewidth=1,
                        bordercolor='black',
                        borderwidth=0.5
                    )
                ),
                name=bird,
                visible=default_visible_map[bird],
                customdata=np.stack([
                    data['bird_name'],
                    data['Date'],
                    data['Time'],
                    data['Altitude (m)'],
                    data['Speed (m/s)'],
                    data['Direction Arrow'],
                    data['Direction (deg)']
                ], axis=-1),
                hovertemplate=hovertemplate
            ))

        fig_speed.update_layout(
            mapbox_style="carto-positron",
            mapbox=dict(
                center=dict(lat=center_lat, lon=center_lon),
                zoom=3
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            font=dict(size=20),
            legend=dict(
                x=0.01, y=0.99,
                bgcolor='black',
                bordercolor='black',
                borderwidth=1,
                font=dict(size=16),
                orientation='h',
                xanchor='left',
                yanchor='top'
            )
        )

        st.plotly_chart(fig_speed, use_container_width=True, height=800)
        st.markdown("""
        - Birds have higher speed over the ocean; possibly wind-assisted flight.
        - Speeds dip near start (Belgium) and end points (Senegal/Gambia).
        - Nico and Eric show occasional high-speed bursts (green points); Sanne maintains a steadier pace.
        - Noticeable slow-down around African coast — possibly due to feeding or resting behavior.
        """)


        # Altitude Visualization Plot
        st.subheader("Bird Altitude Visualization")

        fig_altitude = go.Figure()

        for bird in bird_names:
            data = birddata[birddata['bird_name'] == bird]
            fig_altitude.add_trace(go.Scattermapbox(
                lat=data['latitude'],
                lon=data['longitude'],
                mode='markers',
                marker=dict(
                    size=6,
                    color=data['altitude'],
                    colorscale='Turbo',
                    cmin=birddata['altitude'].min(),
                    cmax=birddata['altitude'].max(),
                    colorbar=dict(
                        title=dict(
                            text="Altitude (m)",
                            side="right",
                            font=dict(size=16, color="black")
                        ),
                        tickfont=dict(size=14, color="black"),
                        x=0.98,
                        xanchor='right',
                        len=0.75,
                        bgcolor='rgba(255,255,255,0.7)',
                        outlinewidth=1,
                        bordercolor='black',
                        borderwidth=0.5
                    )
                ),
                name=bird,
                visible=default_visible_map[bird],
                customdata=np.stack([
                    data['bird_name'],
                    data['Date'],
                    data['Time'],
                    data['Altitude (m)'],
                    data['Speed (m/s)'],
                    data['Direction Arrow'],
                    data['Direction (deg)']
                ], axis=-1),
                hovertemplate=hovertemplate
            ))

        fig_altitude.update_layout(
            mapbox_style="white-bg",
            mapbox=dict(
                center=dict(lat=center_lat, lon=center_lon),
                zoom=3,
                layers=[
                    {
                        "below": 'traces',
                        "sourcetype": "raster",
                        "sourceattribution": "United States Geological Survey",
                        "source": [
                            "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"

                        ]
                    }
                ]
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            font=dict(size=20),
            legend=dict(
                x=0.01, y=0.99,
                bgcolor='black',
                bordercolor='black',
                borderwidth=1,
                font=dict(size=16),
                orientation='h',
                xanchor='left',
                yanchor='top'
            )
        )



        st.plotly_chart(fig_altitude, use_container_width=True, height=800)
        st.markdown("""
        - Altitude and speed show weak correlation — both are low together, but not consistently high together.
        - Birds maintain low altitude along the African coast (cause mostly its desert).
        - Altitudes increases near hilly regions — e.g., Portugal, Spain, and parts of France.
        """)

    with tab2:
        st.header("Daily Mean Speed")
        default_visible = [True, 'legendonly', 'legendonly']
        fig = go.Figure()
        for idx, bird in enumerate(['Eric', 'Nico', 'Sanne']):
            df = agg[agg['bird_name'] == bird]
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['speed_2d'],
                mode='lines+markers',
                name=bird,
                line=dict(color=bird_colors[bird], width=3),
                marker=dict(size=10),
                visible=default_visible[idx],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Mean Speed: %{y:.2f} m/s<br>"
                    "Mean Altitude: %{customdata[0]:.1f} m<br>"
                    "Country: %{customdata[1]}<extra></extra>"
                ),
                text=[bird]*len(df),
                customdata=df[['altitude', 'country']].values
            ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Mean Speed (m/s)",
            yaxis=dict(
                range=[0, 11],   
                autorange=False  
            ),
            font=dict(size=18),
            legend=dict(
                x=0.01, y=0.99, bgcolor='black', bordercolor='black', borderwidth=1,
                font=dict(size=16), orientation='h', xanchor='left', yanchor='top'
            ),
            margin={"r":0,"t":30,"l":0,"b":0},
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True, height=600)
        st.markdown("""
        - Birds fly **faster over the ocean** compared to land.
        - To detect country: \n
        &nbsp;&nbsp;&nbsp;&nbsp;- Reverse geocoding was slow (~17 hrs for 62k rows).  
        &nbsp;&nbsp;&nbsp;&nbsp;- So, used **spatial join** with shapefiles of known countries from trajectory.  
        &nbsp;&nbsp;&nbsp;&nbsp;- Points outside polygons were labeled as **Ocean**.
        - **Sanne** shows more frequent speed fluctuations than Eric and Nico.
        """)


    with tab3:
        st.header("Average Speed by Hour of Day")
        default_visible_hourly_speed = [True, 'legendonly', 'legendonly']
        fig = go.Figure()

        for idx, bird in enumerate(['Eric', 'Nico', 'Sanne']):
            df = hourly_speed[hourly_speed['bird_name'] == bird]
            fig.add_trace(go.Scatter(
                x=df['hour'],
                y=df['speed_2d'],
                mode='lines+markers',
                name=bird,
                line=dict(color=bird_colors[bird], width=3),
                marker=dict(size=10),
                visible=default_visible_hourly_speed[idx]
            ))

        time_blocks = [
            {"start": 0,  "end": 5,  "color": "rgba(0, 0, 100, 0.1)", "label": "Night"},
            {"start": 5,  "end": 10, "color": "rgba(53, 81, 92, 1)", "label": "Morning"},
            {"start": 10, "end": 15, "color": "rgba(255, 165, 0, 1)", "label": "Day"},
            {"start": 15, "end": 20, "color": "rgba(53, 81, 92, 1)", "label": "Evening"},
            {"start": 20, "end": 24, "color": "rgba(0, 0, 100, 0.1)", "label": "Night"},
        ]

        shapes = []
        for block in time_blocks:
            shapes.append(
                dict(
                    type="rect",
                    xref="x",
                    yref="paper",
                    x0=block["start"],
                    x1=block["end"],
                    y0=0,
                    y1=1,
                    fillcolor=block["color"],
                    layer="below",
                    line_width=0,
                )
            )

        fig.update_layout(
            xaxis_title="Hour (UTC)",
            yaxis_title="Average Speed (m/s)",
            yaxis=dict(
                range=[0, 4], 
                autorange=False  
            ),
            template='plotly_white',
            font=dict(size=18),
            legend=dict(
                x=0.01, y=0.99, bgcolor='black', bordercolor='black', borderwidth=1,
                font=dict(size=16), orientation='h', xanchor='left', yanchor='top'
            ),
            margin={"r":0,"t":30,"l":0,"b":0},
            hovermode="x unified",
            shapes=shapes
        )

        st.plotly_chart(fig, use_container_width=True, height=500)
        st.markdown("""
        - Timeline divided into blocks: **Night, Morning, Day, Evening, Night** (with background colors).
        - Birds begin accelerating **early morning (around 2–3 AM)**.
        - **First speed peak at ~7 AM**, dip during noon (heat), **second smaller peak in the evening** (possibly due to fatigue).
        - **Nico is the fastest** overall among the three birds throughout the day.
        """)

        



