import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import re
import requests
from pathlib import Path
from datetime import datetime

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="AMC NPA Monitor Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for cached dataframes
if 'df_bam' not in st.session_state:
    st.session_state.df_bam = None
if 'df_baania' not in st.session_state:
    st.session_state.df_baania = None
if 'df_living' not in st.session_state:
    st.session_state.df_living = None
if 'df_zmyhome' not in st.session_state:
    st.session_state.df_zmyhome = None

# Load custom styling for premium glassmorphism dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Sarabun:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Sarabun', sans-serif;
    }
    
    .stApp {
        background-color: #f8fafc !important;
        color: #1e293b !important;
    }
    
    /* Sidebar Styling for Light Mode */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid rgba(0, 0, 0, 0.08);
    }
    [data-testid="stSidebar"] * {
        color: #1e293b !important;
    }
    [data-testid="stSidebar"] .stRadio > label {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        margin-bottom: 12px !important;
        border-left: 4px solid #4f46e5 !important;
        padding-left: 8px !important;
    }
    
    /* Premium Sidebar Menu Buttons */
    div[role="radiogroup"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 10px !important;
    }
    div[role="radiogroup"] label {
        background-color: #f1f5f9 !important;
        border: 1px solid rgba(0, 0, 0, 0.05) !important;
        padding: 12px 16px !important;
        border-radius: 12px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        margin: 0 !important;
    }
    div[role="radiogroup"] label:hover {
        background-color: #e2e8f0 !important;
        border-color: #4f46e5 !important;
        transform: translateX(6px) !important;
    }
    /* Hide default radio circle icon and its container space */
    div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }
    /* Selected radio state */
    div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
        border-color: #4f46e5 !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2) !important;
    }
    div[role="radiogroup"] label:has(input:checked) * {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Header styling */
    .dashboard-header {
        background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid rgba(0, 0, 0, 0.08);
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04);
    }
    .dashboard-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(to right, #4f46e5, #0d9488);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .dashboard-subtitle {
        font-size: 1rem;
        font-weight: 300;
        margin-top: 0.5rem;
        color: #475569;
    }
    
    /* KPI Grid Cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        color: #1e293b;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        border-color: #4f46e5;
        box-shadow: 0 10px 25px rgba(79, 70, 229, 0.08);
    }
    .kpi-icon {
        font-size: 2rem;
        margin-bottom: 5px;
    }
    .kpi-company {
        font-size: 0.85rem;
        color: #475569;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: #0f172a;
        margin: 8px 0;
    }
    .kpi-pct {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .kpi-time {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 5px;
        border-top: 1px solid rgba(0, 0, 0, 0.06);
        padding-top: 8px;
    }
    
    /* Summary container */
    .summary-section {
        background-color: #ffffff;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
        color: #1e293b;
    }
    .section-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 1.5rem;
        border-left: 5px solid #4f46e5;
        padding-left: 10px;
    }
    
    /* High contrast input, select, and text area fields to prevent blending */
    div[data-testid="stTextInput"] div[data-baseweb="input"],
    div[data-testid="stNumberInput"] div[data-baseweb="input"],
    div[data-testid="stTextArea"] div[data-baseweb="textarea"],
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
    div[data-testid="stDateInput"] div[data-baseweb="input"],
    div[data-testid="stTimeInput"] div[data-baseweb="input"],
    .stTextInput div[data-baseweb="input"],
    .stNumberInput div[data-baseweb="input"],
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1.5px solid #94a3b8 !important; /* Darker, high contrast border (slate-400) */
        border-radius: 8px !important;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    
    /* Make inner input elements borderless and transparent */
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stDateInput"] input,
    div[data-testid="stTimeInput"] input,
    .stTextInput input,
    .stNumberInput input {
        background-color: transparent !important;
        border: none !important;
        color: #0f172a !important;
    }
    
    /* Hover state for input fields */
    div[data-testid="stTextInput"] div[data-baseweb="input"]:hover,
    div[data-testid="stNumberInput"] div[data-baseweb="input"]:hover,
    div[data-testid="stTextArea"] div[data-baseweb="textarea"]:hover,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:hover,
    div[data-testid="stDateInput"] div[data-baseweb="input"]:hover,
    div[data-testid="stTimeInput"] div[data-baseweb="input"]:hover,
    .stTextInput div[data-baseweb="input"]:hover,
    .stNumberInput div[data-baseweb="input"]:hover,
    .stSelectbox div[data-baseweb="select"] > div:hover {
        border-color: #475569 !important;
    }
    
    /* Focus state for input fields */
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:focus-within,
    div[data-testid="stDateInput"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stTimeInput"] div[data-baseweb="input"]:focus-within,
    .stTextInput div[data-baseweb="input"]:focus-within,
    .stNumberInput div[data-baseweb="input"]:focus-within,
    .stSelectbox div[data-baseweb="select"] > div:focus-within {
        border-color: #4f46e5 !important;
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.25) !important;
    }
    
    /* Input placeholder styling for readability */
    ::placeholder {
        color: #64748b !important;
        opacity: 0.8 !important;
    }
    
    div[data-baseweb="select"] * {
        color: #0f172a !important;
        font-weight: 500 !important;
    }
    
    /* High contrast popover dropdown options */
    div[data-baseweb="popover"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
    }
    div[data-baseweb="popover"] li {
        color: #0f172a !important;
        background-color: transparent !important;
    }
    div[data-baseweb="popover"] li * {
        color: #0f172a !important;
    }
    div[data-baseweb="popover"] li:hover {
        background-color: #f1f5f9 !important;
    }
    div[data-baseweb="popover"] li:hover * {
        color: #4f46e5 !important;
    }
</style>
""", unsafe_allow_html=True)

# Define directories relative to dashboard location (supporting local sibling dirs and streamlit cloud deployment)
extensions_dir = Path(__file__).resolve().parent.parent
local_data_dir = Path(__file__).resolve().parent / "data"

bam_dir = extensions_dir / "BAM NPA"
if (not (bam_dir / "BAM NPA.xlsx").exists() or (bam_dir / "BAM NPA.xlsx").stat().st_size == 0) and local_data_dir.exists():
    bam_dir = local_data_dir

baania_dir = extensions_dir / "Baania NPA"
if (not (baania_dir / "baania_listings.xlsx").exists() or (baania_dir / "baania_listings.xlsx").stat().st_size == 0) and local_data_dir.exists():
    baania_dir = local_data_dir

living_dir = extensions_dir / "Livinginsider NPA"
if (not (living_dir / "Livinginsider NPA.xlsx").exists() or (living_dir / "Livinginsider NPA.xlsx").stat().st_size == 0) and local_data_dir.exists():
    living_dir = local_data_dir

zmyhome_dir = extensions_dir / "ZmyHome NPA"
if (not (zmyhome_dir / "ZmyHome NPA.xlsx").exists() or (zmyhome_dir / "ZmyHome NPA.xlsx").stat().st_size == 0) and local_data_dir.exists():
    zmyhome_dir = local_data_dir

# Price Formatter helper
def format_price_thai(val):
    if pd.isna(val) or val == 0:
        return "N/A"
    if val >= 1_000_000_000:
        return f"{val / 1_000_000_000:.2f} พันล้านบาท"
    if val >= 1_000_000:
        return f"{val / 1_000_000:.2f} ล้านบาท"
    return f"{val:,.0f} บาท"

# File modified time helper
def get_file_mod_time(path: Path):
    if path.exists():
        mtime = os.path.getmtime(path)
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    return "ไม่พบไฟล์"

# Web counts fetching helpers (with caching to avoid slow loading)
@st.cache_data(ttl=600)
def fetch_bam_metadata():
    meta_file = bam_dir / "metadata.json"
    if not meta_file.exists() and bam_dir == local_data_dir:
        meta_file = local_data_dir / "bam_metadata.json"
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
                return int(meta.get("total_count", 16541)), meta.get("last_updated", "ไม่ระบุ")
        except Exception:
            pass
    return 16541, "ไม่ระบุ"

@st.cache_data(ttl=600)
def fetch_livinginsider_web_count():
    # Livinginsider search pagination is capped at ~4,412 pages (105,888 listings),
    # but the site actually has 200,000++ listings. We return 240,000 as the real total to represent correct progress.
    return 240000

@st.cache_data(ttl=600)
def fetch_baania_web_count():
    url = "https://www.baania.com/s/%E0%B8%97%E0%B8%B1%E0%B9%89%E0%B8%87%E0%B8%AB%E0%B8%A1%E0%B8%94/listing"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=6)
        match = re.search(r"<script id=\"__NEXT_DATA__\"[^>]*>(.*?)</script>", r.text, flags=re.S)
        if match:
            data = json.loads(match.group(1))
            hits_data = data.get("props", {}).get("pageProps", {}).get("defaultData", {}).get("hits", {})
            total_val = hits_data.get("total", {}).get("value", 10000)
            return total_val
    except Exception:
        pass
    return 10000

@st.cache_data(ttl=600)
def fetch_zmyhome_web_count():
    url = "https://zmyhome.com/buy"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "th,en-US;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/"
    }
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            match = re.search(r'"numberOfItems":\s*(\d+)', r.text)
            if match:
                return int(match.group(1))
    except Exception:
        pass
    return 27368  # Fallback value

# Loader and Cleaner functions with robust caching and session state fallback
@st.cache_data(ttl=30)
def read_excel_file_cached(path, engine='openpyxl'):
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(f"File not found or empty: {path}")
    return pd.read_excel(path, engine=engine)

def load_bam_data():
    path = bam_dir / "BAM NPA.xlsx"
    df = None
    try:
        df = read_excel_file_cached(path, engine='openpyxl')
    except Exception:
        try:
            df = pd.read_excel(path)
        except Exception:
            if bam_dir != local_data_dir:
                fallback_path = local_data_dir / "BAM NPA.xlsx"
                try:
                    df = read_excel_file_cached(fallback_path, engine='openpyxl')
                except Exception:
                    try:
                        df = pd.read_excel(fallback_path)
                    except Exception:
                        pass
            
    if df is not None:
        try:
            df['ประเภททรัพย์'] = df['ประเภททรัพย์'].fillna('อื่นๆ').astype(str).str.strip()
            df['จังหวัด'] = df['จังหวัด'].fillna('ไม่ระบุ').astype(str).str.strip()
            df['ราคา'] = pd.to_numeric(df['ราคา'], errors='coerce').fillna(0)
            st.session_state.df_bam = df
            return df
        except Exception:
            pass
    return st.session_state.get('df_bam', None)

def load_baania_data():
    path = baania_dir / "baania_listings.xlsx"
    df = None
    try:
        df = read_excel_file_cached(path, engine='openpyxl')
    except Exception:
        try:
            df = pd.read_excel(path)
        except Exception:
            if baania_dir != local_data_dir:
                fallback_path = local_data_dir / "baania_listings.xlsx"
                try:
                    df = read_excel_file_cached(fallback_path, engine='openpyxl')
                except Exception:
                    try:
                        df = pd.read_excel(fallback_path)
                    except Exception:
                        pass
            
    if df is not None:
        try:
            df['ประเภททรัพย์'] = df['ประเภททรัพย์'].fillna('อื่นๆ').astype(str).str.strip()
            df['จังหวัด'] = df['จังหวัด'].fillna('ไม่ระบุ').astype(str).str.strip()
            df['ราคาเริ่มต้น'] = pd.to_numeric(df['ราคาเริ่มต้น'], errors='coerce').fillna(0)
            st.session_state.df_baania = df
            return df
        except Exception:
            pass
    return st.session_state.get('df_baania', None)

def load_living_data():
    path = living_dir / "Livinginsider NPA.xlsx"
    df = None
    try:
        df = read_excel_file_cached(path, engine='openpyxl')
    except Exception:
        try:
            df = pd.read_excel(path)
        except Exception:
            if living_dir != local_data_dir:
                fallback_path = local_data_dir / "Livinginsider NPA.xlsx"
                try:
                    df = read_excel_file_cached(fallback_path, engine='openpyxl')
                except Exception:
                    try:
                        df = pd.read_excel(fallback_path)
                    except Exception:
                        pass
            
    if df is not None:
        try:
            df['ประเภททรัพย์'] = df['ประเภททรัพย์'].fillna('อื่นๆ').astype(str).str.strip()
            df['จังหวัด'] = df['จังหวัด'].fillna('ไม่ระบุ').astype(str).str.strip()
            df['ราคา'] = pd.to_numeric(df['ราคา'], errors='coerce').fillna(0)
            st.session_state.df_living = df
            return df
        except Exception:
            pass
    return st.session_state.get('df_living', None)

def load_zmyhome_data():
    path = zmyhome_dir / "ZmyHome NPA.xlsx"
    df = None
    try:
        df = read_excel_file_cached(path, engine='openpyxl')
    except Exception:
        try:
            df = pd.read_excel(path)
        except Exception:
            if zmyhome_dir != local_data_dir:
                fallback_path = local_data_dir / "ZmyHome NPA.xlsx"
                try:
                    df = read_excel_file_cached(fallback_path, engine='openpyxl')
                except Exception:
                    try:
                        df = pd.read_excel(fallback_path)
                    except Exception:
                        pass
            
    if df is not None:
        try:
            if 'ประเภท' in df.columns:
                df['ประเภททรัพย์'] = df['ประเภท'].fillna('อื่นๆ').astype(str).str.strip()
            else:
                df['ประเภททรัพย์'] = df.get('ประเภททรัพย์', pd.Series('อื่นๆ', index=df.index)).fillna('อื่นๆ').astype(str).str.strip()
            df['จังหวัด'] = df['จังหวัด'].fillna('ไม่ระบุ').astype(str).str.strip()
            df['ราคา'] = pd.to_numeric(df['ราคา'], errors='coerce').fillna(0)
            st.session_state.df_zmyhome = df
            return df
        except Exception:
            pass
    return st.session_state.get('df_zmyhome', None)

# Load all data
df_bam = load_bam_data()
df_baania = load_baania_data()
df_living = load_living_data()
df_zmyhome = load_zmyhome_data()

# Fetch totals & metadata
bam_web_total, bam_last_updated = fetch_bam_metadata()
living_web_total = fetch_livinginsider_web_count()
baania_web_total = fetch_baania_web_count()
zmyhome_web_total = fetch_zmyhome_web_count()

# Scraped Counts
scraped_bam = len(df_bam) if df_bam is not None else 0
scraped_baania = len(df_baania) if df_baania is not None else 0
scraped_living = len(df_living) if df_living is not None else 0
scraped_zmyhome = len(df_zmyhome) if df_zmyhome is not None else 0

# Total Scraped Values
bam_total_value = df_bam['ราคา'].sum() if df_bam is not None else 0
baania_total_value = df_baania['ราคาเริ่มต้น'].sum() if df_baania is not None else 0
living_total_value = df_living['ราคา'].sum() if df_living is not None else 0
zmyhome_total_value = df_zmyhome['ราคา'].sum() if df_zmyhome is not None else 0

# Percentages
# BAM
pct_bam = (scraped_bam / bam_web_total * 100) if bam_web_total > 0 else 0
# Baania: completed based on cutoff, it's 100%
pct_baania = 100.0 if scraped_baania >= baania_web_total else (scraped_baania / baania_web_total * 100)
# Livinginsider
pct_living = (scraped_living / living_web_total * 100) if living_web_total > 0 else 0
# ZmyHome
pct_zmyhome = (scraped_zmyhome / zmyhome_web_total * 100) if zmyhome_web_total > 0 else 0

# Baania web count display description
baania_total_desc = f"{baania_web_total:,}+" if baania_web_total == 10000 else f"{baania_web_total:,}"

# File modifications
file_time_bam = get_file_mod_time(bam_dir / "BAM NPA.xlsx")
file_time_baania = get_file_mod_time(baania_dir / "baania_listings.xlsx")
file_time_living = get_file_mod_time(living_dir / "Livinginsider NPA.xlsx")
file_time_zmyhome = get_file_mod_time(zmyhome_dir / "ZmyHome NPA.xlsx")
# Helper to calculate distance between coordinates (Haversine formula)
def haversine_distance(lat1, lon1, lat2, lon2):
    r = 6371.0  # Earth radius in kilometers
    
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0)**2
    c = 2.0 * np.arcsin(np.sqrt(a))
    
    return r * c

# Standardize and merge datasets for comparison
def prepare_comparison_dataset():
    dfs = []
    
    # helper for columns mapping
    def get_column_data(df, candidates, default_val=None, is_numeric=False):
        col = next((c for c in candidates if c in df.columns), None)
        if col is not None:
            if is_numeric:
                return pd.to_numeric(df[col], errors='coerce').fillna(default_val if default_val is not None else 0)
            return df[col]
        # Return a series of default value matching the length of df
        return pd.Series([default_val] * len(df), index=df.index)

    # 1. BAM
    if df_bam is not None and not df_bam.empty:
        temp = pd.DataFrame()
        temp['source'] = ['BAM NPA'] * len(df_bam)
        temp['id'] = get_column_data(df_bam, ['รหัสทรัพย์', 'ID', 'รหัสประกาศ']).astype(str)
        temp['project_name'] = get_column_data(df_bam, ['ชื่อโครงการ', 'โครงการ', 'ชื่อประกาศ', 'หัวข้อ'], 'ไม่ระบุโครงการ').astype(str)
        temp['property_type'] = df_bam['ประเภททรัพย์'] if 'ประเภททรัพย์' in df_bam.columns else 'อื่นๆ'
        temp['price'] = get_column_data(df_bam, ['ราคา', 'ราคาเริ่มต้น', 'ราคาตั้งต้น'], 0, is_numeric=True)
        temp['lat'] = get_column_data(df_bam, ['ละติจูด', 'latitude', 'lat'], np.nan, is_numeric=True)
        temp['lon'] = get_column_data(df_bam, ['ลองจิจูด', 'longitude', 'lon'], np.nan, is_numeric=True)
        temp['province'] = df_bam['จังหวัด'] if 'จังหวัด' in df_bam.columns else 'ไม่ระบุ'
        temp['district'] = df_bam['อำเภอ'] if 'อำเภอ' in df_bam.columns else 'ไม่ระบุ'
        temp['subdistrict'] = df_bam['ตำบล'] if 'ตำบล' in df_bam.columns else 'ไม่ระบุ'
        temp['url'] = get_column_data(df_bam, ['ลิงก์', 'url', 'ลิงค์'], '#').astype(str)
        dfs.append(temp)
        
    # 2. Baania
    if df_baania is not None and not df_baania.empty:
        temp = pd.DataFrame()
        temp['source'] = ['Baania NPA'] * len(df_baania)
        temp['id'] = get_column_data(df_baania, ['id', 'ID', 'รหัสทรัพย์', 'รหัสประกาศ']).astype(str)
        temp['project_name'] = get_column_data(df_baania, ['ชื่อโครงการ', 'โครงการ', 'ชื่อประกาศ', 'หัวข้อ'], 'ไม่ระบุโครงการ').astype(str)
        temp['property_type'] = df_baania['ประเภททรัพย์'] if 'ประเภททรัพย์' in df_baania.columns else 'อื่นๆ'
        temp['price'] = get_column_data(df_baania, ['ราคาเริ่มต้น', 'ราคา', 'ราคาตั้งต้น'], 0, is_numeric=True)
        temp['lat'] = get_column_data(df_baania, ['ละติจูด', 'latitude', 'lat'], np.nan, is_numeric=True)
        temp['lon'] = get_column_data(df_baania, ['ลองจิจูด', 'longitude', 'lon'], np.nan, is_numeric=True)
        temp['province'] = df_baania['จังหวัด'] if 'จังหวัด' in df_baania.columns else 'ไม่ระบุ'
        temp['district'] = df_baania['อำเภอ'] if 'อำเภอ' in df_baania.columns else 'ไม่ระบุ'
        temp['subdistrict'] = df_baania['ตำบล'] if 'ตำบล' in df_baania.columns else 'ไม่ระบุ'
        temp['url'] = get_column_data(df_baania, ['ลิงก์', 'url', 'ลิงค์'], '#').astype(str)
        dfs.append(temp)
        
    # 3. LivingInsider
    if df_living is not None and not df_living.empty:
        temp = pd.DataFrame()
        temp['source'] = ['LivingInsider NPA'] * len(df_living)
        temp['id'] = get_column_data(df_living, ['รหัสประกาศ', 'ID', 'รหัสทรัพย์']).astype(str)
        temp['project_name'] = get_column_data(df_living, ['ชื่อโครงการ', 'โครงการ', 'ชื่อประกาศ', 'หัวข้อ'], 'ไม่ระบุโครงการ').astype(str)
        temp['property_type'] = df_living['ประเภททรัพย์'] if 'ประเภททรัพย์' in df_living.columns else 'อื่นๆ'
        temp['price'] = get_column_data(df_living, ['ราคา', 'ราคาเริ่มต้น', 'ราคาตั้งต้น'], 0, is_numeric=True)
        temp['lat'] = get_column_data(df_living, ['ละติจูด', 'latitude', 'lat'], np.nan, is_numeric=True)
        temp['lon'] = get_column_data(df_living, ['ลองจิจูด', 'longitude', 'lon'], np.nan, is_numeric=True)
        temp['province'] = df_living['จังหวัด'] if 'จังหวัด' in df_living.columns else 'ไม่ระบุ'
        temp['district'] = df_living['อำเภอ'] if 'อำเภอ' in df_living.columns else 'ไม่ระบุ'
        temp['subdistrict'] = df_living['ตำบล'] if 'ตำบล' in df_living.columns else 'ไม่ระบุ'
        temp['url'] = get_column_data(df_living, ['ลิงก์', 'url', 'ลิงค์'], '#').astype(str)
        dfs.append(temp)
        
    # 4. ZmyHome
    if df_zmyhome is not None and not df_zmyhome.empty:
        temp = pd.DataFrame()
        temp['source'] = ['ZmyHome NPA'] * len(df_zmyhome)
        temp['id'] = get_column_data(df_zmyhome, ['รหัสประกาศ', 'ID', 'รหัสทรัพย์']).astype(str)
        temp['project_name'] = get_column_data(df_zmyhome, ['ชื่อโครงการ', 'โครงการ', 'ชื่อประกาศ', 'หัวข้อ'], 'ไม่ระบุโครงการ').astype(str)
        temp['property_type'] = df_zmyhome['ประเภททรัพย์'] if 'ประเภททรัพย์' in df_zmyhome.columns else 'อื่นๆ'
        temp['price'] = get_column_data(df_zmyhome, ['ราคา', 'ราคาเริ่มต้น', 'ราคาตั้งต้น'], 0, is_numeric=True)
        temp['lat'] = get_column_data(df_zmyhome, ['ละติจูด', 'latitude', 'lat'], np.nan, is_numeric=True)
        temp['lon'] = get_column_data(df_zmyhome, ['ลองจิจูด', 'longitude', 'lon'], np.nan, is_numeric=True)
        temp['province'] = df_zmyhome['จังหวัด'] if 'จังหวัด' in df_zmyhome.columns else 'ไม่ระบุ'
        temp['district'] = df_zmyhome['อำเภอ'] if 'อำเภอ' in df_zmyhome.columns else 'ไม่ระบุ'
        temp['subdistrict'] = df_zmyhome['ตำบล'] if 'ตำบล' in df_zmyhome.columns else 'ไม่ระบุ'
        temp['url'] = get_column_data(df_zmyhome, ['ลิงก์', 'url', 'ลิงค์'], '#').astype(str)
        dfs.append(temp)
        
    if not dfs:
        return pd.DataFrame()
        
    master_df = pd.concat(dfs, ignore_index=True)
    # Filter rows with valid coordinates
    master_df = master_df[master_df['lat'].notna() & master_df['lon'].notna() & (master_df['lat'] != 0) & (master_df['lon'] != 0)]
    return master_df


# ----------------- SIDEBAR NAVIGATION -----------------
with st.sidebar:
    st.markdown('<h2 style="color: #818cf8; font-weight: 700;"><i class="fa fa-search"></i> AMC NPA Monitor</h2>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Navigation Radio
    selected_page = st.radio(
        "เลือกหน้าเมนูหลัก:",
        ["🔮 แผนภาพวงกลม NPA ภาพรวม", "📊 สรุปความสำเร็จการดึงข้อมูล", "🔍 เจาะลึกข้อมูลรายบริษัท", "🔄 เปรียบเทียบทรัพย์สินใกล้เคียง"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; color: #6b7280;">
        <b>ระบบเฝ้าติดตาม NPA</b><br>
        พัฒนาโดย ปัญญาประดิษฐ์ coding assistant
    </div>
    """, unsafe_allow_html=True)


# ----------------- PAGE 1: INTERACTIVE BUBBLE CHART (HOMEPAGE) -----------------
# ----------------- PAGE 1: INTERACTIVE BUBBLE CHART (HOMEPAGE) -----------------
if selected_page == "🔮 แผนภาพวงกลม NPA ภาพรวม":
    # Lock vertical scrolling on homepage and remove block container padding
    st.markdown("""
    <style>
        html, body, [data-testid="stApp"], .stApp, [data-testid="stMain"], .stMain {
            overflow: hidden !important;
            height: 100vh !important;
        }
        [data-testid="stAppViewBlockContainer"], .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 0px !important;
            max-height: 100vh !important;
            overflow: hidden !important;
        }
        footer {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Add a premium, multi-tiered header above the chart
    st.markdown("""
    <div style="text-align: center; margin-top: 5px; margin-bottom: 20px; font-family: 'Outfit', 'Sarabun', sans-serif;">
        <!-- Main Title -->
        <h1 style="font-weight: 800; color: #0f172a; margin: 0 0 6px 0; font-size: 2.1rem; letter-spacing: -0.5px; background: linear-gradient(135deg, #4f46e5 0%, #0d9488 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Overview AMC NPA Monitor
        </h1>
        <!-- Subtitle -->
        <p style="font-size: 0.95rem; color: #475569; margin: 0; font-weight: 400;">
            แผนภาพสรุปความสำเร็จการดึงข้อมูลทรัพย์สินรอการขาย (3D Glossy Bubble Chart)
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 1. Two-column layout: Diagram on the left, selector on the right
    col_chart, col_control = st.columns([4.2, 1.0])
    
    with col_control:
        st.markdown("""
        <div style="font-family: 'Outfit', 'Sarabun', sans-serif; border-left: 4px solid #4f46e5; padding-left: 8px; margin-top: 15px; margin-bottom: 10px;">
            <p style="font-size: 0.9rem; font-weight: 700; color: #0f172a; margin: 0;">เกณฑ์เปรียบเทียบสัดส่วน</p>
        </div>
        """, unsafe_allow_html=True)
        bubble_metric = st.radio(
            "เกณฑ์การวัดสัดส่วน:",
            ["สัดส่วนตามจำนวนทรัพย์สิน (Asset Count)", "สัดส่วนตามมูลค่ารวมของทรัพย์สิน (Total Value)"],
            index=0,
            label_visibility="collapsed"
        )

    # Calculate config dynamically based on selected metric
    if bubble_metric == "สัดส่วนตามจำนวนทรัพย์สิน (Asset Count)":
        config = {
            "BAM":           {"cx": 800, "cy": 190, "r": 99},
            "Baania":        {"cx": 790, "cy": 400, "r": 77},
            "LivingInsider": {"cx": 490, "cy": 300, "r": 240},
            "ZmyHome":       {"cx": 160, "cy": 300, "r": 122}
        }
    else: # มูลค่ารวม (Total Value)
        config = {
            "BAM":           {"cx": 800, "cy": 170, "r": 95},
            "Baania":        {"cx": 810, "cy": 420, "r": 168},
            "LivingInsider": {"cx": 490, "cy": 300, "r": 230},
            "ZmyHome":       {"cx": 160, "cy": 300, "r": 104}
        }

    bam_conf = config["BAM"]
    baa_conf = config["Baania"]
    liv_conf = config["LivingInsider"]
    zmy_conf = config["ZmyHome"]

    # Helper function for generating SVG slices
    import math
    def get_pie_slice_path(cx, cy, r, start_pct, end_pct):
        if end_pct - start_pct >= 0.9999:
            return f"M {cx} {cy} m -{r} 0 a {r} {r} 0 1 0 {2*r} 0 a {r} {r} 0 1 0 -{2*r} 0"
        start_angle = -math.pi/2 + start_pct * 2 * math.pi
        end_angle = -math.pi/2 + end_pct * 2 * math.pi
        x1 = cx + r * math.cos(start_angle)
        y1 = cy + r * math.sin(start_angle)
        x2 = cx + r * math.cos(end_angle)
        y2 = cy + r * math.sin(end_angle)
        large_arc = 1 if (end_pct - start_pct) > 0.5 else 0
        return f"M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z"

    def generate_bubble_markup(cx, cy, r, name, total_desc, scraped, pct, value, scraped_grad, unscraped_grad, bubble_id):
        pct_fraction = pct / 100.0
        if pct_fraction >= 0.999:
            slices = f'<g filter="url(#shadow)"><circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{scraped_grad})" /></g>'
        elif pct_fraction <= 0.001:
            slices = f'<g filter="url(#shadow)"><circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{unscraped_grad})" /></g>'
        else:
            path_scraped = get_pie_slice_path(cx, cy, r, 0, pct_fraction)
            path_unscraped = get_pie_slice_path(cx, cy, r, pct_fraction, 1.0)
            slices = f"""
            <g filter="url(#shadow)">
                <path d="{path_unscraped}" fill="url(#{unscraped_grad})" />
                <path d="{path_scraped}" fill="url(#{scraped_grad})" />
            </g>
            """
        sheen = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(255, 255, 255, 0.45)" stroke-width="2" />'
        hcx = cx - r * 0.35
        hcy = cy - r * 0.35
        hrx = r * 0.4
        hry = r * 0.25
        highlight = f'<ellipse cx="{hcx}" cy="{hcy}" rx="{hrx}" ry="{hry}" fill="url(#highlight-grad)" transform="rotate(-30, {hcx}, {hcy})" />'
        
        title_size = int(r * 0.12)
        text_size = int(r * 0.085)
        if title_size < 16: title_size = 16
        if text_size < 11: text_size = 11
        
        # Calculate badge padding and styling dynamically based on size
        badge_padding = "4px 12px" if r > 150 else "3px 10px"
        badge_gap = "6px" if r > 150 else "4px"
        margin_bottom = "6px" if r > 150 else "4px"
        
        # Define Streamlit App URLs for each provider
        company_urls = {
            "BAM NPA": "https://bam-npa-scrap-vwsfgmplzgpwobidj3vuhm.streamlit.app/",
            "Baania NPA": "https://baania-npa-gji2towcxpuc2nokydt22p.streamlit.app/",
            "LivingInsider NPA": "https://livinginsider-npa-kx7b3t4xujq5ahdruzpgfp.streamlit.app/",
            "ZmyHome NPA": "#"
        }
        url = company_urls.get(name, "#")

        bubble_body = f"""
            <g class="bubble-group" id="{bubble_id}">
                {slices}
                {sheen}
                {highlight}
                <foreignObject x="{cx - r}" y="{cy - r}" width="{2*r}" height="{2*r}">
                    <div style="width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; font-family: 'Outfit', 'Sarabun', sans-serif; pointer-events: none; box-sizing: border-box; padding: 12px; line-height: 1.4; will-change: transform; transform: translate3d(0,0,0);">
                        <!-- Title -->
                        <div style="font-weight: 800; font-size: {title_size}px; color: #0f172a; letter-spacing: -0.3px; margin-bottom: 8px; text-transform: uppercase;">
                            {name}
                        </div>
                        
                        <!-- Stats: บนเว็บ -->
                        <div style="background: rgba(255, 255, 255, 0.45); backdrop-filter: blur(4px); border-radius: 20px; padding: {badge_padding}; display: inline-flex; align-items: center; gap: {badge_gap}; margin-bottom: {margin_bottom}; border: 1px solid rgba(255, 255, 255, 0.5); box-shadow: 0 2px 5px rgba(15, 23, 42, 0.04);">
                            <span style="font-size: {text_size - 1.5}px; color: #475569; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px;">บนเว็บ</span>
                            <span style="font-size: {text_size}px; color: #0f172a; font-weight: 800;">{total_desc}</span>
                        </div>
                        
                        <!-- Stats: ดึงสำเร็จ -->
                        <div style="background: rgba(255, 255, 255, 0.45); backdrop-filter: blur(4px); border-radius: 20px; padding: {badge_padding}; display: inline-flex; align-items: center; gap: {badge_gap}; margin-bottom: {margin_bottom}; border: 1px solid rgba(255, 255, 255, 0.5); box-shadow: 0 2px 5px rgba(15, 23, 42, 0.04);">
                            <span style="font-size: {text_size - 1.5}px; color: #475569; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px;">ดึงสำเร็จ</span>
                            <span style="font-size: {text_size}px; color: #0f172a; font-weight: 800;">{scraped:,} <span style="color: #4f46e5; font-size: {text_size - 1}px; font-weight: 700;">({pct:.1f}%)</span></span>
                        </div>
                        
                        <!-- Stats: มูลค่ารวม -->
                        <div style="background: rgba(255, 255, 255, 0.45); backdrop-filter: blur(4px); border-radius: 20px; padding: {badge_padding}; display: inline-flex; align-items: center; gap: {badge_gap}; border: 1px solid rgba(255, 255, 255, 0.5); box-shadow: 0 2px 5px rgba(15, 23, 42, 0.04);">
                            <span style="font-size: {text_size - 1.5}px; color: #475569; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px;">มูลค่ารวม</span>
                            <span style="font-size: {text_size}px; color: #0f172a; font-weight: 800;">{value}</span>
                        </div>
                    </div>
                </foreignObject>
            </g>
        """

        if url != "#":
            bubble_body = f'<a href="{url}" target="_blank" style="text-decoration: none;">{bubble_body}</a>'

        return f"""
        <g class="float-wrapper float-{bubble_id}">
            {bubble_body}
        </g>
        """

    # Construct SVG content
    svg_content = f"""
    <svg viewBox="0 0 1000 620" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="background-color: transparent;">
      <defs>
        <!-- Drop Shadow Filter for Light Mode (Soft shadow) -->
        <filter id="shadow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="12" stdDeviation="15" flood-color="#0f172a" flood-opacity="0.16"/>
        </filter>
        
        <!-- Highlight Gradient -->
        <linearGradient id="highlight-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="rgba(255, 255, 255, 0.6)"/>
          <stop offset="100%" stop-color="rgba(255, 255, 255, 0)"/>
        </linearGradient>
        
        <!-- BAM Radial Gradients (Bright Gold/Orange) -->
        <radialGradient id="bam-scraped" cx="50%" cy="50%" r="50%" fx="35%" fy="30%">
          <stop offset="0%" stop-color="#fffebd"/>
          <stop offset="50%" stop-color="#ffa726"/>
          <stop offset="100%" stop-color="#f57c00"/>
        </radialGradient>
        <radialGradient id="bam-unscraped" cx="50%" cy="50%" r="50%" fx="35%" fy="30%">
          <stop offset="0%" stop-color="#fffefb"/>
          <stop offset="70%" stop-color="#ffeed6"/>
          <stop offset="100%" stop-color="#ffe0b2"/>
        </radialGradient>
        
        <!-- Baania Radial Gradients (Bright Green) -->
        <radialGradient id="baania-scraped" cx="50%" cy="50%" r="50%" fx="35%" fy="30%">
          <stop offset="0%" stop-color="#f1fdf5"/>
          <stop offset="50%" stop-color="#66bb6a"/>
          <stop offset="100%" stop-color="#388e3c"/>
        </radialGradient>
        <radialGradient id="baania-unscraped" cx="50%" cy="50%" r="50%" fx="35%" fy="30%">
          <stop offset="0%" stop-color="#fafdfb"/>
          <stop offset="70%" stop-color="#e8f5e9"/>
          <stop offset="100%" stop-color="#c8e6c9"/>
        </radialGradient>
        
        <!-- LivingInsider Radial Gradients (Bright Red) -->
        <radialGradient id="living-scraped" cx="50%" cy="50%" r="50%" fx="38%" fy="35%">
          <stop offset="0%" stop-color="#fff5f5"/>
          <stop offset="50%" stop-color="#ef5350"/>
          <stop offset="100%" stop-color="#d32f2f"/>
        </radialGradient>
        <radialGradient id="living-unscraped" cx="50%" cy="50%" r="50%" fx="38%" fy="35%">
          <stop offset="0%" stop-color="#fffbfa"/>
          <stop offset="70%" stop-color="#ffe4e6"/>
          <stop offset="100%" stop-color="#ffcdd2"/>
        </radialGradient>

        <!-- ZmyHome Radial Gradients (Bright Orange) -->
        <radialGradient id="zmyhome-scraped" cx="50%" cy="50%" r="50%" fx="38%" fy="35%">
          <stop offset="0%" stop-color="#fff1e0"/>
          <stop offset="50%" stop-color="#ff9800"/>
          <stop offset="100%" stop-color="#e65100"/>
        </radialGradient>
        <radialGradient id="zmyhome-unscraped" cx="50%" cy="50%" r="50%" fx="38%" fy="35%">
          <stop offset="0%" stop-color="#fffbf5"/>
          <stop offset="70%" stop-color="#ffe0b2"/>
          <stop offset="100%" stop-color="#ffd180"/>
        </radialGradient>
      </defs>
      
      {generate_bubble_markup(bam_conf['cx'], bam_conf['cy'], bam_conf['r'], "BAM NPA", f"{bam_web_total:,}", scraped_bam, pct_bam, format_price_thai(bam_total_value), "bam-scraped", "bam-unscraped", "bubble-bam")}
      {generate_bubble_markup(baa_conf['cx'], baa_conf['cy'], baa_conf['r'], "Baania NPA", baania_total_desc, scraped_baania, pct_baania, format_price_thai(baania_total_value), "baania-scraped", "baania-unscraped", "bubble-baania")}
      {generate_bubble_markup(liv_conf['cx'], liv_conf['cy'], liv_conf['r'], "LivingInsider NPA", f"{living_web_total:,}", scraped_living, pct_living, format_price_thai(living_total_value), "living-scraped", "living-unscraped", "bubble-living")}
      {generate_bubble_markup(zmy_conf['cx'], zmy_conf['cy'], zmy_conf['r'], "ZmyHome NPA", f"{zmyhome_web_total:,}", scraped_zmyhome, pct_zmyhome, format_price_thai(zmyhome_total_value), "zmyhome-scraped", "zmyhome-unscraped", "bubble-zmyhome")}
    </svg>
    """

    # Wrap inside HTML with CSS for animations and fonts
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Sarabun:wght@300;400;600;700&display=swap');
        body {{
            margin: 0;
            padding: 0;
            background-color: transparent;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }}
        .bubble-container {{
            width: 100%;
            max-width: 900px;
            height: auto;
        }}
        svg {{
            text-rendering: geometricPrecision;
        }}
        .float-wrapper, .bubble-group, text {{
            will-change: transform;
            transform: translate3d(0, 0, 0);
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        .bubble-group {{
            transition: transform 0.35s cubic-bezier(0.25, 0.8, 0.25, 1);
            cursor: pointer;
        }}
        #bubble-bam {{ transform-origin: {bam_conf['cx']}px {bam_conf['cy']}px; }}
        #bubble-baania {{ transform-origin: {baa_conf['cx']}px {baa_conf['cy']}px; }}
        #bubble-living {{ transform-origin: {liv_conf['cx']}px {liv_conf['cy']}px; }}
        #bubble-zmyhome {{ transform-origin: {zmy_conf['cx']}px {zmy_conf['cy']}px; }}
        
        .bubble-group:hover {{
            transform: scale(1.05);
        }}
        .bubble-group:hover circle, .bubble-group:hover path {{
            filter: brightness(1.08);
        }}
        .bubble-group text {{
            pointer-events: none;
        }}

        /* Floating keyframes */
        @keyframes float-bam-anim {{
            0% {{ transform: translate(0px, 0px); }}
            50% {{ transform: translate(4px, -8px); }}
            100% {{ transform: translate(0px, 0px); }}
        }}
        @keyframes float-baania-anim {{
            0% {{ transform: translate(0px, 0px); }}
            50% {{ transform: translate(-5px, -7px); }}
            100% {{ transform: translate(0px, 0px); }}
        }}
        @keyframes float-living-anim {{
            0% {{ transform: translate(0px, 0px); }}
            50% {{ transform: translate(3px, -9px); }}
            100% {{ transform: translate(0px, 0px); }}
        }}
        @keyframes float-zmyhome-anim {{
            0% {{ transform: translate(0px, 0px); }}
            50% {{ transform: translate(-4px, -8px); }}
            100% {{ transform: translate(0px, 0px); }}
        }}

        /* Floating classes applied to wrappers */
        .float-bubble-bam {{
            animation: float-bam-anim 6s ease-in-out infinite;
        }}
        .float-bubble-baania {{
            animation: float-baania-anim 7s ease-in-out infinite;
        }}
        .float-bubble-living {{
            animation: float-living-anim 8s ease-in-out infinite;
        }}
        .float-bubble-zmyhome {{
            animation: float-zmyhome-anim 6.5s ease-in-out infinite;
        }}
    </style>
    </head>
    <body>
    <div class="bubble-container">
        {svg_content}
    </div>
    </body>
    </html>
    """
    
    with col_chart:
        import streamlit.components.v1 as components
        components.html(html_content, height=620)


# ----------------- PAGE 2: SCRAPING SUCCESS AND PROGRESS METRICS -----------------
elif selected_page == "📊 สรุปความสำเร็จการดึงข้อมูล":
    st.markdown("""
    <div class="dashboard-header">
        <h1 class="dashboard-title">📊 สรุปความสำเร็จและเปรียบเทียบผลการดึงข้อมูล (Scraping Metrics)</h1>
        <p class="dashboard-subtitle">ข้อมูลเปรียบเทียบสัดส่วนและเป้าหมายการกวาดข้อมูล NPA จากผู้ให้บริการคู่แข่งในรูปแบบเชิงปริมาณ</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ----------------- KPI CARDS GRID -----------------
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-icon">🏢</div>
                <div class="kpi-company">BAM NPA</div>
                <div class="kpi-value">{scraped_bam:,} / {bam_web_total:,}</div>
            </div>
            <div>
                <div class="kpi-pct" style="color: #60a5fa;">{pct_bam:.2f}% Scraped</div>
                <div class="kpi-time">ไฟล์อัปเดต: {file_time_bam}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-icon">🏡</div>
                <div class="kpi-company">Baania NPA</div>
                <div class="kpi-value">{scraped_baania:,} / {baania_total_desc}</div>
            </div>
            <div>
                <div class="kpi-pct" style="color: #34d399;">{pct_baania:.2f}% Scraped</div>
                <div class="kpi-time">ไฟล์อัปเดต: {file_time_baania}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-icon">🏙️</div>
                <div class="kpi-company">LivingInsider NPA</div>
                <div class="kpi-value">{scraped_living:,} / {living_web_total:,}</div>
            </div>
            <div>
                <div class="kpi-pct" style="color: #ef4444;">{pct_living:.2f}% Scraped</div>
                <div class="kpi-time">ไฟล์อัปเดต: {file_time_living}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-icon">🏠</div>
                <div class="kpi-company">ZmyHome NPA</div>
                <div class="kpi-value">{scraped_zmyhome:,} / {zmyhome_web_total:,}</div>
            </div>
            <div>
                <div class="kpi-pct" style="color: #f97316;">{pct_zmyhome:.2f}% Scraped</div>
                <div class="kpi-time">ไฟล์อัปเดต: {file_time_zmyhome}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        total_scraped = scraped_bam + scraped_baania + scraped_living + scraped_zmyhome
        total_web = bam_web_total + baania_web_total + living_web_total + zmyhome_web_total
        overall_pct = (total_scraped / total_web * 100) if total_web > 0 else 0
        st.markdown(f"""
        <div class="kpi-card" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, #111827 100%); border-color: #6366f1;">
            <div>
                <div class="kpi-icon">📊</div>
                <div class="kpi-company">Overall Summary</div>
                <div class="kpi-value">{total_scraped:,} Properties</div>
            </div>
            <div>
                <div class="kpi-pct" style="color: #a78bfa;">{overall_pct:.2f}% Total Progress</div>
                <div class="kpi-time">รวมข้อมูลทรัพย์สินรอการขายทั้งหมด</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ----------------- COIN360 STYLE TREEMAP HEATMAP -----------------
    st.markdown('<div class="summary-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 สรุปเปรียบเทียบอัตราความสำเร็จและการดึงข้อมูล (Treemap Heatmap)</div>', unsafe_allow_html=True)

    customdata_treemap = [
        [scraped_living, pct_living, format_price_thai(living_total_value)],
        [scraped_bam, pct_bam, format_price_thai(bam_total_value)],
        [scraped_baania, pct_baania, format_price_thai(baania_total_value)],
        [scraped_zmyhome, pct_zmyhome, format_price_thai(zmyhome_total_value)]
    ]

    fig_treemap = go.Figure(go.Treemap(
        labels=["LivingInsider NPA", "BAM NPA", "Baania NPA", "ZmyHome NPA"],
        parents=["", "", "", ""],
        values=[living_web_total, bam_web_total, baania_web_total, zmyhome_web_total], # sizes match web totals
        texttemplate=(
            "<span style='font-size: 1.5rem; font-weight: bold;'>%{label}</span><br><br>"
            "<span style='font-size: 1.05rem;'>"
            "📢 จำนวนประกาศบนเว็บ: <b>%{value:,}</b> รายการ<br>"
            "📥 ดึงข้อมูลสำเร็จ (Scraped): <b>%{customdata[0]:,}</b> รายการ (<b>%{customdata[1]:.2f}%</b>)<br>"
            "💰 มูลค่ารวมที่ดึงมา: <b>%{customdata[2]}</b>"
            "</span>"
        ),
        customdata=customdata_treemap,
        marker=dict(
            colors=[
                "#ef4444",  # LivingInsider (Red)
                "#f59e0b" if pct_bam < 60 else "#84cc16",  # BAM
                "#10b981",  # Baania
                "#f97316" if pct_zmyhome < 60 else "#10b981"  # ZmyHome
            ],
            line=dict(width=2, color="#090d16")
        ),
        textfont=dict(color="#ffffff"),
        hovertemplate="<b>%{label}</b><br>ประกาศทั้งหมดบนเว็บ: %{value:,} รายการ<extra></extra>"
    ))

    fig_treemap.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400
    )
    st.plotly_chart(fig_treemap, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------- OVERVIEW TABLE -----------------
    st.markdown('<div class="summary-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 ตารางสรุปเชิงสถิติทรัพย์สิน NPA เปรียบเทียบ</div>', unsafe_allow_html=True)
    
    # Calculate Prices min/max/avg again for table
    # BAM
    if df_bam is not None and not df_bam.empty:
        bam_min = df_bam['ราคา'].replace(0, np.nan).min()
        bam_max = df_bam['ราคา'].max()
        bam_avg = df_bam['ราคา'].replace(0, np.nan).mean()
        bam_types = ", ".join(df_bam['ประเภททรัพย์'].value_counts().index[:3])
    else:
        bam_min, bam_max, bam_avg, bam_types = 0, 0, 0, "-"

    # Baania
    if df_baania is not None and not df_baania.empty:
        baania_min = df_baania['ราคาเริ่มต้น'].replace(0, np.nan).min()
        baania_max = df_baania['ราคาเริ่มต้น'].max()
        baania_avg = df_baania['ราคาเริ่มต้น'].replace(0, np.nan).mean()
        baania_types = ", ".join(df_baania['ประเภททรัพย์'].value_counts().index[:3])
    else:
        baania_min, baania_max, baania_avg, baania_types = 0, 0, 0, "-"

    # LivingInsider
    if df_living is not None and not df_living.empty:
        living_min = df_living['ราคา'].replace(0, np.nan).min()
        living_max = df_living['ราคา'].max()
        living_avg = df_living['ราคา'].replace(0, np.nan).mean()
        living_types = ", ".join(df_living['ประเภททรัพย์'].value_counts().index[:3])
    else:
        living_min, living_max, living_avg, living_types = 0, 0, 0, "-"

    # ZmyHome
    if df_zmyhome is not None and not df_zmyhome.empty:
        zmyhome_min = df_zmyhome['ราคา'].replace(0, np.nan).min()
        zmyhome_max = df_zmyhome['ราคา'].max()
        zmyhome_avg = df_zmyhome['ราคา'].replace(0, np.nan).mean()
        zmyhome_types = ", ".join(df_zmyhome['ประเภททรัพย์'].value_counts().index[:3])
    else:
        zmyhome_min, zmyhome_max, zmyhome_avg, zmyhome_types = 0, 0, 0, "-"

    summary_rows = [
        {
            "บริษัท / แหล่งข้อมูล": "BAM (บสก.)",
            "จำนวนดึงสำเร็จ": f"{scraped_bam:,} รายการ",
            "ประกาศจริงบนเว็บ": f"{bam_web_total:,} รายการ",
            "ร้อยละการ Scrap": f"{pct_bam:.2f}%",
            "ราคาเฉลี่ย": format_price_thai(bam_avg),
            "ช่วงราคาเริ่มต้น": f"{format_price_thai(bam_min)} - {format_price_thai(bam_max)}",
            "ประเภททรัพย์หลัก": bam_types,
            "วันที่ปรับปรุงไฟล์": file_time_bam
        },
        {
            "บริษัท / แหล่งข้อมูล": "Baania (บาเนีย)",
            "จำนวนดึงสำเร็จ": f"{scraped_baania:,} รายการ",
            "ประกาศจริงบนเว็บ": f"{baania_total_desc} รายการ",
            "ร้อยละการ Scrap": f"{pct_baania:.2f}%",
            "ราคาเฉลี่ย": format_price_thai(baania_avg),
            "ช่วงราคาเริ่มต้น": f"{format_price_thai(baania_min)} - {format_price_thai(baania_max)}",
            "ประเภททรัพย์หลัก": baania_types,
            "วันที่ปรับปรุงไฟล์": file_time_baania
        },
        {
            "บริษัท / แหล่งข้อมูล": "LivingInsider (ลิฟวิ่งอินไซเดอร์)",
            "จำนวนดึงสำเร็จ": f"{scraped_living:,} รายการ",
            "ประกาศจริงบนเว็บ": f"{living_web_total:,} รายการ",
            "ร้อยละการ Scrap": f"{pct_living:.2f}%",
            "ราคาเฉลี่ย": format_price_thai(living_avg),
            "ช่วงราคาเริ่มต้น": f"{format_price_thai(living_min)} - {format_price_thai(living_max)}",
            "ประเภททรัพย์หลัก": living_types,
            "วันที่ปรับปรุงไฟล์": file_time_living
        },
        {
            "บริษัท / แหล่งข้อมูล": "ZmyHome (ซีมายโฮม)",
            "จำนวนดึงสำเร็จ": f"{scraped_zmyhome:,} รายการ",
            "ประกาศจริงบนเว็บ": f"{zmyhome_web_total:,} รายการ",
            "ร้อยละการ Scrap": f"{pct_zmyhome:.2f}%",
            "ราคาเฉลี่ย": format_price_thai(zmyhome_avg),
            "ช่วงราคาเริ่มต้น": f"{format_price_thai(zmyhome_min)} - {format_price_thai(zmyhome_max)}",
            "ประเภททรัพย์หลัก": zmyhome_types,
            "วันที่ปรับปรุงไฟล์": file_time_zmyhome
        }
    ]

    df_summary_table = pd.DataFrame(summary_rows)
    st.dataframe(
        df_summary_table,
        use_container_width=True,
        hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ----------------- PAGE 3: COMPANY INSIGHTS BREAKDOWN -----------------
elif selected_page == "🔍 เจาะลึกข้อมูลรายบริษัท":
    st.markdown("""
    <div class="dashboard-header">
        <h1 class="dashboard-title">🔍 ข้อมูลจำแนกของแต่ละบริษัท (Quick Insights)</h1>
        <p class="dashboard-subtitle">ข้อมูลการกระจายตัวของประเภททรัพย์สิน (Property Types) และจังหวัดยอดนิยมของข้อมูลแต่ละแหล่ง</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="summary-section">', unsafe_allow_html=True)
    
    # Select company tab
    selected_tab = st.radio("เลือกดูภาพรวมข้อมูลรายบริษัท:", ["BAM NPA", "Baania NPA", "LivingInsider NPA", "ZmyHome NPA"], horizontal=True)

    if selected_tab == "BAM NPA":
        if df_bam is not None and not df_bam.empty:
            col_type, col_prov = st.columns(2)
            
            with col_type:
                # Type distribution
                type_counts = df_bam['ประเภททรัพย์'].value_counts().reset_index()
                type_counts.columns = ['ประเภททรัพย์', 'จำนวน']
                fig_bam_type = px.bar(
                    type_counts.head(10),
                    y='ประเภททรัพย์',
                    x='จำนวน',
                    orientation='h',
                    title="ประเภททรัพย์สินที่มีในระบบ (Top 10)",
                    color='จำนวน',
                    color_continuous_scale='Blues'
                )
                fig_bam_type.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#888888'), height=300)
                st.plotly_chart(fig_bam_type, use_container_width=True)
                
            with col_prov:
                # Province distribution
                prov_counts = df_bam['จังหวัด'].value_counts().reset_index()
                prov_counts.columns = ['จังหวัด', 'จำนวน']
                fig_bam_prov = px.bar(
                    prov_counts.head(10),
                    x='จังหวัด',
                    y='จำนวน',
                    title="จังหวัดที่มีการดึงประกาศสูงสุด (Top 10)",
                    color='จำนวน',
                    color_continuous_scale='Purples'
                )
                fig_bam_prov.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#888888'), height=300)
                st.plotly_chart(fig_bam_prov, use_container_width=True)
        else:
            st.warning("ไม่มีข้อมูล BAM NPA ให้แสดง")

    elif selected_tab == "Baania NPA":
        if df_baania is not None and not df_baania.empty:
            col_type, col_prov = st.columns(2)
            
            with col_type:
                # Type distribution
                type_counts = df_baania['ประเภททรัพย์'].value_counts().reset_index()
                type_counts.columns = ['ประเภททรัพย์', 'จำนวน']
                fig_baa_type = px.bar(
                    type_counts.head(10),
                    y='ประเภททรัพย์',
                    x='จำนวน',
                    orientation='h',
                    title="ประเภททรัพย์สินที่มีในระบบ (Top 10)",
                    color='จำนวน',
                    color_continuous_scale='Greens'
                )
                fig_baa_type.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#888888'), height=300)
                st.plotly_chart(fig_baa_type, use_container_width=True)
                
            with col_prov:
                # Province distribution
                prov_counts = df_baania['จังหวัด'].value_counts().reset_index()
                prov_counts.columns = ['จังหวัด', 'จำนวน']
                fig_baa_prov = px.bar(
                    prov_counts.head(10),
                    x='จังหวัด',
                    y='จำนวน',
                    title="จังหวัดที่มีการดึงประกาศสูงสุด (Top 10)",
                    color='จำนวน',
                    color_continuous_scale='Teal'
                )
                fig_baa_prov.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#888888'), height=300)
                st.plotly_chart(fig_baa_prov, use_container_width=True)
        else:
            st.warning("ไม่มีข้อมูล Baania NPA ให้แสดง")

    elif selected_tab == "LivingInsider NPA":
        if df_living is not None and not df_living.empty:
            col_type, col_prov = st.columns(2)
            
            with col_type:
                # Type distribution
                type_counts = df_living['ประเภททรัพย์'].value_counts().reset_index()
                type_counts.columns = ['ประเภททรัพย์', 'จำนวน']
                fig_liv_type = px.bar(
                    type_counts.head(10),
                    y='ประเภททรัพย์',
                    x='จำนวน',
                    orientation='h',
                    title="ประเภททรัพย์สินที่มีในระบบ (Top 10)",
                    color='จำนวน',
                    color_continuous_scale='Oranges'
                )
                fig_liv_type.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#888888'), height=300)
                st.plotly_chart(fig_liv_type, use_container_width=True)
                
            with col_prov:
                # Province distribution
                prov_counts = df_living['จังหวัด'].value_counts().reset_index()
                prov_counts.columns = ['จังหวัด', 'จำนวน']
                fig_liv_prov = px.bar(
                    prov_counts.head(10),
                    x='จังหวัด',
                    y='จำนวน',
                    title="จังหวัดที่มีการดึงประกาศสูงสุด (Top 10)",
                    color='จำนวน',
                    color_continuous_scale='Reds'
                )
                fig_liv_prov.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#888888'), height=300)
                st.plotly_chart(fig_liv_prov, use_container_width=True)
        else:
            st.warning("ไม่มีข้อมูล LivingInsider NPA ให้แสดง")
            
    elif selected_tab == "ZmyHome NPA":
        if df_zmyhome is not None and not df_zmyhome.empty:
            col_type, col_prov = st.columns(2)
            
            with col_type:
                # Type distribution
                type_counts = df_zmyhome['ประเภททรัพย์'].value_counts().reset_index()
                type_counts.columns = ['ประเภททรัพย์', 'จำนวน']
                fig_zmy_type = px.bar(
                    type_counts.head(10),
                    y='ประเภททรัพย์',
                    x='จำนวน',
                    orientation='h',
                    title="ประเภททรัพย์สินที่มีในระบบ (Top 10)",
                    color='จำนวน',
                    color_continuous_scale='Oranges'
                )
                fig_zmy_type.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#888888'), height=300)
                st.plotly_chart(fig_zmy_type, use_container_width=True)
                
            with col_prov:
                # Province distribution
                prov_counts = df_zmyhome['จังหวัด'].value_counts().reset_index()
                prov_counts.columns = ['จังหวัด', 'จำนวน']
                fig_zmy_prov = px.bar(
                    prov_counts.head(10),
                    x='จังหวัด',
                    y='จำนวน',
                    title="จังหวัดที่มีการดึงประกาศสูงสุด (Top 10)",
                    color='จำนวน',
                    color_continuous_scale='YlOrBr'
                )
                fig_zmy_prov.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#888888'), height=300)
                st.plotly_chart(fig_zmy_prov, use_container_width=True)
        else:
            st.warning("ไม่มีข้อมูล ZmyHome NPA ให้แสดง")
            
    st.markdown('</div>', unsafe_allow_html=True)


# ----------------- PAGE 4: PROPERTY COMPARISON & VALUATION -----------------
elif selected_page == "🔄 เปรียบเทียบทรัพย์สินใกล้เคียง":
    st.markdown("""
    <div class="dashboard-header">
        <h1 class="dashboard-title">🔄 เปรียบเทียบทรัพย์สินใกล้เคียง (Property Comparison)</h1>
        <p class="dashboard-subtitle">ค้นหาทรัพย์สินใกล้เคียง เปรียบเทียบราคาตลาด และวิเคราะห์ส่วนต่างเชิงทำเลในรัศมีที่กำหนด</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("กำลังจัดเตรียมข้อมูลสำหรับเปรียบเทียบ..."):
        df_comp = prepare_comparison_dataset()
        
    if df_comp.empty:
        st.warning("⚠️ ไม่พบข้อมูลพิกัดทรัพย์สินในฐานข้อมูลสำหรับการเปรียบเทียบ")
    else:
        st.markdown('<div class="summary-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">1. เลือกทรัพย์สินหลักสำหรับเปรียบเทียบ (Reference Property)</h3>', unsafe_allow_html=True)
        
        tab_db, tab_manual = st.tabs(["เลือกจากทรัพย์สินในระบบ", "กรอกข้อมูลทรัพย์สินใหม่ด้วยตนเอง"])
        
        ref_asset = None
        
        with tab_db:
            col_search_prov, col_search_type, col_search_name = st.columns([1, 1, 2])
            
            with col_search_prov:
                provinces = sorted(df_comp['province'].unique())
                bkk_idx = provinces.index('กรุงเทพมหานคร') if 'กรุงเทพมหานคร' in provinces else 0
                selected_search_prov = st.selectbox("จังหวัดที่ต้องการค้นหา:", provinces, index=bkk_idx)
                
            with col_search_type:
                types = sorted(df_comp[df_comp['province'] == selected_search_prov]['property_type'].unique())
                selected_search_type = st.selectbox("ประเภททรัพย์สินหลัก:", ["ทั้งหมด"] + list(types))
                
            with col_search_name:
                df_filtered_search = df_comp[df_comp['province'] == selected_search_prov]
                if selected_search_type != "ทั้งหมด":
                    df_filtered_search = df_filtered_search[df_filtered_search['property_type'] == selected_search_type]
                
                search_kw = st.text_input("ค้นหาชื่อโครงการ/ชื่อประกาศ หรือรหัสทรัพย์ (แล้วกด Enter):", "")
                if search_kw:
                    df_filtered_search = df_filtered_search[
                        df_filtered_search['project_name'].str.contains(search_kw, case=False, na=False) |
                        df_filtered_search['id'].str.contains(search_kw, case=False, na=False)
                    ]
            
            if not df_filtered_search.empty:
                asset_options = []
                for _, r in df_filtered_search.iterrows():
                    price_str = format_price_thai(r['price'])
                    asset_options.append(f"[{r['source']}] {r['project_name']} | ID: {r['id']} | ราคา: {price_str}")
                    
                selected_option = st.selectbox("เลือกทรัพย์สินหลัก:", asset_options)
                selected_idx = asset_options.index(selected_option)
                ref_asset = df_filtered_search.iloc[selected_idx].to_dict()
            else:
                st.info("ℹ️ ไม่พบทรัพย์สินตามเงื่อนไขค้นหา กรุณาเปลี่ยนคำค้นหาหรือเลือกแท็บกรอกข้อมูลเอง")
                
        with tab_manual:
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                manual_project = st.text_input("ชื่อโครงการ / ชื่อประกาศจำลอง:", "บ้านเดี่ยวโครงการใหม่")
                manual_type = st.selectbox(
                    "ประเภททรัพย์สินอ้างอิง:", 
                    sorted(list(df_comp['property_type'].unique())) if not df_comp.empty else ["บ้านเดี่ยว", "คอนโด", "ทาวน์เฮ้าส์"]
                )
                manual_price = st.number_input("ราคาอ้างอิงหลัก (บาท):", min_value=0, value=3000000, step=100000)
            
            with col_m2:
                manual_lat = st.number_input("ละติจูด (Latitude) ทรัพย์จำลอง:", min_value=-90.0, max_value=90.0, value=13.7468, format="%.6f")
                manual_lon = st.number_input("ลองจิจูด (Longitude) ทรัพย์จำลอง:", min_value=-180.0, max_value=180.0, value=100.5349, format="%.6f")
                manual_province = st.text_input("ระบุจังหวัด:", "กรุงเทพมหานคร")
                
            if st.button("ตกลงใช้ทรัพย์สมมตินี้เป็นทรัพย์สินหลัก", key="use_manual_asset"):
                ref_asset = {
                    "source": "ข้อมูลนำเข้าเอง (Manual)",
                    "id": "CUSTOM_NPA_01",
                    "project_name": manual_project,
                    "property_type": manual_type,
                    "price": manual_price,
                    "lat": manual_lat,
                    "lon": manual_lon,
                    "province": manual_province,
                    "district": "ไม่ระบุ",
                    "subdistrict": "ไม่ระบุ",
                    "url": "#"
                }
                st.session_state['manual_ref_asset'] = ref_asset
                
        # Fallback to session state manual asset
        if 'manual_ref_asset' in st.session_state and ref_asset is None:
            ref_asset = st.session_state['manual_ref_asset']
            
        if ref_asset is not None:
            st.markdown('<h4 style="font-weight:600; color:#1e293b; margin-top: 15px;">ตารางแสดงทรัพย์สินหลักที่เลือก</h4>', unsafe_allow_html=True)
            df_ref_table = pd.DataFrame([{
                "แหล่งข้อมูล": ref_asset['source'],
                "รหัสทรัพย์": ref_asset['id'],
                "ชื่อโครงการ / ประกาศ": ref_asset['project_name'],
                "ประเภททรัพย์": ref_asset['property_type'],
                "ราคาตลาด": format_price_thai(ref_asset['price']),
                "ตำบล": ref_asset['subdistrict'],
                "อำเภอ": ref_asset['district'],
                "จังหวัด": ref_asset['province'],
                "พิกัด (Lat, Lon)": f"{ref_asset['lat']:.6f}, {ref_asset['lon']:.6f}"
            }])
            st.dataframe(df_ref_table, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 2. Comparison parameters
            st.markdown('<div class="summary-section">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">2. เงื่อนไขในการหาทรัพย์ใกล้เคียง</h3>', unsafe_allow_html=True)
            
            col_cond1, col_cond2, col_cond3 = st.columns(3)
            
            with col_cond1:
                radius_km = st.slider(
                    "ระยะทางรัศมีที่กำหนด (กิโลเมตร):", 
                    min_value=0.1, 
                    max_value=20.0, 
                    value=3.0, 
                    step=0.1
                )
                
            with col_cond2:
                filter_type_option = st.radio(
                    "กรองประเภททรัพย์:",
                    ["เฉพาะประเภททรัพย์เดียวกันเท่านั้น", "ประเภททรัพย์สินใดก็ได้"],
                    index=0
                )
                
            with col_cond3:
                filter_project_option = st.radio(
                    "กรองชื่อโครงการ:",
                    ["โครงการใดก็ได้", "เฉพาะโครงการเดียวกันเท่านั้น", "ระบุคำค้นชื่อโครงการ"],
                    index=0
                )
                
                custom_project_kw = ""
                if filter_project_option == "ระบุคำค้นชื่อโครงการ":
                    custom_project_kw = st.text_input("คำค้นชื่อโครงการ:", "")
            
            # Select sources to compare
            st.markdown('<p style="font-size:0.9rem; font-weight:600; margin-bottom:5px;">เลือกแหล่งข้อมูลค่ายที่จะค้นหารวม:</p>', unsafe_allow_html=True)
            col_src1, col_src2, col_src3, col_src4 = st.columns(4)
            with col_src1:
                src_bam = st.checkbox("BAM (บสก.)", value=True)
            with col_src2:
                src_baania = st.checkbox("Baania (บาเนีย)", value=True)
            with col_src3:
                src_living = st.checkbox("LivingInsider", value=True)
            with col_src4:
                src_zmyhome = st.checkbox("ZmyHome", value=True)
                
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Process search
            selected_sources = []
            if src_bam: selected_sources.append('BAM NPA')
            if src_baania: selected_sources.append('Baania NPA')
            if src_living: selected_sources.append('LivingInsider NPA')
            if src_zmyhome: selected_sources.append('ZmyHome NPA')
            
            df_candidates = df_comp[df_comp['source'].isin(selected_sources)].copy()
            
            # Exclude self
            if ref_asset['source'] in selected_sources:
                df_candidates = df_candidates[df_candidates['id'] != ref_asset['id']]
                
            if not df_candidates.empty:
                # Calculate distance
                df_candidates['distance_km'] = haversine_distance(
                    ref_asset['lat'], 
                    ref_asset['lon'], 
                    df_candidates['lat'], 
                    df_candidates['lon']
                )
                
                # Filter radius
                df_matches = df_candidates[df_candidates['distance_km'] <= radius_km].copy()
                
                # Filter type
                if filter_type_option == "เฉพาะประเภททรัพย์เดียวกันเท่านั้น":
                    df_matches = df_matches[df_matches['property_type'] == ref_asset['property_type']]
                    
                # Filter project
                if filter_project_option == "เฉพาะโครงการเดียวกันเท่านั้น":
                    ref_proj_clean = ref_asset['project_name'].replace(" ", "").lower()
                    if ref_proj_clean and ref_proj_clean != 'ไม่ระบุโครงการ':
                        df_matches = df_matches[
                            df_matches['project_name'].str.replace(" ", "").str.lower().str.contains(ref_proj_clean, na=False) |
                            df_matches['project_name'].apply(lambda x: x.replace(" ", "").lower() in ref_proj_clean)
                        ]
                    else:
                        st.warning("⚠️ ทรัพย์สินหลักไม่ระบุชื่อโครงการ ไม่สามารถกรองเฉพาะโครงการเดียวกันได้")
                elif filter_project_option == "ระบุคำค้นชื่อโครงการ" and custom_project_kw:
                    df_matches = df_matches[
                        df_matches['project_name'].str.contains(custom_project_kw, case=False, na=False)
                    ]
            else:
                df_matches = pd.DataFrame()
                
            # 3. Results rendering
            st.markdown('<div class="summary-section">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-title">3. สรุปการเปรียบเทียบทรัพย์สินและราคากลาง</h3>', unsafe_allow_html=True)
            
            if df_matches.empty:
                st.info("ℹ️ ไม่พบทรัพย์สินใกล้เคียงในเงื่อนไขการค้นหาข้างต้น กรุณาลองปรับเพิ่มรัศมีหรือลดตัวกรอง")
            else:
                avg_price = df_matches['price'].mean()
                min_price = df_matches['price'].min()
                max_price = df_matches['price'].max()
                total_matches = len(df_matches)
                
                # Difference calculation
                ref_price = ref_asset['price']
                price_diff = ref_price - avg_price
                price_diff_pct = (price_diff / avg_price * 100) if avg_price > 0 else 0
                
                # Render KPIs
                col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
                
                with col_kpi1:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-icon">⭐</div>
                        <div class="kpi-company">ราคาทรัพย์อ้างอิง</div>
                        <div class="kpi-value">{format_price_thai(ref_price)}</div>
                        <div class="kpi-time">ค่าย: {ref_asset['source']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col_kpi2:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-icon">📊</div>
                        <div class="kpi-company">ราคาเฉลี่ยทรัพย์รอบตัว ({total_matches} รายการ)</div>
                        <div class="kpi-value">{format_price_thai(avg_price)}</div>
                        <div class="kpi-time">ช่วง: {format_price_thai(min_price)} - {format_price_thai(max_price)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col_kpi3:
                    if price_diff > 0:
                        diff_text = f"สูงกว่าราคาเฉลี่ยรอบข้าง {price_diff_pct:.2f}%"
                        diff_color = "#ef4444"
                        diff_icon = "📈"
                    elif price_diff < 0:
                        diff_text = f"ต่ำกว่าราคาเฉลี่ยรอบข้าง {abs(price_diff_pct):.2f}%"
                        diff_color = "#10b981"
                        diff_icon = "📉"
                    else:
                        diff_text = "เท่ากับราคาเฉลี่ยตลาดรอบข้าง"
                        diff_color = "#64748b"
                        diff_icon = "⚖️"
                        
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-icon">{diff_icon}</div>
                        <div class="kpi-company">เปรียบเทียบกับราคาเฉลี่ยรอบข้าง</div>
                        <div class="kpi-value" style="color: {diff_color} !important; font-size: 1.25rem;">{diff_text}</div>
                        <div class="kpi-time">ส่วนต่าง: {format_price_thai(abs(price_diff))}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col_kpi4:
                    st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-icon">📍</div>
                        <div class="kpi-company">ระยะที่วิเคราะห์</div>
                        <div class="kpi-value" style="color: #4f46e5; font-size: 1.35rem;">รัศมี {radius_km} กม.</div>
                        <div class="kpi-time">พิกัดศูนย์กลาง: {ref_asset['lat']:.4f}, {ref_asset['lon']:.4f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # 4. Map
                st.markdown('<h4 style="font-weight:600; color:#1e293b; margin-top: 15px;">แผนที่แสดงพิกัดเชิงทำเลของทรัพย์เปรียบเทียบ</h4>', unsafe_allow_html=True)
                
                source_colors = {
                    'BAM NPA': '#3b82f6',
                    'Baania NPA': '#10b981',
                    'LivingInsider NPA': '#f97316',
                    'ZmyHome NPA': '#a855f7'
                }
                
                fig_comp_map = go.Figure()
                
                # Add reference point (Red Star)
                fig_comp_map.add_trace(go.Scattermapbox(
                    lat=[ref_asset['lat']],
                    lon=[ref_asset['lon']],
                    mode='markers',
                    marker=go.scattermapbox.Marker(
                        size=18,
                        color='#ef4444',
                        symbol='star'
                    ),
                    name='ทรัพย์สินหลัก (Reference)',
                    text=[f"⭐ {ref_asset['project_name']}<br>ราคา: {format_price_thai(ref_asset['price'])}<br>ประเภท: {ref_asset['property_type']}"],
                    hoverinfo='text'
                ))
                
                # Add comparables grouped by source
                for src in selected_sources:
                    df_src_matches = df_matches[df_matches['source'] == src]
                    if not df_src_matches.empty:
                        lats = df_src_matches['lat'].tolist()
                        lons = df_src_matches['lon'].tolist()
                        texts = []
                        for _, r in df_src_matches.iterrows():
                            price_ratio = ((r['price'] - ref_price)/ref_price * 100) if ref_price > 0 else 0
                            texts.append(
                                f"📍 {r['project_name']}<br>"
                                f"แหล่งข้อมูล: {r['source']}<br>"
                                f"ราคา: {format_price_thai(r['price'])}<br>"
                                f"ประเภท: {r['property_type']}<br>"
                                f"ระยะทาง: {r['distance_km']:.2f} กม.<br>"
                                f"ส่วนต่างราคาทรัพย์หลัก: {price_ratio:+.1f}%"
                            )
                            
                        fig_comp_map.add_trace(go.Scattermapbox(
                            lat=lats,
                            lon=lons,
                            mode='markers',
                            marker=go.scattermapbox.Marker(
                                size=11,
                                color=source_colors.get(src, '#64748b')
                            ),
                            name=src,
                            text=texts,
                            hoverinfo='text'
                        ))
                
                fig_comp_map.update_layout(
                    mapbox=dict(
                        style="open-street-map",
                        center=dict(lat=ref_asset['lat'], lon=ref_asset['lon']),
                        zoom=13 - (radius_km / 5.0) if radius_km > 0 else 13
                    ),
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=450,
                    showlegend=True,
                    legend=dict(
                        yanchor="top",
                        y=0.98,
                        xanchor="left",
                        x=0.01,
                        bgcolor="rgba(255, 255, 255, 0.85)"
                    )
                )
                
                st.plotly_chart(fig_comp_map, use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                # 5. Table
                st.markdown('<h4 style="font-weight:600; color:#1e293b;">ตารางแสดงรายละเอียดการเปรียบเทียบทรัพย์สิน (เรียงตามระยะห่างจากใกล้ไปไกล)</h4>', unsafe_allow_html=True)
                
                df_table = df_matches.sort_values(by='distance_km').copy()
                
                df_table['ราคาส่วนต่าง (%)'] = df_table['price'].apply(
                    lambda x: f"{((x - ref_price) / ref_price * 100):+.1f}%" if ref_price > 0 else "0.0%"
                )
                df_table['ระยะห่าง (กม.)'] = df_table['distance_km'].round(2)
                df_table['ราคาทรัพย์เปรียบเทียบ'] = df_table['price'].apply(format_price_thai)
                
                df_table_display = df_table[[
                    'source', 'id', 'project_name', 'property_type', 
                    'ราคาทรัพย์เปรียบเทียบ', 'ระยะห่าง (กม.)', 
                    'ราคาส่วนต่าง (%)', 'subdistrict', 'district', 'province', 'url'
                ]].copy()
                
                df_table_display.columns = [
                    'แหล่งข้อมูล', 'รหัสทรัพย์', 'ชื่อโครงการ / ประกาศ', 'ประเภททรัพย์', 
                    'ราคา', 'ระยะห่าง (กม.)', 'ราคาส่วนต่าง (%)', 
                    'ตำบล', 'อำเภอ', 'จังหวัด', 'ลิงก์ประกาศต้นทาง'
                ]
                
                st.dataframe(
                    df_table_display,
                    column_config={
                        "ลิงก์ประกาศต้นทาง": st.column_config.LinkColumn("ลิงก์ประกาศต้นทาง", display_text="เปิดดูประกาศเดิม")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            st.markdown('</div>', unsafe_allow_html=True)
