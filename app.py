import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import TimestampedGeoJson
import numpy as np
import glob, os
from folium.plugins import MarkerCluster
import altair as alt
import datetime

st.markdown("""
    <style>
    /* Highlight the slider track and handle */
    .stSlider [data-baseweb="slider"] {
        padding-top: 15px;
        padding-bottom: 15px;
    }
    /* Add a background color to the slider area to make it a distinct 'section' */
    div[data-testid="stExpander"], .stSlider {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00d4ff; /* Cyan accent matching your FEATURED_COLOR */
    }
    </style>
    """, unsafe_allow_html=True)


# --- CONFIG & SETUP ---
st.set_page_config(layout="wide", page_title="VahidOnline Data Analysis")

FEATURED_IDS = [68847, 68873, 68886, 68918, 68981, 68994, 69000, 69010, 69042, 69200, 69218, 69225, 69265, 69277, 69293, 69304, 69511, 
                69518, 69540, 69641, 69688, 69702, 69705]
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



@st.cache_data
def load_memorial_data(file_path):
    df = pd.read_excel(file_path)
    # Perform all cleaning here once
    df = df.dropna(subset=['latitude', 'longitude']).copy()
    return df

# # @st.cache_resource
# def get_cached_casualty_map(_df):
#     # The underscore prefix tells Streamlit not to hash the entire dataframe
#     # This significantly speeds up the caching check
#     return create_casualty_map(_df)



def create_map(df):
    # 1. Define the boundary coordinates for Iran
    # Format: [[South, West], [North, East]]
    iran_bounds = [[24.0, 43.0], [40.0, 64.0]] 

    # 2. Add the constraints to the Map object
    m = folium.Map(
        location=[32.4279, 53.6880], 
        zoom_start=6, 
        tiles="cartodbpositron",
        max_bounds=True,           # Enables boundary enforcement
        min_lat=iran_bounds[0][0], # Southern boundary
        max_lat=iran_bounds[1][0], # Northern boundary
        min_lon=iran_bounds[0][1], # Western boundary
        max_lon=iran_bounds[1][1], # Eastern boundary
        min_zoom=5,                # Prevents zooming out to see the whole world
        max_zoom=14                # Optional: prevents excessive zooming in
    )


    df = df.dropna(subset=['latitude', 'longitude'])
    # Center map
    start_loc = [32.4279, 53.6880]

    color_map = {'1': "blue", '2': "red", '3': "magenta"}

    for _, row in df.iterrows():


        seed = int(str(row['id'])[-6:]) # Use last 6 digits of ID as a seed
        np.random.seed(seed) 

        offset = 0.0015
        lat_jitter = row['latitude'] + np.random.uniform(-1 * offset, offset)
        lon_jitter = row['longitude'] + np.random.uniform(-1 * offset, offset)

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
    filtered_df = filtered_df.dropna(subset=['latitude', 'longitude'])
    # Setup map centered on Iran

        # 1. Define the boundary coordinates for Iran
    # Format: [[South, West], [North, East]]
    iran_bounds = [[24.0, 43.0], [40.0, 64.0]] 

    # 2. Add the constraints to the Map object
    m = folium.Map(
        location=[32.4279, 53.6880], 
        zoom_start=6, 
        tiles="cartodbpositron",
        max_bounds=True,           # Enables boundary enforcement
        min_lat=iran_bounds[0][0], # Southern boundary
        max_lat=iran_bounds[1][0], # Northern boundary
        min_lon=iran_bounds[0][1], # Western boundary
        max_lon=iran_bounds[1][1], # Eastern boundary
        min_zoom=5,                # Prevents zooming out to see the whole world
        max_zoom=14                # Optional: prevents excessive zooming in
    )

    color_map = {
        '4': "yellow",   
        '5': "orange",    
        '6': "orangered",
        '7': "purple",
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

def create_casualty_map(df):
    # Use a fixed starting location to reduce computation
    # 1. Define the boundary coordinates for Iran
    # Format: [[South, West], [North, East]]
    iran_bounds = [[24.0, 43.0], [40.0, 64.0]] 

    # 2. Add the constraints to the Map object
    m = folium.Map(
        location=[32.4279, 53.6880], 
        zoom_start=6, 
        tiles="cartodbpositron",
        max_bounds=True,           # Enables boundary enforcement
        min_lat=iran_bounds[0][0], # Southern boundary
        max_lat=iran_bounds[1][0], # Northern boundary
        min_lon=iran_bounds[0][1], # Western boundary
        max_lon=iran_bounds[1][1], # Eastern boundary
        min_zoom=5,                # Prevents zooming out to see the whole world
        max_zoom=14                # Optional: prevents excessive zooming in
    )

    # Speed up MarkerCluster
    marker_cluster = MarkerCluster(
        disableClusteringAtZoom=10,
        spiderfyOnMaxZoom=True
    ).add_to(m)

    # Use a vectorized approach or a faster loop
    for row in df.itertuples():
        folium.CircleMarker(
            location=[row.latitude, row.longitude],
            radius=5,
            color="black",
            weight=1,
            fill=True,
            fill_opacity=0.6,
            tooltip="ID: " + str(row.message_id) 
        ).add_to(marker_cluster)
    return m

# --- STREAMLIT UI ---
st.title("Mapping the timeline of the Protests in Iran")

try:
    data = load_and_clean_data("final_data.xlsx")
    # memo_data = pd.read_excel("memorial_final_data.xlsx")
    # memo_data = memo_data.dropna(subset=['address']).copy()

        # --- Intro SECTION (Full Width) ---
    st.divider() # Adds a visual horizontal line
    st.header("Analysis Overview")
    st.write("""
Between late December 2025 and early January 2026, Iran experienced a [massive nationwide uprising](https://en.wikipedia.org/wiki/2025%E2%80%932026_Iranian_protests). Initially sparked by soaring inflation, 
a malfunctioning economy, and a plummeting currency value, the movement quickly evolved into a widespread protest against the existence of the regime itself. 
This uprising was met with unprecedented brutal force by the government, resulting in tens of thousands of casualties—most of which occurred during the two-day
peak of the protests on January 8–9, 2026.
Because independent journalism is prohibited in Iran, news is primarily disseminated through videos captured by protesters and bystanders and shared globally. 
One of the most trusted platforms for these recordings is [VahidOnline’s](https://en.wikipedia.org/wiki/Vahid_Online) Telegram channel.

To develop this analysis platform, we analyzed 820 videos from VahidOnline posted between December 14, 2025, and January 13, 2026. 
This period covers the start of the uprising through the government-imposed nationwide internet blackout on January 8th, which utilized military-grade jamming
technology (see [here](https://www.ft.com/content/5d848323-84a9-4512-abd2-dd09e0a786a3) - paid access). Our objective was to create a temporal map of the uprising, 
tracking both the evolution of protest slogans and the intensity of state violence.

Each video was carefully reviewed and labeled based on:

- Chanted Slogans: Categorized to show the shift in protest focus (see the first map).

- Levels of Violence: Documenting the force used by the regime to suppress demonstrators.

- Protester Response: Identifying instances of defensive violence or civil unrest (see the second map).

Locations were determined using the metadata and captions provided with each video. 
Of the initial corpus, 769 videos were successfully labeled and geolocated. 
The raw dataset is available for review via [this link](https://drive.google.com/drive/folders/1A8jxa_Pz1ITmyfCQJMkRETotUvXzsRZS?usp=sharing). 
Each video ID - visible by clicking on the points - can then be used to find the corresponding video in the data stash shared above.


Finally, we have integrated a map of nationwide casualties using data compiled by the memorial Telegram channel, [RememberTheirNames](https://t.me/RememberTheirNames).


If you would like to provide any feedback please contact us at [this](mailto:iran1404data@gmail.com) address.
""")

    st.subheader("Number of videos posted on VahidOnline leading to 9th Jan 2026")
    col_a, col_b = st.columns(2)

    with col_a:
        # st.write("Histogram of posted videos on VahidOnline")
        # hist_data = data.copy()
        # hist_data['date_utc'] = pd.to_datetime(hist_data['date_utc'], utc=True, errors='coerce')
        # hist_data['just_date'] = hist_data['date_utc'].dt.date
        # date_counts = hist_data['just_date'].value_counts().sort_index()
        # st.bar_chart(date_counts)
        # st.caption("<p style='text-align: center;'>Date of Video</p>", unsafe_allow_html=True)

        st.write("Histogram of posted videos on VahidOnline")
        hist_data = data.copy()
        hist_data['date_utc'] = pd.to_datetime(hist_data['date_utc'], utc=True, errors='coerce')
        hist_data['just_date'] = hist_data['date_utc'].dt.date

        # Prepare data for Altair
        date_counts = hist_data['just_date'].value_counts().reset_index()
        date_counts.columns = ['Date', 'Count']
        date_counts = date_counts.sort_values('Date')

        # Create the chart with fixed lateral axes
        chart = alt.Chart(date_counts).mark_bar(color='steelblue').encode(
            x=alt.X('Date:T', 
                    title='Date of Video',
                    # This fixes the axis range to the period of the uprising
                    scale=alt.Scale(domain=['2025-12-20', '2026-01-15']) 
            ),
            y=alt.Y('Count:Q', title='Number of Videos'),
            tooltip=['Date', 'Count']
        ).interactive(bind_y=False) # This allows the zoom/pan within the fixed range

        st.altair_chart(chart, use_container_width=True)
        st.caption("<p style='text-align: center;'>Date of Video (Scroll to zoom, drag to pan)</p>", unsafe_allow_html=True)

    with col_b:
        st.write("""
        In this plot you can see the number of videos shared on VahidOnline platform across the dates specified. 
        Please note that we are ignoring all the non-video contents here. 
        The point at which the government shut down the internet is clear.
        """)

    # You can even use a container to group things
    with st.container():
        st.info("💡 Tip: Use the timeline slider at the top of the map to filter by date.")

    col1, col2 = st.columns([1, 2])

    with col2:

        # UI Section
        min_date = data['date_utc'].min().date()
        max_date = data['date_utc'].max().date()

        # The slider effectively acts as your timeline
        start_date = datetime.date(2025, 12, 25)
        selected_date = st.slider("Slide to Change the Date", min_date, max_date, start_date)

        # Filter dataframe
        filtered_data = data[data['date_utc'].dt.date <= selected_date]

        # Display Map
        map_obj = create_map(filtered_data)
        map_data = st_folium(map_obj, key="main_map")

    with col1:
        st.subheader("Slogans chanted in protests mapped over time")
        st.subheader("Map Legend")
        # Using HTML to create colored circles
        st.markdown("""
        <div style="line-height: 2;">
            <span style="color:blue; font-size:20px;">●</span> <b>Label 1:</b> Economy<br>
            <span style="color:red; font-size:20px;">●</span> <b>Label 2:</b> Anti-regime<br>
            <span style="color:magenta; font-size:20px;">●</span> <b>Label 3:</b> Pro-monarchy<br>
            <span style="border: 2px solid red; border-radius: 50%; width: 12px; height: 12px; display: inline-block; background-color: blue; margin-right: 5px;"></span> <b>Two-tone:</b> Mixed Slogans<br>
            <span style="color:cyan; font-size:20px;">●</span> <b>Featured video (Click for the video to appear)</b> 
        </div>
        """, unsafe_allow_html=True)

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
                    st.write(f"**Date:** {row_data['date_utc'].date()}")
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
        start_date = datetime.date(2025, 12, 25)
        v_selected_date = st.slider("Slide to Change the Date", min_date, max_date, start_date, key="v_slider")

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
            <span style="color:orangered; font-size:20px;">●</span> <b>Label 6:</b> Shotgun<br>
            <span style="color:purple; font-size:20px;">●</span> <b>Label 7:</b> Assault weapon<br>
            <span style="color:black; font-size:20px;">●</span> <b>Label 8:</b> Protester defensive violence
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

    # --- CASUALTY MAP SECTION ---
    st.divider()
    st.header("Casualties Mapped")
    st.write("""
    The number of killed Protesters is currently unkown with reported casualties ranging from around 6000 to more than 30000 
    [please see sources [here](https://en.wikipedia.org/wiki/2026_Iran_massacres#cite_note-4)]. Here we have used the information posted on
    the Telegram channel [RememberTheirNames](https://t.me/RememberTheirNames) to map the casualties. This map will be updated over time. 
        """)
    st.write("Date updated: **21 Feb 2026**")

    # 1. Prepare your casualty dataframe (assuming it follows the same cleaning logic)
    # casualty_data = load_and_clean_data("casualty_data.xlsx") 

    col1_c, col2_c = st.columns([1, 2])
    memo_data = load_memorial_data("memorial_final_data_21Feb2026.xlsx")
    # c_map_obj = get_cached_casualty_map(memo_data)

    with col2_c:
        c_map_obj = create_casualty_map(memo_data)
        # get_cached_casualty_map(memo_data)

        c_map_data = st_folium(
            c_map_obj, 
            width=800, 
            height=600, 
            key="casualty_map",
            returned_objects=["last_object_clicked_tooltip"]
        )

    with col1_c:
        st.subheader("Details")
        # Since tooltip now only contains the ID (see Step 2), cleanup is easier
        clicked_val = c_map_data.get("last_object_clicked_tooltip")

        if clicked_val:
            clicked_id = str(clicked_val[3:]).strip()
            # Filter once using the index for speed
            selected_rows = memo_data[memo_data['message_id'] == int(clicked_id)]

            if not selected_rows.empty:
                c_row = selected_rows.iloc[0]
                st.write(f"### {c_row.get('Name', 'ID: ' + clicked_id)}")
                st.write(f"**Location:** {c_row.get('City', 'Unknown')}")

                image_path = f"static/images/{clicked_id}.jpg"
                if os.path.exists(image_path):
                    st.image(image_path, width=400)


except Exception as e:
    st.error(f"Please ensure 'geocoded_results.xlsx' exists. Error: {e}")
