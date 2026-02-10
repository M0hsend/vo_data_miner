import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import TimestampedGeoJson
import numpy as np

# --- 1. CONFIG & SETUP ---
st.set_page_config(layout="wide", page_title="VahidOnline Data Analysis")

def add_legend_chants(m):
    legend_html = '''
    <div style="position: fixed; 
                bottom: 80px; right: 20px; width: 140px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:12px;
                padding: 10px; border-radius: 5px; opacity: 0.8;">
        <b>Legend</b><br>
        <i class="fa fa-circle" style="color:blue"></i>&nbsp; 1 Economy<br>
        <i class="fa fa-circle" style="color:red"></i>&nbsp; 2 Anti-regime<br>
        <i class="fa fa-circle" style="color:magenta"></i>&nbsp; 3 Pro-monarchy
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    return m
        # '4': "yellow",   
        # '5': "orange",    
        # '6': "orangered",
        # '7': "red",
        # '8': "black", 

def add_legend_violence(m):
    legend_html = '''
    <div style="position: fixed; 
                bottom: 80px; right: 20px; width: 160px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:12px;
                padding: 10px; border-radius: 5px; opacity: 0.9;">
        <b>Violence Legend</b><br>
        <i class="fa fa-circle" style="color:yellow"></i>&nbsp; 4 Tear gas<br>
        <i class="fa fa-circle" style="color:orange"></i>&nbsp; 5 Cold weapon<br>
        <i class="fa fa-circle" style="color:orangered"></i>&nbsp; 6 Shotgun<br>
        <i class="fa fa-circle" style="color:red"></i>&nbsp; 7 Assault weapon<br>
        <i class="fa fa-circle" style="color:black"></i>&nbsp; 8 Protestor violence
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
    # df = df.dropna(subset=['latitude', 'longitude'])
    return df

# def get_combination(label_val):
#     label_str = str(label_val)
#     # Extract only target characters that are present in the string
#     found = [char for char in label_str if char in target_labels]
#     # Sort them so '21' and '12' are treated the same, then join with '+'
#     return "+".join(sorted(found)) if found else None

# --- 2. MAP GENERATION ---
def create_map(df):
    # colors = ["green", "blue", "purple", "navy", "magenta", "yellow", "red", "tomato", "pink"]
    # Mapping of label string to specific color
    color_map = {
        # '0': "green",   # No Chant
        '1': "blue",    # Economy
        '2': "red",     # Anti-regime
        '3': "magenta", # Promonarchy
    }
    # colors = ["green", "blue", "red", "magenta", "orange"]
    # Center on the first point or Tehran
    start_loc = [df.iloc[0]['latitude'], df.iloc[0]['longitude']] if not df.empty else [35.6892, 51.3890]
    m = folium.Map(location=start_loc, zoom_start=6, tiles="cartodbpositron")
    counter = 0
    features = []
    for _, row in df.iterrows():
        # To avoid overlapping points

        seed = int(str(row['id'])[-6:]) # Use last 6 digits of ID as a seed
        np.random.seed(seed) 

        # Apply a tiny offset (approx 5-15 meters)
        offset = 0.015
        lat_jitter = row['latitude'] + np.random.uniform(-1 * offset, offset)
        lon_jitter = row['longitude'] + np.random.uniform(-1 * offset, offset)

        # Reset seed to avoid affecting other parts of the app
        np.random.seed(None)

        # --- Enhanced Mixed Label Logic ---

        labels = str(row['Label'])
        chant_labels = ['1','2','3']
        is_chant = any(char in labels for char in chant_labels)
        if not is_chant:
            continue  # Skip this row entirely; it won't be drawn on the map
        else:
            counter +=1
            # Check for Chants (1, 2, 3)
            chants_found = [c for c in labels if c in ['1', '2', '3']]

            if len(chants_found) == 1:
                # Single Case: Same color for both
                fill_color = color_map[chants_found[0]]
                edge_color = color_map[chants_found[0]]
            elif len(chants_found) >= 2:
                # Mixed Case: Edge is first chant, Fill is second chant
                edge_color = color_map[chants_found[0]]
                fill_color = color_map[chants_found[1]]
            elif '0' not in labels:
                pass

            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    # 'coordinates': [row['longitude'], row['latitude']],
                    'coordinates': [lon_jitter, lat_jitter],
                },
                'properties': {
                    'time': row['date_utc'].strftime('%Y-%m-%dT%H:%M:%S'),
                    'popup': f"<b>{row['id']}</b><br>{row['address']}",
                    'id': row['id'],# .name # Useful for clicking,
                    "icon": "circle",
                    "iconstyle": {
                        "fillColor": fill_color,
                        "fillOpacity": 1,
                        "color": edge_color,  # This defines the edge color
                        "stroke": "true",
                        "radius": 10,
                        "weight": 4           # Thicker weight makes the edge color visible
                    },
                }
            }
            features.append(feature)
    print(f"Total number mapped: {counter}")

    TimestampedGeoJson(
        {'type': 'FeatureCollection', 'features': features},
        period='P1D',
        add_last_point=True,
        auto_play=False,
        date_options='YYYY-MM-DD',
    ).add_to(m)

    # Add the Legend
    # m = add_legend_chants(m)

    return m

def create_violence_timeline_map(df):
    # 1. Filter for labels 4 through 8
    violence_pattern = '[45678]'
    v_df = data[data['Label'].astype(str).str.contains(violence_pattern)].copy()

    # 2. Setup map centered on Iran
    m = folium.Map(location=[32.4279, 53.6880], zoom_start=5, tiles="cartodbpositron")
    color_map = {
        '4': "yellow",   
        '5': "orange",    
        '6': "orangered",
        '7': "red",
        '8': "black", 
    }
    features = []
    for _, row in v_df.iterrows():
        # Use deterministic jitter for the second map as well
        seed = int(str(row['id'])[-6:])
        np.random.seed(seed)
        offset = 0.015
        lat_jitter = row['latitude'] + np.random.uniform(-1 * offset, offset)
        lon_jitter = row['longitude'] + np.random.uniform(-1 * offset, offset)
        np.random.seed(None)

        labels = str(row['Label'])
        viol_labels = ['4','5','6', '7', '8']
        is_viol = any(char in labels for char in viol_labels)
        if not is_viol:
            continue  # Skip this row entirely; it won't be drawn on the map
        else:
            # counter +=1
            # Check for Chants (1, 2, 3)
            viol_found = [c for c in labels if c in viol_labels]

            if len(viol_found) == 1:
                # Single Case: Same color for both
                fill_color = color_map[viol_found[0]]
                edge_color = color_map[viol_found[0]]
            elif len(viol_found) >= 2:
                # Mixed Case: Edge is first chant, Fill is second chant
                edge_color = color_map[viol_found[0]]
                fill_color = color_map[viol_found[1]]
            elif '0' not in labels:
                pass

        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [lon_jitter, lat_jitter],
            },
            'properties': {
                'time': row['date_utc'].strftime('%Y-%m-%dT%H:%M:%S'),
                'popup': f"<b>Violence/Other ID: {row['id']}</b><br>Label: {row['Label']}",
                "icon": "circle",
                "iconstyle": {
                        "fillColor": fill_color,
                        "fillOpacity": 1,
                        "color": edge_color,  # This defines the edge color
                        "stroke": "true",
                        "radius": 10,
                        "weight": 4           # Thicker weight makes the edge color visible
                    },
            }
        }
        features.append(feature)

    # 3. Add the Timeline Slider to the second map
    TimestampedGeoJson(
        {'type': 'FeatureCollection', 'features': features},
        period='P1D',
        add_last_point=True,
        auto_play=False,
        date_options='YYYY-MM-DD',
    ).add_to(m)

    # m = add_legend_violence(m)

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
        st.subheader("Map Legend")
        # Using HTML to create colored circles
        st.markdown("""
        <div style="line-height: 2;">
            <span style="color:blue; font-size:20px;">●</span> <b>Label 1:</b> Economy<br>
            <span style="color:red; font-size:20px;">●</span> <b>Label 2:</b> Anti-regime<br>
            <span style="color:magenta; font-size:20px;">●</span> <b>Label 3:</b> Pro-monarchy<br>
            <span style="border: 2px solid red; border-radius: 50%; width: 12px; height: 12px; display: inline-block; background-color: blue; margin-right: 5px;"></span> <b>Two-tone:</b> Mixed Slogans
        </div>
        """, unsafe_allow_html=True)

        #         <i class="fa fa-circle" style="color:blue"></i>&nbsp; 1 Economy<br>
        # <i class="fa fa-circle" style="color:red"></i>&nbsp; 2 Anti-regime<br>
        # <i class="fa fa-circle" style="color:magenta"></i>&nbsp; 3 Pro-monarchy

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

    st.divider() # Adds a visual horizontal line
    st.header("Slogans in numbers")
    st.write("""
    Table below shows the number of instances of chanted slogans within each category. 
    """)

    individual_counts = {
        "Label 1 (Economy)": [int(data['Label'].astype(str).str.contains('1').sum())],
        "Label 2 (Anti-regime)": [int(data['Label'].astype(str).str.contains('2').sum())],
        "Label 3 (Promonarchy)": [int(data['Label'].astype(str).str.contains('3').sum())],
    }
    individual_counts = pd.DataFrame(individual_counts).T
    individual_counts.columns = [ 'Count']

    left_spacer, table_col, right_spacer = st.columns([1, 2, 1])

    with table_col:
        st.write("### Slogan Statistics")
        st.table(individual_counts)




    st.divider()
    st.header("Timeline of Violence & Conflict (Labels 4-8)")

    col1, col2 = st.columns([1, 2])

    with col2:
        # Display the map
        v_map_obj = create_violence_timeline_map(data)

        # 'key="violence_timeline"' prevents conflicts with the first map
        st_folium(v_map_obj, width=800, height=600, key="violence_timeline")

        # with st.sidebar:
        #     st.write("### Map Legends")
        #     with st.expander("Violence Map (Labels 4-8)"):
        #         st.markdown("🟡 Tear gas<br>🟠 Cold weapon<br>🔴 Shotgun/Assault<br>⚫ Protestor violence", unsafe_allow_html=True)

    with col1:
        st.subheader("Violence mapped over time")
        # Logic to show video if a point is clicked

        st.subheader("Map Legend")
        # Using HTML to create colored circles
        st.markdown("""
        <div style="line-height: 2;">
            <span style="color:yellow; font-size:20px;">●</span> <b>Label 4:</b> Altercation - Tear gas<br>
            <span style="color:orange; font-size:20px;">●</span> <b>Label 5:</b> Cold weapon<br>
            <span style="color:orangered; font-size:20px;">●</span> <b>Labe 6:</b> Shotgun<br>
            <span style="color:red; font-size:20px;">●</span> <b>Label 7:</b> Assault weapon<br>
            <span style="color:black; font-size:20px;">●</span> <b>Label 8:</b> Protestor violence<br>
            <span style="border: 2px solid red; border-radius: 50%; width: 12px; height: 12px; display: inline-block; background-color: blue; margin-right: 5px;"></span> <b>Two-tone:</b> Mixed Slogans
        </div>
        """, unsafe_allow_html=True)



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
    st.error(f"Please ensure 'geocoded_results.xlsx' exists. Error: {e}")
