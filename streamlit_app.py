import streamlit as st
import pandas as pd
import datetime as dt
import math
from pathlib import Path

import altair as alt

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Sensor dashboard',
    page_icon=':robot:',
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_sensor_data_temp():
    """Grab sensor data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """
    DATA_ROOM_1 = Path(__file__).parent/'data/Room_1305-Aug.csv'
    raw_sensor_df1 = pd.read_csv(DATA_ROOM_1)
    raw_sensor_df1['Room'] = 'Room 1305'

    DATA_ROOM_2 = Path(__file__).parent/'data/Room_1401-Aug.csv'
    raw_sensor_df2 = pd.read_csv(DATA_ROOM_2)
    raw_sensor_df2['Room'] = 'Room 1401'

    DATA_ROOM_3 = Path(__file__).parent/'data/Room_2208-Aug.csv'
    raw_sensor_df3 = pd.read_csv(DATA_ROOM_3)
    raw_sensor_df3['Room'] = 'Room 2208'

    sensor_df = pd.concat([raw_sensor_df1, raw_sensor_df2, raw_sensor_df3])

    # Ensure timestamps are in datetime format
    sensor_df['timestamp'] = pd.to_datetime(sensor_df['DateTime'])
    sensor_df = sensor_df.groupby([
                    pd.Grouper(key='Room'),
                    pd.Grouper(key='timestamp', axis=0, freq='1D', sort=True),
                ]).mean(numeric_only=True)
    sensor_df = sensor_df.round(4)

    sensor_df = sensor_df.reset_index()

    # Add a 'Date' column
    sensor_df['Date'] = sensor_df['timestamp'].map(lambda x: x.date())

    return sensor_df

@st.cache_data
def get_sensor_data(csv_file):
    sensor_df = pd.read_csv(csv_file,
                            names=['date', 'temperature_degc', 'humidity_rh'],
                            header=0
                            )

    # Ensure timestamps are in datetime format
    sensor_df['date'] = pd.to_datetime(sensor_df['date'])

    # Set room name
    sensor_df['room'] = 'Room 2208'

    # Group data per day using mean
    sensor_df = sensor_df.groupby([
                    pd.Grouper(key='room'),
                    pd.Grouper(key='date', axis=0, freq='1D', sort=True),
                ]).mean(numeric_only=True)
    
    # Round values up to 4 decimal places
    sensor_df = sensor_df.round(4)

    # Reset the index added by the groupby
    sensor_df = sensor_df.reset_index()

    # Extract just the date component of the timestamp
    sensor_df['date'] = sensor_df['date'].map(lambda x: x.date())

    return sensor_df
    
# -----------------------------------------------------------------------------

'''
# :robot_face: Sensors dashboard
'''

''
''

sensor_df = pd.DataFrame()

# Upload CSV for visualization
uploaded_files = st.file_uploader(label='', type=['csv'], accept_multiple_files=True, label_visibility="visible")

# Check if any files are uploaded
if uploaded_files:
    # Store file names and room names
    file_room_pairs = {}

    # Iterate through uploaded files
    for uploaded_file in uploaded_files:
        col1, col2 = st.columns(2)
        with col1:
            # Textbox for room name
            room_name = st.text_input(f'Room Name for {uploaded_file.name}', key=uploaded_file.name)
        with col2:
            # Display uploaded file name
            st.text(uploaded_file.name)
        
        # Save the pair (room name is updated when user enters it)
        file_room_pairs[uploaded_file.name] = (uploaded_file, room_name)

    # Process CSV files
    if st.button("Process Files"):
        combined_data = []
        
        for file_name, (file_obj, room_name) in file_room_pairs.items():
            if room_name:
                try:
                    # Read CSV file
                    df = get_sensor_data(file_obj)
                    
                    # Add room name as a new column
                    df['room'] = room_name

                    # df['file_name'] = file_name
                    
                    # Append to combined data
                    combined_data.append(df)
                except Exception as e:
                    st.error(f"Error processing {file_name}: {e}")
            else:
                st.warning(f"Room name for {file_name} is empty.")
        
        # Combine all data into one DataFrame
        if combined_data:
            sensor_df = pd.concat(combined_data, ignore_index=True)
            st.success("Files processed successfully!")
            # st.dataframe(sensor_df)
        else:
            st.warning("No files were processed. Please ensure room names are entered.")

# -----------------------------------------------------------------------------

# sensor_df = get_sensor_data_temp()

if not sensor_df.empty:

    min_date = sensor_df['date'].min()
    max_date = sensor_df['date'].max()

    min_date, max_date = st.slider(
        'Select range',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date])

    rooms = sensor_df['room'].unique()

    selected_rooms = st.multiselect(
        'Select rooms',
        rooms,
        rooms)

    ''
    ''
    ''

    # Filter the data
    filtered_sensor_df = sensor_df[
        (sensor_df['room'].isin(selected_rooms))
        & (sensor_df['date'] <= max_date)
        & (min_date <= sensor_df['date'])
    ]

    st.header('Temperature (degC) over time', divider='gray')

    ''

    start_date = max_date - \
        pd.offsets.DateOffset(months=1)
    date_range = (start_date.date(), max_date)

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
            ).add_params(
                selection
            )

    upper = base.encode(
        alt.X('date:T').scale(domain=interval),
        alt.Y("temperature_degc:Q").scale(zero=False),
    )

    circle = upper.mark_circle().encode(
        size=alt.condition(highlight, alt.value(100), alt.value(0), empty=False)
    ).add_params(
        highlight
    )

    view = base.encode(
        alt.Y("temperature_degc:Q").scale(zero=False),
    ).properties(
        height=60
    ).add_params(interval)

    (upper + circle) & view

    ''
    ''

    st.header('Humidity (rh%) over time', divider='gray')

    ''

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
