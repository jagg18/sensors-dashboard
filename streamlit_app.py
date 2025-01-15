import streamlit as st
import pandas as pd
import datetime as dt
import math
from pathlib import Path

import altair as alt

# Set the page configuration
st.set_page_config(page_title='Sensor Dashboard', page_icon=':robot:')

# Initialize session state for uploaded files and processed data
if 'file_room_pairs' not in st.session_state:
    st.session_state.file_room_pairs = {}
if 'sensor_df' not in st.session_state:
    st.session_state.sensor_df = pd.DataFrame()

# Function to process uploaded files
def process_uploaded_files(file_room_pairs):
    combined_data = []
    for file_name, (file_obj, room_name) in file_room_pairs.items():
        if room_name:
            try:
                # Read and process the CSV file
                df = pd.read_csv(file_obj,
                                 names=['date', 'temperature_degc', 'humidity_rh'],
                                 header=0)
                df['date'] = pd.to_datetime(df['date'])
                df['room'] = room_name
                df = df.groupby(['room', pd.Grouper(key='date', freq='1D')]).mean().reset_index()
                df['date'] = df['date'].map(lambda x: x.date())

                combined_data.append(df)
            except Exception as e:
                st.error(f"Error processing {file_name}: {e}")
        else:
            st.warning(f"Room name for {file_name} is empty.")
    return pd.concat(combined_data, ignore_index=True) if combined_data else pd.DataFrame()

# File uploader
uploaded_files = st.file_uploader("Upload Sensor Files", type=['csv'], accept_multiple_files=True)

# Display uploaded files and room name inputs
if uploaded_files:
    for uploaded_file in uploaded_files:
        col1, col2, col3 = st.columns(3)
        with col1:
            # Room name input
            room_name = st.text_input(f'Room Name for {uploaded_file.name}', key=f"room_{uploaded_file.name}")
        # with col2:
        #     st.text(uploaded_file.name)
        
        # Store file and room name in session state
        st.session_state.file_room_pairs[uploaded_file.name] = (uploaded_file, room_name)

# Process files if a button is clicked
if st.button("Process Files"):
    st.session_state.sensor_df = process_uploaded_files(st.session_state.file_room_pairs)
    if not st.session_state.sensor_df.empty:
        st.success("Files processed successfully!")
    else:
        st.warning("No valid data was processed.")

# Use the processed DataFrame for visualization
sensor_df = st.session_state.sensor_df

# Visualization
if not sensor_df.empty:
    min_date = sensor_df['date'].min()
    max_date = sensor_df['date'].max()

    # Date slider
    min_date, max_date = st.slider(
        'Select Date Range',
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date)
    )

    # Room selection
    rooms = sensor_df['room'].unique()
    selected_rooms = st.multiselect('Select Rooms', rooms, default=rooms)

    # Filter data based on selections
    filtered_sensor_df = sensor_df[
        (sensor_df['room'].isin(selected_rooms)) &
        (sensor_df['date'] >= min_date) &
        (sensor_df['date'] <= max_date)
    ]

    # Charts
    st.header('Temperature (degC) over time', divider='gray')
    
    # Interval Default Range
    start_date = max_date - \
        pd.offsets.DateOffset(months=1)
    date_range = (start_date.date(), max_date)

    # Params
    interval = alt.selection_interval(encodings=['x'],
                                value={'x': date_range})
    selection = alt.selection_point(fields=['room'], bind='legend')
    highlight = alt.selection_point(
        on="pointerover", fields=['date'], nearest=True, clear="pointerout"
    )

    base = alt.Chart(filtered_sensor_df, width=600, height=200) \
            .mark_line().encode(
                x='date:T',
                y='temperature_degc:Q',
                color='room',
                opacity=alt.when(selection).then(alt.value(1)).otherwise(alt.value(0.2)),
            ).add_params(selection)
    upper = base.encode(
        alt.X('date:T').scale(domain=interval),
        alt.Y("temperature_degc:Q").scale(zero=False),
    )

    circle = upper.mark_circle().encode(
        size=alt.condition(highlight, alt.value(100), alt.value(0), empty=False)
    ).add_params(highlight)

    view = base.encode(
        alt.Y("temperature_degc:Q").scale(zero=False),
    ).properties(height=60).add_params(interval)

    (upper + circle) & view

    # Humidity
    st.header('Humidity (rh%) over time', divider='gray')
    (upper.encode(alt.Y("humidity_rh:Q").scale(zero=False)) + \
    circle.encode(alt.Y("humidity_rh:Q").scale(zero=False))) & \
    view.encode(alt.Y("humidity_rh:Q").scale(zero=False))


# first_year = gdp_df[gdp_df['Year'] == from_year]
# last_year = gdp_df[gdp_df['Year'] == to_year]

# st.header(f'GDP in {to_year}', divider='gray')

# ''

# cols = st.columns(4)

# for i, country in enumerate(selected_countries):
#     col = cols[i % len(cols)]

#     with col:
#         first_gdp = first_year[first_year['Country Code'] == country]['GDP'].iat[0] / 1000000000
#         last_gdp = last_year[last_year['Country Code'] == country]['GDP'].iat[0] / 1000000000

#         if math.isnan(first_gdp):
#             growth = 'n/a'
#             delta_color = 'off'
#         else:
#             growth = f'{last_gdp / first_gdp:,.2f}x'
#             delta_color = 'normal'

#         st.metric(
#             label=f'{country} GDP',
#             value=f'{last_gdp:,.0f}B',
#             delta=growth,
#             delta_color=delta_color
#         )
