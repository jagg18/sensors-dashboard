import streamlit as st
import pandas as pd
import datetime as dt
import math
from pathlib import Path
import re

import altair as alt

# Set the page configuration
st.set_page_config(page_title='Sensor Dashboard', page_icon=':robot:')

'''
# :robot_face: Sensor Dashboard
'''

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
                                #  names=['date', 'temperature_degc', 'humidity_rh'],
                                 )
                
                # Function to clean column names
                def clean_column_name(column_name):
                    # Remove "Room", "room", and trailing numbers, and clean up extra spaces
                    cleaned_name = re.sub(r'\b[Rr]oom\s*\d*\b', '', column_name)
                    return re.sub(r'\s+', ' ', cleaned_name).strip()

                # Apply the function to all column names
                df.columns = [clean_column_name(col) for col in df.columns]
                
                # Rename the first column to 'date'
                df.rename(columns={df.columns[0]: 'date'}, inplace=True)

                # Convert the 'date' column to datetime
                df['date'] = pd.to_datetime(df['date'])

                # Insert 'room' as the second column
                df.insert(1, 'room', room_name)

                df = df.groupby(['room', pd.Grouper(key='date', freq='1D')]).mean().reset_index()
                df['date'] = df['date'].map(lambda x: x.date())

                combined_data.append(df)
            except Exception as e:
                st.error(f"Error processing {file_name}: {e}")
        else:
            st.warning(f"Room name for {file_name} is empty.")
    return pd.concat(combined_data, ignore_index=True) if combined_data else pd.DataFrame()

# File uploader
with st.sidebar:
    with st.expander("File upload", expanded=True):
        uploaded_files = st.file_uploader("Upload sensor files", type=['csv'], accept_multiple_files=True)

        # Display uploaded files and room name inputs
        if uploaded_files:
            for uploaded_file in uploaded_files:
                col1, col2, _ = st.columns(3)
                with col1:
                    # Room name input
                    room_name = st.text_input(f'Room Name:', key=f"room_{uploaded_file.name}")
                with col2:
                    st.text(uploaded_file.name)
                
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

# Utility functions

def get_max_param(group, param):
    return group.loc[group[param].idxmax()]

def get_min_param(group, param):
    return group.loc[group[param].idxmin()]

def render_metrics(param, vals, header_string):
    st.header(header_string, divider='gray')
    cols = st.columns(len(vals))
    for i, col in enumerate(cols):
        with col:
            st.metric(
                label=vals.iloc[i]['room'],
                value=f"{round(vals.iloc[i][param], 2)}",
                delta=None, delta_color="normal", label_visibility="visible", border=True)
            st.text(vals.iloc[i]['date'])

# Function to render a chart
def render_chart(y_field, title, divider, date_range):
    st.header(title, divider=divider)
    interval = alt.selection_interval(encodings=['x'], value={'x': date_range})
    selection = alt.selection_point(fields=['room'], bind='legend')
    highlight = alt.selection_point(
        on="pointerover", fields=['date'], nearest=True, clear="pointerout"
    )

    base = alt.Chart(df_non_null, width=600, height=200).mark_line().encode(
        x='date:T',
        y=f'{y_field}:Q',
        color='room',
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
    ).add_params(selection)

    upper = base.encode(
        alt.X('date:T').scale(domain=interval),
        alt.Y(f'{y_field}:Q').scale(zero=False),
    )

    circle = upper.mark_circle().encode(
        size=alt.condition(highlight, alt.value(100), alt.value(0), empty=False)
    ).add_params(highlight)

    view = base.encode(
        alt.Y(f'{y_field}:Q').scale(zero=False),
    ).properties(height=60).add_params(interval)

    st.altair_chart((upper + circle) & view, use_container_width=True)

if not sensor_df.empty:
    # st.dataframe(sensor_df)

    min_date = sensor_df['date'].min()
    max_date = sensor_df['date'].max()

    # Date slider
    with st.sidebar:
        min_date, max_date = st.slider(
            'Select Date Range',
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date)
        )

    # Room selection
    rooms = sensor_df['room'].unique()
    with st.sidebar:
        selected_rooms = st.multiselect('Select Rooms', rooms, default=rooms)

    # Filter data based on selections
    filtered_sensor_df = sensor_df[
        (sensor_df['room'].isin(selected_rooms)) &
        (sensor_df['date'] >= min_date) &
        (sensor_df['date'] <= max_date)
    ]

    # Interval Default Range
    start_date = max_date - \
        pd.offsets.DateOffset(months=1)
    date_range = (start_date.date(), max_date)

    ''

    # Params selection
    params = sensor_df.columns.unique()

    with st.sidebar:
        selected_params = st.multiselect('Select Parameters', params[2:], default=[params[2], params[3]])

    for param in selected_params:
        # Remove rows with null values
        df_non_null = filtered_sensor_df.dropna(subset=[param])

        render_chart(param, f"{param} over time", divider="gray", date_range=date_range)

        # Metrics

        max_temperatures = df_non_null.groupby('room').apply(lambda df: get_max_param(df, param))
        min_temperatures = df_non_null.groupby('room').apply(lambda df: get_min_param(df, param))

        render_metrics(param, max_temperatures, f'All-Time High - {param}')
        render_metrics(param, min_temperatures, f'All-Time Low - {param}')
else:
    '''
    Upload your files and click **Process Files** to generate plots.
    '''