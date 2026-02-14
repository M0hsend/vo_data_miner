import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import TimestampedGeoJson
import numpy as np
import glob

# --- CONFIG & SETUP ---
st.set_page_config(layout="wide", page_title="VahidOnline Data Analysis")

FEATURED_IDS = [68847, 68873, 68886, 68918, 68981, 68994, 69000, 69010, 69042, 69200, 69218, 69225, 69265, 69277, 69293, 69304, 69511, 69702, 69705]
FEATURED_COLOR = "cyan"


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



def create_map(df):
    # Center map
    start_loc = [32.4279, 53.6880]
    m = folium.Map(location=start_loc, zoom_start=6, tiles="cartodbpositron")

    color_map = {'1': "blue", '2': "red", '3': "magenta"}

    for _, row in df.iterrows():
        # ... keep your jitter logic here ...


        seed = int(str(row['id'])[-6:]) # Use last 6 digits of ID as a seed
        np.random.seed(seed) 

        offset = 0.0015
        lat_jitter = row['latitude'] + np.random.uniform(-1 * offset, offset)
        lon_jitter = row['longitude'] + np.random.uniform(-1 * offset, offset)

        # labels = str(row['Label'])
        # chants_found = [c for c in labels if c in ['1', '2', '3']]



        is_featured = row['id'] in FEATURED_IDS
        chants = [c for c in str(row['Label']) if c in ['1', '2', '3']]
        if not chants and not is_featured: continue

        fill = FEATURED_COLOR if is_featured else color_map.get(chants[0], "gray")

        # By using a unique 'name' or embedding the ID in the popup, 
        # st_folium can track it directly.
        folium.CircleMarker(
            location=[lat_jitter, lon_jitter],
            radius=12 if is_featured else 8,
            color="white" if is_featured else fill,
            fill=True,
            fill_color=fill,
            fill_opacity=0.8,
            popup=f"{row['id']}", # This will appear in last_object_clicked_popup
            tooltip=f"ID: {row['id']}" # This will appear in last_object_clicked_tooltip
        ).add_to(m)

    return m





def create_violence_timeline_map(filtered_df):
    # Setup map centered on Iran
    m = folium.Map(location=[32.4279, 53.6880], zoom_start=5, tiles="cartodbpositron")

    color_map = {
        '4': "yellow",   
        '5': "orange",    
        '6': "orangered",
        '7': "red",
        '8': "black", 
    }

    for _, row in filtered_df.iterrows():
        # Deterministic jitter using ID
        seed = int(str(row['id'])[-6:])
        np.random.seed(seed)
        offset = 0.015
        lat_jitter = row['latitude'] + np.random.uniform(-1 * offset, offset)
        lon_jitter = row['longitude'] + np.random.uniform(-1 * offset, offset)

        labels = str(row['Label'])
        viol_labels = ['4','5','6', '7', '8']
        viol_found = [c for c in labels if c in viol_labels]

        if not viol_found:
            continue

        # Color logic: edge is first label found, fill is second (if applicable)
        edge_color = color_map[viol_found[0]]
        fill_color = color_map[viol_found[1]] if len(viol_found) >= 2 else edge_color

        # Direct CircleMarker for stable click-detection
        folium.CircleMarker(
            location=[lat_jitter, lon_jitter],
            radius=10,
            color=edge_color,
            weight=4,
            fill=True,
            fill_color=fill_color,
            fill_opacity=1,
            # IDs for st_folium retrieval
            popup=f"Violence ID: {row['id']}",
            tooltip=f"ID: {row['id']}"
        ).add_to(m)

    return m

# --- STREAMLIT UI ---
st.title("Mapping the timeline of the Protests in Iran")

try:
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

        # UI Section
        min_date = data['date_utc'].min().date()
        max_date = data['date_utc'].max().date()

        # The slider effectively acts as your timeline
        selected_date = st.slider("Timeline Control", min_date, max_date, min_date)

        # Filter dataframe
        filtered_data = data[data['date_utc'].dt.date <= selected_date]

        # Display Map
        map_obj = create_map(filtered_data)
        map_data = st_folium(map_obj, key="main_map")




        # map_obj = create_map(data)
        # # We capture the map output to detect clicks
        # map_data = st_folium(map_obj, width=800, height=600, key="main_map")
        # print(map_data)
        # print("HERE:", map_data.get("last_object_clicked"))

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

        # Logic to show video if a point is clicked
# Logic to show video if a point is clicked
        videos_paths = glob.glob('static/*.mp4')
        print(videos_paths)
        if map_data and map_data.get("last_object_clicked_tooltip"):
            # Extract the ID directly from the tooltip string (e.g., "ID: 68781")
            tooltip_text = map_data["last_object_clicked_tooltip"]
            clicked_id = tooltip_text.replace("ID: ", "").strip()

            st.write(f"### Selected ID: {clicked_id}")

            # Trigger video
            if int(clicked_id) in FEATURED_IDS:
                selected_row = data[data['id'] == int(clicked_id)]
                row_data = selected_row.iloc[0]
                if 'address' in row_data:
                    st.write(f"**Location:** {row_data['address']}")
                if 'Description' in row_data: 
                    st.info(f"**Description:** {row_data['Description']}")

                video_match = [p for p in videos_paths if clicked_id in p]
                print("PATH: ", video_match)
                if video_match:
                    st.video(video_match[0])



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







    # --- VIOLENCE MAP SECTION ---
    st.divider()
    st.header("Timeline of Violence & Conflict")

    # Filter for relevant violence labels first
    violence_pattern = '[45678]'
    violence_data = data[data['Label'].astype(str).str.contains(violence_pattern)].copy()

    col1_v, col2_v = st.columns([1, 2])

    with col2_v:
        # Use a separate slider or the same one as above
        v_selected_date = st.slider("Violence Timeline Control", min_date, max_date, min_date, key="v_slider")

        # Filter by date
        v_filtered = violence_data[violence_data['date_utc'].dt.date <= v_selected_date]

        # Render map
        v_map_obj = create_violence_timeline_map(v_filtered)
        v_map_data = st_folium(v_map_obj, width=800, height=600, key="violence_timeline")

    with col1_v:
        st.subheader("Violence Details")

        st.subheader("Map Legend")
        # Using HTML to create colored circles
        st.markdown("""
        <div style="line-height: 2;">
            <span style="color:yellow; font-size:20px;">●</span> <b>Label 4:</b> Altercation - Tear gas<br>
            <span style="color:orange; font-size:20px;">●</span> <b>Label 5:</b> Cold weapon<br>
            <span style="color:orangered; font-size:20px;">●</span> <b>Labe 6:</b> Shotgun<br>
            <span style="color:red; font-size:20px;">●</span> <b>Label 7:</b> Assault weapon<br>
            <span style="color:black; font-size:20px;">●</span> <b>Label 8:</b> Protestor defensive violence
        </div>
        """, unsafe_allow_html=True)

        # Logic to show video/text for the Violence Map
        if v_map_data and v_map_data.get("last_object_clicked_tooltip"):
            v_tooltip = v_map_data["last_object_clicked_tooltip"]
            v_clicked_id = v_tooltip.replace("ID: ", "").strip()

            # Display ID and matched data
            st.write(f"### Selected Violence ID: {v_clicked_id}")
            v_row = data[data['id'] == int(v_clicked_id)].iloc[0]

            st.write(f"**Location:** {v_row['address']}")
            # if int(v_clicked_id) in VIOL_FEATURED_IDS:
            #     selected_row = data[data['id'] == int(clicked_id)]
            #     row_data = selected_row.iloc[0]
            #     if 'address' in row_data:
            #         st.write(f"**Location:** {row_data['address']}")
            #     if 'Description' in row_data: 
            #         st.info(f"**Description:** {row_data['Description']}")

            #     video_match = [p for p in videos_paths if clicked_id in p]
            #     print("PATH: ", video_match)
            #     if video_match:
            #         st.video(video_match[0])


except Exception as e:
    st.error(f"Please ensure 'geocoded_results.xlsx' exists. Error: {e}")
