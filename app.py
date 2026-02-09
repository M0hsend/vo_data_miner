import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import TimestampedGeoJson


st.set_page_config(layout="wide", page_title="VahidOnline Data Analysis")

def add_legend(m):
    legend_html = '''
    <div style="position: fixed; 
                bottom: 80px; right: 20px; width: 140px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:12px;
                padding: 10px; border-radius: 5px; opacity: 0.8;">
        <b>Legend</b><br>
        <i class="fa fa-circle" style="color:green"></i>&nbsp; No Chant<br>
        <i class="fa fa-circle" style="color:blue"></i>&nbsp; 1 Economy<br>
        <i class="fa fa-circle" style="color:red"></i>&nbsp; 2 Anti-regime<br>
        <i class="fa fa-circle" style="color:magenta"></i>&nbsp; 3 Promonarchy<br>
        <i class="fa fa-circle" style="color:orange"></i>&nbsp; Mixed Cases
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    return m


@st.cache_data
def load_and_clean_data(file_path):
    # Load and drop empty addresses
    df = pd.read_excel(file_path)
    df = df.dropna(subset=['address']).copy()
    df['date_utc'] = pd.to_datetime(df['date_utc'], utc=True)
    # df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('date_utc')

    # Assuming coordinates were saved in previous geocoding step
    # If not, you'd run the geocoder here
    df = df.dropna(subset=['latitude', 'longitude'])
    return df

# --- 2. MAP GENERATION ---
def create_map(df):
    # colors = ["green", "blue", "purple", "navy", "magenta", "yellow", "red", "tomato", "pink"]
    colors = ["green", "blue", "red", "magenta", "orange"]
    # Center on the first point or Tehran
    start_loc = [df.iloc[0]['latitude'], df.iloc[0]['longitude']] if not df.empty else [35.6892, 51.3890]
    m = folium.Map(location=start_loc, zoom_start=6, tiles="cartodbpositron")

    features = []
    for _, row in df.iterrows():
        labels = str(row['Label'])
        chant_labels = ['1','2','3']
        violence_labels = ['4','5','6','7','8']
        if any(char in labels for char in chant_labels):
            if len(labels) == 1:
                c_ind = int(labels)
            else:
                c_ind = 4
        else:
            c_ind = 0

        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [row['longitude'], row['latitude']],
            },
            'properties': {
                'time': row['date_utc'].strftime('%Y-%m-%dT%H:%M:%S'),
                'popup': f"<b>{row['id']}</b><br>{row['address']}",
                'id': row['id'],# .name # Useful for clicking,
                "icon": "circle",
                "iconstyle": {
                    "fillColor": colors[c_ind],
                    "fillOpacity": 1.0,
                    "stroke": "true",
                    "radius": 10,
                    "weight": 1
                },
            }
        }
        features.append(feature)

    TimestampedGeoJson(
        {'type': 'FeatureCollection', 'features': features},
        period='P1D',
        add_last_point=True,
        auto_play=False,
        date_options='YYYY-MM-DD',
    ).add_to(m)

    # Add the Legend
    m = add_legend(m)

    return m

# --- 3. STREAMLIT UI ---
st.title("Mapping the timeline of the Protests in Iran")

# Load data (Replace with your actual filename)
try:
    # data = load_and_clean_data("geocoded_results.xlsx")
    data = load_and_clean_data("final_data.xlsx")

        # --- Intro SECTION (Full Width) ---
    st.divider() # Adds a visual horizontal line
    st.header("Analysis Overview")
    st.write("""
    In late December 2025 - early January 2026 Iran witnessed a [massive uprising](https://en.wikipedia.org/wiki/2025%E2%80%932026_Iranian_protests) across 
    its nation. Ignited initially by high inflation rates, malfunctioning economy and plummeting value of the currency, morphed into a widespread protest 
    against the regime's existence. This was suppressed by brutal force by the government, resulting in tens of thousands of casualties, mostly inflicted 
    during the two days at peak of these protests (8-9 Jan. 2026).
    Since there is no independent journalism allowed in Iran, the main source of news is the stream of
    videos captured by the protestors or by-standers, shared with outside world. One trusted platform that widely shares these videos is 
    [VahidOnline's](https://en.wikipedia.org/wiki/Vahid_Online) Telegram channel. 
    By observing the map on the right, you can see the progression of events 
    across various regions of Iran.
    """)


        # --- Overall look at histogram ---
    st.subheader("Data flow from VafidOnline leading to 9th Jan 2026")
    col_a, col_b = st.columns(2)

    with col_a:
        st.write("Histogram of posted videos on VahidOnline")
        hist_data = data.copy()
        hist_data['date_utc'] = pd.to_datetime(hist_data['date_utc'], utc=True, errors='coerce')
        hist_data['just_date'] = hist_data['date_utc'].dt.date
        date_counts = hist_data['just_date'].value_counts().sort_index()
        st.bar_chart(date_counts)
        st.caption("<p style='text-align: center;'>Date of Video</p>", unsafe_allow_html=True)

    with col_b:
        st.write("""
        In this plot you can see the number of videos shared on VahidOnline platform across the dates specified. 
        Please note that we are ignoring all the non-video contents here. 
        The point at which the government shut down the internet is clear.
        """)

    # You can even use a container to group things
    with st.container():
        st.info("💡 Tip: Use the timeline slider at the bottom of the map to filter by date.")

    col1, col2 = st.columns([1, 2])

    with col2:
        map_obj = create_map(data)
        # We capture the map output to detect clicks
        map_data = st_folium(map_obj, width=800, height=600)

    with col1:
        st.subheader("Slogans chanted in protests mapped over time")
        # Logic to show video if a point is clicked
        if map_data.get("last_object_clicked"):
            # Folium returns [lat, lon], we find matching row
            click_lat = map_data["last_object_clicked"]["lat"]
            selected = data[data['latitude'] == click_lat].iloc[0]

            st.info(f"Selected: {selected['id']}")
            st.write(f"**Address:** {selected['address']}")

            if 'video_url' in selected and pd.notna(selected['video_url']):
                st.video(selected['video_url'])
            else:
                st.warning("No video associated with this point.")
        else:
            st.write("Click a point on the map to see details.")

except Exception as e:
    st.error(f"Please ensure 'final_data.xlsx' exists. Error: {e}")
