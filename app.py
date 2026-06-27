import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np
import glob, os
from folium.plugins import MarkerCluster
import altair as alt
import datetime

# ---------------------------------------------------------------------------
# CONFIG — must be the very first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="VahidOnline | وحیدآنلاین")

# ---------------------------------------------------------------------------
# LANGUAGE SELECTION
# ---------------------------------------------------------------------------
if 'lang' not in st.session_state:
    st.session_state.lang = 'fa'

lang_choice = st.sidebar.radio(
    "🌐 زبان / Language",
    options=['fa', 'en'],
    format_func=lambda x: 'فارسی' if x == 'fa' else 'English',
    index=0 if st.session_state.lang == 'fa' else 1,
)
st.session_state.lang = lang_choice
L = lang_choice  # shorthand used throughout

# ---------------------------------------------------------------------------
# TRANSLATIONS
# ---------------------------------------------------------------------------
T = {
    'page_title': {
        'fa': 'تحلیل داده‌های وحیدآنلاین',
        'en': 'VahidOnline Data Analysis',
    },
    'main_title': {
        'fa': 'نقشه‌نگاری خیزش‌های مردمی ایران',
        'en': 'Mapping the Timeline of the Protests in Iran',
    },
    'overview_header': {
        'fa': 'مروری بر تحلیل',
        'en': 'Analysis Overview',
    },
    'overview_body': {
        'fa': """
از اواخر آذرماه ۱۴۰۴ تا اوایل دی‌ماه همان سال، ایران شاهد یک [قیام سراسری گسترده](https://en.wikipedia.org/wiki/2025%E2%80%932026_Iranian_protests) بود.
این جنبش که ابتدا با انگیزه‌های اقتصادی نظیر تورم افسارگسیخته، فروپاشی اقتصاد و سقوط ارزش ریال آغاز شد، به‌سرعت به اعتراضی فراگیر علیه موجودیت نظام تبدیل گردید.
این خیزش با سرکوب خشن و بی‌سابقه‌ای از سوی حکومت مواجه شد که در نتیجه آن چندین هزار نفر کشته و زخمی شدند؛ بیشترین تلفات در دو روز اوج اعتراضات، یعنی هجدهم و نوزدهم دی‌ماه ۱۴۰۴، به ثبت رسید.

چون روزنامه‌نگاری مستقل در ایران با محدودیت شدیدی همراه است، اخبار عمدتاً از طریق ویدیوهایی که توسط معترضان و شاهدان عینی ضبط و در سطح جهانی به اشتراک گذاشته می‌شود، منتشر می‌گردد.
یکی از معتبرترین منابع برای انتشار این تصاویر، کانال تلگرامی [وحیدآنلاین](https://en.wikipedia.org/wiki/Vahid_Online) است.

برای توسعه این بستر تحلیلی حاضر، ۸۲۰ ویدیو از وحیدآنلاین که بین ۲۳ آذر ۱۴۰۴ و ۲۳ دی‌ماه ۱۴۰۴ منتشر شده بودند، مورد بررسی قرار گرفتند.
این بازه زمانی از آغاز خیزش تا قطعی سراسری اینترنت توسط حکومت در هجدهم دی‌ماه — که با استفاده از فناوری پارازیت نظامی اجرا شد — را در بر می‌گیرد
(برای اطلاعات بیشتر [اینجا](https://www.ft.com/content/5d848323-84a9-4512-abd2-dd09e0a786a3) را ببینید ).
هدف ما ایجاد نقشه‌ای زمانی از خیزش بود که هم تحول شعارهای اعتراضی و هم شدت خشونت دولتی را به تصویر بکشد.

هر ویدیو به‌دقت بررسی و بر اساس معیارهای زیر برچسب‌گذاری شد:

- **شعارهای سرداده‌شده:** دسته‌بندی‌شده برای نشان دادن تغییر محور اعتراضات (نقشه اول).
- **سطوح خشونت:** مستندسازی نیرویی که حکومت برای سرکوب معترضان به‌کار گرفت.
- **واکنش معترضان:** شناسایی موارد خشونت دفاعی یا آشوب مدنی (نقشه دوم).

موقعیت مکانی ویدیوها بر اساس توضیحات پیوست هر ویدیو تعیین شد.
از مجموع ویدیوهای اولیه، ۷۶۹ مورد با موفقیت برچسب‌گذاری و جغرافیایابی شدند.
مجموعه داده خام از طریق [این لینک](https://drive.google.com/drive/folders/1A8jxa_Pz1ITmyfCQJMkRETotUvXzsRZS?usp=sharing) قابل دسترسی است.
هر شناسه ویدیو — که با کلیک روی نقاط نمایش داده می‌شود — می‌تواند برای یافتن ویدیوی مربوطه در بایگانی داده‌های فوق استفاده شود.

در نهایت، نقشه‌ای از تلفات سراسری با استفاده از داده‌های کانال تلگرامی [نام‌ها را به خاطر بسپار](https://t.me/RememberTheirNames) به این مجموعه افزوده شده است.

برای ارسال بازخورد، با ما از طریق [این آدرس](mailto:iran1404data@gmail.com) در تماس باشید.
""",
        'en': """
Between late December 2025 and early January 2026, Iran experienced a [massive nationwide uprising](https://en.wikipedia.org/wiki/2025%E2%80%932026_Iranian_protests). Initially sparked by soaring inflation,
a malfunctioning economy, and a plummeting currency value, the movement quickly evolved into a widespread protest against the existence of the regime itself.
This uprising was met with unprecedented brutal force by the government, resulting in tens of thousands of casualties—most of which occurred during the two-day
peak of the protests on January 8–9, 2026.

Because independent journalism is prohibited in Iran, news is primarily disseminated through videos captured by protesters and bystanders and shared globally.
One of the most trusted platforms for these recordings is [VahidOnline's](https://en.wikipedia.org/wiki/Vahid_Online) Telegram channel.

To develop this analysis platform, we analyzed 820 videos from VahidOnline posted between December 14, 2025, and January 13, 2026.
This period covers the start of the uprising through the government-imposed nationwide internet blackout on January 8th, which utilized military-grade jamming
technology (see [here](https://www.ft.com/content/5d848323-84a9-4512-abd2-dd09e0a786a3) - paid access). Our objective was to create a temporal map of the uprising,
tracking both the evolution of protest slogans and the intensity of state violence.

Each video was carefully reviewed and labeled based on:

- **Chanted Slogans:** Categorized to show the shift in protest focus (see the first map).
- **Levels of Violence:** Documenting the force used by the regime to suppress demonstrators.
- **Protester Response:** Identifying instances of defensive violence or civil unrest (see the second map).

Locations were determined using the metadata and captions provided with each video.
Of the initial corpus, 769 videos were successfully labeled and geolocated.
The raw dataset is available for review via [this link](https://drive.google.com/drive/folders/1A8jxa_Pz1ITmyfCQJMkRETotUvXzsRZS?usp=sharing).
Each video ID — visible by clicking on the points — can then be used to find the corresponding video in the data stash shared above.

Finally, we have integrated a map of nationwide casualties using data compiled by the memorial Telegram channel, [RememberTheirNames](https://t.me/RememberTheirNames).

If you would like to provide any feedback please contact us at [this](mailto:iran1404data@gmail.com) address.
""",
    },
    'histogram_subheader': {
        'fa': 'تعداد ویدیوهای منتشرشده در وحیدآنلاین تا ۱۹ دی ۱۴۰۴',
        'en': 'Number of Videos Posted on VahidOnline Leading to 9th Jan 2026',
    },
    'histogram_title': {
        'fa': 'نمودار میله‌ای ویدیوهای منتشرشده در وحیدآنلاین',
        'en': 'Histogram of Posted Videos on VahidOnline',
    },
    'histogram_x': {
        'fa': 'تاریخ ویدیو',
        'en': 'Date of Video',
    },
    'histogram_y': {
        'fa': 'تعداد ویدیوها',
        'en': 'Number of Videos',
    },
    'histogram_caption': {
        'fa': 'تاریخ ویدیو (اسکرول برای زوم، درگ برای جابجایی)',
        'en': 'Date of Video (Scroll to zoom, drag to pan)',
    },
    'histogram_note': {
        'fa': """در این نمودار می‌توانید تعداد ویدیوهای به اشتراک گذاشته‌شده در کانال وحیدآنلاین را در بازه‌های زمانی مشخص مشاهده کنید.
توجه داشته باشید که محتوای غیرویدیویی در اینجا در نظر گرفته نشده است.
لحظه‌ای که حکومت اینترنت را قطع کرد، به‌وضوح در نمودار قابل مشاهده است.""",
        'en': """In this plot you can see the number of videos shared on VahidOnline platform across the dates specified.
Please note that we are ignoring all the non-video contents here.
The point at which the government shut down the internet is clear.""",
    },
    'slider_tip': {
        'fa': '💡 توجه: از اسلایدر زمانی بالای نقشه برای فیلتر کردن بر اساس تاریخ استفاده کنید.',
        'en': '💡 Tip: Use the timeline slider at the top of the map to filter by date.',
    },
    'featured_timeline_subheader': {
        'fa': 'خط زمانی ویدیوهای ویژه',
        'en': 'Featured Videos Timeline',
    },
    'featured_timeline_caption': {
        'fa': 'برای پخش ویدیو روی نقطه کلیک کنید.',
        'en': 'Click a dot to play the corresponding video.',
    },
    'tl_tooltip_id': {
        'fa': 'شناسه ویدیو',
        'en': 'Video ID',
    },
    'tl_tooltip_date': {
        'fa': 'تاریخ',
        'en': 'Date',
    },
    'tl_tooltip_location': {
        'fa': 'مکان',
        'en': 'Location',
    },
    'tl_id_label': {
        'fa': '**شناسه:**',
        'en': '**ID:**',
    },
    'tl_location_label': {
        'fa': '**مکان:**',
        'en': '**Location:**',
    },
    'tl_date_label': {
        'fa': '**تاریخ:**',
        'en': '**Date:**',
    },
    'tl_desc_label': {
        'fa': '**توضیحات:**',
        'en': '**Description:**',
    },
    'tl_no_video': {
        'fa': 'فایل ویدیویی برای این شناسه یافت نشد.',
        'en': 'No video file found for this ID.',
    },
    'slogan_map_subheader': {
        'fa': 'شعارهای اعتراضی در طول زمان روی نقشه',
        'en': 'Slogans Chanted in Protests Mapped Over Time',
    },
    'map_legend': {
        'fa': 'راهنمای نقشه',
        'en': 'Map Legend',
    },
    'legend_slogan': {
        'fa': """<div style="line-height: 2; direction: rtl; text-align: right;">
            <span style="color:blue; font-size:20px;">●</span> <b>برچسب ۱:</b> اقتصادی<br>
            <span style="color:red; font-size:20px;">●</span> <b>برچسب ۲:</b> ضد رژیم<br>
            <span style="color:magenta; font-size:20px;">●</span> <b>برچسب ۳:</b> طرفدار سلطنت<br>
            <span style="border: 2px solid red; border-radius: 50%; width: 12px; height: 12px; display: inline-block; background-color: blue; margin-right: 5px;"></span> <b>دو رنگ:</b> شعارهای ترکیبی<br>
            <span style="color:cyan; font-size:20px;">●</span> <b>ویدیوی ویژه (برای نمایش ویدیو کلیک کنید)</b>
        </div>""",
        'en': """<div style="line-height: 2;">
            <span style="color:blue; font-size:20px;">●</span> <b>Label 1:</b> Economy<br>
            <span style="color:red; font-size:20px;">●</span> <b>Label 2:</b> Anti-regime<br>
            <span style="color:magenta; font-size:20px;">●</span> <b>Label 3:</b> Pro-monarchy<br>
            <span style="border: 2px solid red; border-radius: 50%; width: 12px; height: 12px; display: inline-block; background-color: blue; margin-right: 5px;"></span> <b>Two-tone:</b> Mixed Slogans<br>
            <span style="color:cyan; font-size:20px;">●</span> <b>Featured video (Click for the video to appear)</b>
        </div>""",
    },
    'slider_label': {
        'fa': 'تاریخ را تغییر دهید',
        'en': 'Slide to Change the Date',
    },
    'selected_id': {
        'fa': '### شناسه انتخاب‌شده:',
        'en': '### Selected ID:',
    },
    'location_label': {
        'fa': '**مکان:**',
        'en': '**Location:**',
    },
    'date_label': {
        'fa': '**تاریخ:**',
        'en': '**Date:**',
    },
    'desc_label': {
        'fa': '**توضیحات:**',
        'en': '**Description:**',
    },
    'slogans_numbers_header': {
        'fa': 'شعارها به عدد',
        'en': 'Slogans in Numbers',
    },
    'slogans_numbers_body': {
        'fa': 'جدول زیر تعداد تکرار شعارهای هر دسته را نشان می‌دهد.',
        'en': 'Table below shows the number of instances of chanted slogans within each category.',
    },
    'slogan_stats_title': {
        'fa': '### آمار شعارها',
        'en': '### Slogan Statistics',
    },
    'slogan_rows': {
        'fa': {
            'l1': 'برچسب ۱ (اقتصادی)',
            'l2': 'برچسب ۲ (ضد رژیم)',
            'l3': 'برچسب ۳ (طرفدار سلطنت)',
            'col': 'تعداد',
        },
        'en': {
            'l1': 'Label 1 (Economy)',
            'l2': 'Label 2 (Anti-regime)',
            'l3': 'Label 3 (Pro-monarchy)',
            'col': 'Count',
        },
    },
    'violence_header': {
        'fa': 'خط زمانی خشونت و درگیری',
        'en': 'Timeline of Violence & Conflict',
    },
    'violence_details': {
        'fa': 'جزئیات خشونت',
        'en': 'Violence Details',
    },
    'legend_violence': {
        'fa': """<div style="line-height: 2; direction: rtl; text-align: right;">
            <span style="color:yellow; font-size:20px;">●</span> <b>برچسب ۴:</b> درگیری - گاز اشک‌آور<br>
            <span style="color:orange; font-size:20px;">●</span> <b>برچسب ۵:</b> سلاح سرد<br>
            <span style="color:orangered; font-size:20px;">●</span> <b>برچسب ۶:</b> ساچمه‌ای / شات‌گان<br>
            <span style="color:purple; font-size:20px;">●</span> <b>برچسب ۷:</b> سلاح جنگی<br>
            <span style="color:black; font-size:20px;">●</span> <b>برچسب ۸:</b> خشونت دفاعی معترضان
        </div>""",
        'en': """<div style="line-height: 2;">
            <span style="color:yellow; font-size:20px;">●</span> <b>Label 4:</b> Altercation - Tear gas<br>
            <span style="color:orange; font-size:20px;">●</span> <b>Label 5:</b> Cold weapon<br>
            <span style="color:orangered; font-size:20px;">●</span> <b>Label 6:</b> Shotgun<br>
            <span style="color:purple; font-size:20px;">●</span> <b>Label 7:</b> Assault weapon<br>
            <span style="color:black; font-size:20px;">●</span> <b>Label 8:</b> Protester defensive violence
        </div>""",
    },
    'selected_violence_id': {
        'fa': '### شناسه خشونت انتخاب‌شده:',
        'en': '### Selected Violence ID:',
    },
    'casualty_header': {
        'fa': 'نقشه کشته‌شدگان',
        'en': 'Casualties Mapped',
    },
    'casualty_body': {
        'fa': """تعداد دقیق کشته‌شدگان هنوز مشخص نیست و آمارهای گزارش‌شده از حدود ۶۰۰۰ تا بیش از ۳۰۰۰۰ نفر متفاوت است
([منابع را اینجا ببینید](https://en.wikipedia.org/wiki/2026_Iran_massacres#cite_note-4)).
در اینجا از اطلاعات منتشرشده در کانال تلگرامی [نام‌ها را به خاطر بسپار](https://t.me/RememberTheirNames) برای نقشه‌نگاری کشته‌شدگان استفاده کرده‌ایم.
این نقشه به‌مرور زمان به‌روزرسانی خواهد شد.""",
        'en': """The number of killed protesters is currently unknown with reported casualties ranging from around 6,000 to more than 30,000
([please see sources here](https://en.wikipedia.org/wiki/2026_Iran_massacres#cite_note-4)). Here we have used the information posted on
the Telegram channel [RememberTheirNames](https://t.me/RememberTheirNames) to map the casualties. This map will be updated over time.""",
    },
    'casualty_updated': {
        'fa': 'تاریخ به‌روزرسانی: **۶ تیر ۱۴۰۵**',
        'en': 'Date updated: **27 June 2026**',
    },
    'casualty_details': {
        'fa': 'جزئیات',
        'en': 'Details',
    },
    'city_label': {
        'fa': '**شهر:**',
        'en': '**Location:**',
    },
    'unknown': {
        'fa': 'نامشخص',
        'en': 'Unknown',
    },
    'error_msg': {
        'fa': "لطفاً مطمئن شوید که فایل 'geocoded_results.xlsx' وجود دارد. خطا:",
        'en': "Please ensure 'geocoded_results.xlsx' exists. Error:",
    },
}

def t(key):
    """Return the translation for the current language."""
    return T[key][L]


# ---------------------------------------------------------------------------
# CSS — switches direction based on language
# ---------------------------------------------------------------------------
is_rtl = (L == 'fa')
rtl_css = """
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap');

    /* Apply Vazirmatn font to all readable content */
    .main p, .main li, .main td, .main th,
    .main h1, .main h2, .main h3, .main h4, .main h5,
    .main label, .main .stMarkdown, .main .stText,
    .main [data-testid="stCaptionContainer"],
    .main [data-testid="stAlertContainer"] {
        font-family: 'Vazirmatn', sans-serif !important;
    }
""" if is_rtl else ""

base_css = """
    .stSlider [data-baseweb="slider"] { padding-top: 15px; padding-bottom: 15px; }
    div[data-testid="stExpander"], .stSlider {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00d4ff;
    }

    /* --- Mobile responsiveness --- */
    @media (max-width: 768px) {
        /* Stack all multi-column layouts vertically */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }

        /* Prevent wide content from causing horizontal scroll */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }

        /* Folium maps: full width, shorter height on small screens */
        iframe {
            width: 100% !important;
            height: 350px !important;
        }

        /* Altair charts: allow shrinking */
        [data-testid="stArrowVegaLiteChart"] canvas,
        [data-testid="stArrowVegaLiteChart"] svg {
            max-width: 100% !important;
        }
    }
"""

st.markdown(f"<style>{base_css}{rtl_css}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
FEATURED_IDS = [
    68847, 68873, 68886, 68918, 68981, 68994, 69000, 69010, 69042, 69200,
    69218, 69225, 69265, 69277, 69293, 69304, 69511, 69518, 69540, 69641,
    69688, 69702, 69705,
]
FEATURED_COLOR = "cyan"


# ---------------------------------------------------------------------------
# DATA LOADERS
# ---------------------------------------------------------------------------
@st.cache_data
def load_and_clean_data(file_path):
    df = pd.read_excel(file_path)
    df = df.dropna(subset=['address']).copy()
    df['date_utc'] = pd.to_datetime(df['date_utc'], utc=True)
    df = df.sort_values('date_utc')
    return df


@st.cache_data
def load_memorial_data(file_path):
    df = pd.read_excel(file_path)
    df = df.dropna(subset=['latitude', 'longitude']).copy()
    return df


# ---------------------------------------------------------------------------
# MAP BUILDERS
# ---------------------------------------------------------------------------
def _iran_map(**kwargs):
    return folium.Map(
        location=[32.4279, 53.6880],
        zoom_start=6,
        tiles="cartodbpositron",
        max_bounds=True,
        min_lat=24.0, max_lat=40.0,
        min_lon=43.0, max_lon=64.0,
        min_zoom=5, max_zoom=14,
        **kwargs,
    )


def create_map(df):
    m = _iran_map()
    df = df.dropna(subset=['latitude', 'longitude'])
    color_map = {'1': "blue", '2': "red", '3': "magenta"}

    for _, row in df.iterrows():
        np.random.seed(int(str(row['id'])[-6:]))
        offset = 0.0015
        lat = row['latitude'] + np.random.uniform(-offset, offset)
        lon = row['longitude'] + np.random.uniform(-offset, offset)

        is_featured = row['id'] in FEATURED_IDS
        chants = [c for c in str(row['Label']) if c in ['1', '2', '3']]
        if not chants and not is_featured:
            continue

        fill = FEATURED_COLOR if is_featured else color_map.get(chants[0], "gray")
        folium.CircleMarker(
            location=[lat, lon],
            radius=12 if is_featured else 8,
            color="white" if is_featured else fill,
            fill=True, fill_color=fill, fill_opacity=0.8,
            popup=f"{row['id']}",
            tooltip=f"ID: {row['id']}",
        ).add_to(m)
    return m


def create_violence_timeline_map(filtered_df):
    filtered_df = filtered_df.dropna(subset=['latitude', 'longitude'])
    m = _iran_map()
    color_map = {'4': "yellow", '5': "orange", '6': "orangered", '7': "purple", '8': "black"}

    for _, row in filtered_df.iterrows():
        np.random.seed(int(str(row['id'])[-6:]))
        offset = 0.015
        lat = row['latitude'] + np.random.uniform(-offset, offset)
        lon = row['longitude'] + np.random.uniform(-offset, offset)

        viol_found = [c for c in str(row['Label']) if c in color_map]
        if not viol_found:
            continue

        edge = color_map[viol_found[0]]
        fill = color_map[viol_found[1]] if len(viol_found) >= 2 else edge
        folium.CircleMarker(
            location=[lat, lon],
            radius=10, color=edge, weight=4,
            fill=True, fill_color=fill, fill_opacity=1,
            popup=f"Violence ID: {row['id']}",
            tooltip=f"ID: {row['id']}",
        ).add_to(m)
    return m


def create_casualty_map(df):
    m = _iran_map()
    mc = MarkerCluster(disableClusteringAtZoom=10, spiderfyOnMaxZoom=True).add_to(m)
    for row in df.itertuples():
        folium.CircleMarker(
            location=[row.latitude, row.longitude],
            radius=5, color="black", weight=1,
            fill=True, fill_opacity=0.6,
            tooltip="ID: " + str(row.message_id),
        ).add_to(mc)
    return m


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title(t('main_title'))

try:
    data = load_and_clean_data("final_data.xlsx")

    # --- OVERVIEW ---
    st.divider()
    st.header(t('overview_header'))
    st.write(t('overview_body'))

    # --- HISTOGRAM ---
    st.subheader(t('histogram_subheader'))
    col_a, col_b = st.columns(2)

    with col_a:
        st.write(t('histogram_title'))
        hist_data = data.copy()
        hist_data['just_date'] = pd.to_datetime(hist_data['date_utc'], utc=True, errors='coerce').dt.date
        date_counts = hist_data['just_date'].value_counts().reset_index()
        date_counts.columns = ['Date', 'Count']
        date_counts = date_counts.sort_values('Date')

        chart = (
            alt.Chart(date_counts)
            .mark_bar(color='steelblue')
            .encode(
                x=alt.X('Date:T', title=t('histogram_x'),
                         scale=alt.Scale(domain=['2025-12-20', '2026-01-15'])),
                y=alt.Y('Count:Q', title=t('histogram_y')),
                tooltip=['Date', 'Count'],
            )
            .interactive(bind_y=False)
        )
        st.altair_chart(chart, use_container_width=True)
        st.caption(f"<p style='text-align: center;'>{t('histogram_caption')}</p>", unsafe_allow_html=True)

    with col_b:
        st.write(t('histogram_note'))

    with st.container():
        st.info(t('slider_tip'))

    # --- FEATURED VIDEO TIMELINE ---
    st.subheader(t('featured_timeline_subheader'))
    st.caption(t('featured_timeline_caption'))

    videos_paths_tl = glob.glob('static/*.mp4')
    featured_df = data[data['id'].isin(FEATURED_IDS)].copy()
    featured_df = featured_df.sort_values('date_utc')
    featured_df['id_str'] = featured_df['id'].astype(str)

    tl_selector = alt.selection_point(name="tl_click", fields=['id_str'])

    timeline_chart = (
        alt.Chart(featured_df)
        .mark_point(size=200, filled=True, opacity=0.9)
        .encode(
            x=alt.X(
                'date_utc:T',
                title=None,
                axis=alt.Axis(
                    format='%b %d', labelAngle=-45, labelFontSize=11,
                    tickCount='day', grid=False, labelPadding=6,
                ),
                scale=alt.Scale(padding=20),
            ),
            y=alt.value(20),
            color=alt.condition(tl_selector, alt.value('cyan'), alt.value('steelblue')),
            tooltip=[
                alt.Tooltip('id_str:N', title=t('tl_tooltip_id')),
                alt.Tooltip('date_utc:T', title=t('tl_tooltip_date'), format='%b %d, %Y'),
                alt.Tooltip('address:N', title=t('tl_tooltip_location')),
            ],
        )
        .add_params(tl_selector)
        .properties(height=100)
        .configure_view(strokeWidth=0)
    )

    tl_event = st.altair_chart(timeline_chart, on_select="rerun", use_container_width=True)

    tl_selected = (tl_event.selection or {}).get("tl_click", [])
    if tl_selected:
        tl_id = int(tl_selected[0]['id_str'])
        tl_row = featured_df[featured_df['id'] == tl_id].iloc[0]
        tl_col1, tl_col2 = st.columns([1, 1])
        with tl_col1:
            st.write(f"{t('tl_id_label')} {tl_id}")
            st.write(f"{t('tl_location_label')} {tl_row.get('address', 'N/A')}")
            st.write(f"{t('tl_date_label')} {tl_row['date_utc'].date()}")
            if 'Description' in tl_row and pd.notna(tl_row['Description']):
                st.info(f"{t('tl_desc_label')} {tl_row['Description']}")
        with tl_col2:
            tl_video_match = [p for p in videos_paths_tl if str(tl_id) in p]
            if tl_video_match:
                st.video(tl_video_match[0])
            else:
                st.warning(t('tl_no_video'))

    st.divider()

    # --- SLOGAN MAP ---
    col1, col2 = st.columns([1, 2])
    min_date = data['date_utc'].min().date()
    max_date = data['date_utc'].max().date()

    with col2:
        start_date = datetime.date(2025, 12, 25)
        selected_date = st.slider(t('slider_label'), min_date, max_date, start_date)
        filtered_data = data[data['date_utc'].dt.date <= selected_date]
        map_obj = create_map(filtered_data)
        map_data = st_folium(map_obj, key="main_map")

    with col1:
        st.subheader(t('slogan_map_subheader'))
        st.subheader(t('map_legend'))
        st.markdown(t('legend_slogan'), unsafe_allow_html=True)

        videos_paths = glob.glob('static/*.mp4')
        if map_data and map_data.get("last_object_clicked_tooltip"):
            clicked_id = map_data["last_object_clicked_tooltip"].replace("ID: ", "").strip()
            st.write(f"{t('selected_id')} {clicked_id}")

            if int(clicked_id) in FEATURED_IDS:
                row_data = data[data['id'] == int(clicked_id)].iloc[0]
                st.write(f"{t('location_label')} {row_data.get('address', '')}")
                st.write(f"{t('date_label')} {row_data['date_utc'].date()}")
                if 'Description' in row_data and pd.notna(row_data['Description']):
                    st.info(f"{t('desc_label')} {row_data['Description']}")
                video_match = [p for p in videos_paths if clicked_id in p]
                if video_match:
                    st.video(video_match[0])

    # --- SLOGANS IN NUMBERS ---
    st.divider()
    st.header(t('slogans_numbers_header'))
    st.write(t('slogans_numbers_body'))

    sr = t('slogan_rows')
    individual_counts = {
        sr['l1']: [int(data['Label'].astype(str).str.contains('1').sum())],
        sr['l2']: [int(data['Label'].astype(str).str.contains('2').sum())],
        sr['l3']: [int(data['Label'].astype(str).str.contains('3').sum())],
    }
    individual_counts = pd.DataFrame(individual_counts).T
    individual_counts.columns = [sr['col']]

    _, table_col, _ = st.columns([1, 2, 1])
    with table_col:
        st.write(t('slogan_stats_title'))
        st.table(individual_counts)

    # --- VIOLENCE MAP ---
    st.divider()
    st.header(t('violence_header'))

    violence_data = data[data['Label'].astype(str).str.contains('[45678]')].copy()
    col1_v, col2_v = st.columns([1, 2])

    with col2_v:
        start_date_v = datetime.date(2025, 12, 25)
        v_selected_date = st.slider(t('slider_label'), min_date, max_date, start_date_v, key="v_slider")
        v_filtered = violence_data[violence_data['date_utc'].dt.date <= v_selected_date]
        v_map_data = st_folium(create_violence_timeline_map(v_filtered), use_container_width=True, height=600, key="violence_timeline")

    with col1_v:
        st.subheader(t('violence_details'))
        st.subheader(t('map_legend'))
        st.markdown(t('legend_violence'), unsafe_allow_html=True)

        if v_map_data and v_map_data.get("last_object_clicked_tooltip"):
            v_clicked_id = v_map_data["last_object_clicked_tooltip"].replace("ID: ", "").strip()
            st.write(f"{t('selected_violence_id')} {v_clicked_id}")
            v_row = data[data['id'] == int(v_clicked_id)].iloc[0]
            st.write(f"{t('location_label')} {v_row['address']}")

    # --- CASUALTY MAP ---
    st.divider()
    st.header(t('casualty_header'))
    st.write(t('casualty_body'))
    st.write(t('casualty_updated'))

    memo_data = load_memorial_data("memorial_final_data_27June2026.xlsx")
    col1_c, col2_c = st.columns([1, 2])

    with col2_c:
        c_map_data = st_folium(
            create_casualty_map(memo_data),
            use_container_width=True, height=600,
            key="casualty_map",
            returned_objects=["last_object_clicked_tooltip"],
        )

    with col1_c:
        st.subheader(t('casualty_details'))
        clicked_val = c_map_data.get("last_object_clicked_tooltip")
        if clicked_val:
            clicked_id = str(clicked_val[3:]).strip()
            selected_rows = memo_data[memo_data['message_id'] == int(clicked_id)]
            if not selected_rows.empty:
                c_row = selected_rows.iloc[0]
                st.write(f"### {c_row.get('Name', 'ID: ' + clicked_id)}")
                st.write(f"{t('city_label')} {c_row.get('City', t('unknown'))}")
                image_path = f"static/images/{clicked_id}.jpg"
                if os.path.exists(image_path):
                    st.image(image_path, width=400)

except Exception as e:
    st.error(f"{t('error_msg')} {e}")
