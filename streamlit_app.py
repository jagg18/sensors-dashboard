import streamlit as st
import pandas as pd
import datetime as dt
import re

import altair as alt

# Set the page configuration
st.set_page_config(page_title='Air Quality Sensor Dashboard', page_icon=':robot:')

'''
# :robot_face: Air Quality Sensor Dashboard
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

def render_metrics(param, vals, header_string, decimal_places):
    st.header(header_string, divider='gray')
    cols = st.columns(len(vals))
    for i, col in enumerate(cols):
        with col:
            st.metric(
                label=vals.iloc[i]['room'],
                value = f"{vals.iloc[i][param]:.{decimal_places}f}",
                delta=None, delta_color="normal", label_visibility="visible", border=True)
            st.text(vals.iloc[i]['date'].date())

# Line Charts
def render_chart(data, label_x, label_y, legend, title, divider, date_range):
    st.header(title, divider=divider)
    interval = alt.selection_interval(encodings=['x'], value={'x': date_range})
    selection = alt.selection_point(fields=[legend], bind='legend')
    highlight = alt.selection_point(
        on="pointerover", fields=[label_x], nearest=True, clear="pointerout"
    )

    base = alt.Chart(data).mark_line().encode(
        x=f'{label_x}:T',
        y=alt.Y(f'{label_y}:Q'),
        color=f'{legend}:N',
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
    ).properties(
        width=600,
        height=200
    ).add_params(selection)

    upper = base.encode(
        alt.X(f'{label_x}:T').scale(domain=interval),
        alt.Y(f'{label_y}:Q').scale(zero=False),
    )

    circle = upper.mark_circle().encode(
        size=alt.condition(highlight, alt.value(100), alt.value(0), empty=False)
    ).add_params(highlight)

    view = base.encode(
        alt.Y(f'{label_y}:Q').scale(zero=False),
    ).properties(height=60).add_params(interval)

    st.altair_chart((upper + circle) & view, use_container_width=True)

# Define seasons and adjust year for Winter
def get_season_and_adjusted_year(date):
    month = date.month
    year = date.year
    if month == 12:  # December belongs to the next year's Winter
        return 'Winter', year + 1
    elif month in [1, 2]:
        return 'Winter', year
    elif month in [3, 4, 5]:
        return 'Spring', year
    elif month in [6, 7, 8]:
        return 'Summer', year
    elif month in [9, 10, 11]:
        return 'Fall', year

def render_seasonal_data(data, param_name):
    data[['season', 'adjusted_year']] = data['date'].apply(
        get_season_and_adjusted_year
    ).apply(pd.Series)

    # Group by adjusted_year and season to calculate the mean
    grouped = chart_data.groupby(['adjusted_year', 'season']).agg(
        avg_param=(LABEL_Y, 'mean')
    ).reset_index()

    # Round the avg_param column
    grouped['avg_param'] = grouped['avg_param'].round(get_decimal_places(data_decimal_places, param_name))

    bar_chart = alt.Chart(grouped).mark_bar(size=40).encode(
        x=alt.X(
            'season:N', 
            sort=['Winter', 'Spring', 'Summer', 'Fall'],
            title='Season'
        ),
        y=alt.Y(
            'avg_param:Q', 
            title=f'Average {param_name}'
        ),
        color='season:N',
        tooltip=[
            alt.Tooltip('season:N', title='Season'),
            alt.Tooltip('adjusted_year:N', title='Year'),
            alt.Tooltip('avg_param:Q', title=f'Average {param_name}')
        ],
        facet=alt.Facet(
            'adjusted_year:N', 
            title='Year',
            columns=1
        )
    ).properties(
        title=f'Average {param_name} by Season and Year',
        width=500,
        height=200
    )

    st.altair_chart(bar_chart, use_container_width=False)

def get_decimal_places(data_decimal_places, col_name):
    """
    Returns the format string for a given column name based on decimal places.

    Parameters:
        data_decimal_places (dict): A dictionary with column name keys and decimal places as values.
        col_name (str): The name of the column to check.

    Returns:
        str: The format string for the column, or None if the column doesn't match.
    """
    for key, decimal_places in data_decimal_places.items():
        if col_name.lower().startswith(key):
            return decimal_places
    return 4

data_decimal_places = {
    "temperature": 1,
    "humidity": 0,
    "voc": 1,
    "co2": 0,
    "pm": 0,
    "mass concentration": 1,
}

if not sensor_df.empty:
    # st.dataframe(sensor_df)

    min_max_date = (sensor_df['date'].min(), sensor_df['date'].max())

    # Date slider
    with st.sidebar:
        min_date, max_date = st.slider(
            'Select Date Range',
            min_value=min_max_date[0].date(),
            max_value=min_max_date[1].date(),
            value=(min_max_date[0].date(), min_max_date[1].date())
        )

    # Room selection
    rooms = sensor_df['room'].unique()
    with st.sidebar:
        selected_rooms = st.multiselect('Select Rooms', rooms, default=rooms)

    # Filter data based on selections
    filtered_sensor_df = sensor_df[
        (sensor_df['room'].isin(selected_rooms))
        & (sensor_df['date'].dt.date >= min_date)
        & (sensor_df['date'].dt.date <= max_date)
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

        # Rename columns to avoid using special characters in Altair charts
        # CONSTANTS
        LABEL_X = 'date'
        LABEL_Y = 'value'
        LABEL_LEGEND = 'room'
        chart_data = df_non_null[[LABEL_X, LABEL_LEGEND, param]].rename(columns={LABEL_X: LABEL_X, LABEL_LEGEND: LABEL_LEGEND, param: LABEL_Y})

        # Round off the data values
        chart_data[LABEL_Y] = chart_data[LABEL_Y].round(get_decimal_places(data_decimal_places, param))
        
        render_chart(chart_data, label_x=LABEL_X, label_y=LABEL_Y, legend=LABEL_LEGEND, title=f"{param} over time", divider="gray", date_range=date_range)

        # All-Time Metrics

        max_params = chart_data.groupby('room').apply(lambda df: get_max_param(df, LABEL_Y))
        # max_params[LABEL_Y] = max_params[LABEL_Y].astype(str)
        min_params = chart_data.groupby('room').apply(lambda df: get_min_param(df, LABEL_Y))
        # min_params[LABEL_Y] = max_params[LABEL_Y].astype(str)

        render_metrics(LABEL_Y, max_params, f'All-Time High - {param}', get_decimal_places(data_decimal_places, param))
        render_metrics(LABEL_Y, min_params, f'All-Time Low - {param}', get_decimal_places(data_decimal_places, param))

        # Seasonal Metrics

        render_seasonal_data(chart_data, param)

else:
    '''
    Upload your files and click **Process Files** to generate plots.
    '''