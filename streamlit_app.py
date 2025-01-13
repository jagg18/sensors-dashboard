import streamlit as st
import pandas as pd
import math
from pathlib import Path

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Sensor dashboard',
    page_icon=':robot:',
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_sensor_data():
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

    sensor_df = sensor_df.reset_index()

    # Add a 'Date' column
    sensor_df['Date'] = sensor_df['timestamp'].map(lambda x: x.date())

    # sensor_df

    return sensor_df

sensor_df = get_sensor_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :robot_face: Sensors dashboard
'''

# Add some spacing
''
''

min_date = sensor_df['Date'].min()
max_date = sensor_df['Date'].max()

min_date, max_date = st.slider(
    'Select range',
    min_value=min_date,
    max_value=max_date,
    value=[min_date, max_date])

# countries = gdp_df['Country Code'].unique()

# if not len(countries):
#     st.warning("Select at least one country")

# selected_countries = st.multiselect(
#     'Which countries would you like to view?',
#     countries,
#     ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])

''
''
''

# Filter the data
# filtered_gdp_df = gdp_df[
#     (gdp_df['Country Code'].isin(selected_countries))
#     & (gdp_df['Year'] <= to_year)
#     & (from_year <= gdp_df['Year'])
# ]

st.header('Temperature (degC) over time', divider='gray')

''

st.line_chart(
    sensor_df,
    x='Date',
    y='Temperature (degC)',
    color='Room',
)

''
''

st.header('Humidity (rh%) over time', divider='gray')

''

st.line_chart(
    sensor_df,
    x='Date',
    y='Humidity (rh%)',
    color='Room',
)


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
