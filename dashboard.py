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
</style>
""", unsafe_allow_html=True)

# Define directories relative to dashboard location (supporting local sibling dirs and streamlit cloud deployment)
extensions_dir = Path(__file__).resolve().parent.parent
local_data_dir = Path(__file__).resolve().parent / "data"

bam_dir = extensions_dir / "BAM NPA"
if not (bam_dir / "BAM NPA.xlsx").exists() and local_data_dir.exists():
    bam_dir = local_data_dir

baania_dir = extensions_dir / "Baania NPA"
if not (baania_dir / "baania_listings.xlsx").exists() and local_data_dir.exists():
    baania_dir = local_data_dir

living_dir = extensions_dir / "Livinginsider NPA"
if not (living_dir / "Livinginsider NPA.xlsx").exists() and local_data_dir.exists():
    living_dir = local_data_dir

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
    url = "https://www.livinginsider.com/searchword/all/all/1/รวมประกาศ-ซื้อ-ขาย-เช่า-เซ้ง-คอนโด-บ้าน-ที่ดิน.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code == 200:
            pages = [int(x) for x in re.findall(r'/searchword/all/all/(\d+)/', r.text)]
            if pages:
                max_page = max(pages)
                # Fallback to items_count. LivingInsider standard list has 24 listings per page
                return max_page * 24
    except Exception:
        pass
    return 105720

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

# Load all data
df_bam = load_bam_data()
df_baania = load_baania_data()
df_living = load_living_data()

# Fetch totals & metadata
bam_web_total, bam_last_updated = fetch_bam_metadata()
living_web_total = fetch_livinginsider_web_count()
baania_web_total = fetch_baania_web_count()

# Scraped Counts
scraped_bam = len(df_bam) if df_bam is not None else 0
scraped_baania = len(df_baania) if df_baania is not None else 0
scraped_living = len(df_living) if df_living is not None else 0

# Total Scraped Values
bam_total_value = df_bam['ราคา'].sum() if df_bam is not None else 0
baania_total_value = df_baania['ราคาเริ่มต้น'].sum() if df_baania is not None else 0
living_total_value = df_living['ราคา'].sum() if df_living is not None else 0

# Percentages
# BAM
pct_bam = (scraped_bam / bam_web_total * 100) if bam_web_total > 0 else 0
# Baania: completed based on cutoff, it's 100%
pct_baania = 100.0 if scraped_baania >= baania_web_total else (scraped_baania / baania_web_total * 100)
# Livinginsider
pct_living = (scraped_living / living_web_total * 100) if living_web_total > 0 else 0

# Baania web count display description
baania_total_desc = f"{baania_web_total:,}+" if baania_web_total == 10000 else f"{baania_web_total:,}"

# File modifications
file_time_bam = get_file_mod_time(bam_dir / "BAM NPA.xlsx")
file_time_baania = get_file_mod_time(baania_dir / "baania_listings.xlsx")
file_time_living = get_file_mod_time(living_dir / "Livinginsider NPA.xlsx")


# ----------------- SIDEBAR NAVIGATION -----------------
with st.sidebar:
    st.markdown('<h2 style="color: #818cf8; font-weight: 700;"><i class="fa fa-search"></i> AMC NPA Monitor</h2>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Navigation Radio
    selected_page = st.radio(
        "เลือกหน้าเมนูหลัก:",
        ["🔮 แผนภาพวงกลม NPA ภาพรวม", "📊 สรุปความสำเร็จการดึงข้อมูล", "🔍 เจาะลึกข้อมูลรายบริษัท"],
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

    # 1. Helper function for generating SVG slices
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
        
        return f"""
        <g class="float-wrapper float-{bubble_id}">
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
        </g>
        """

    # Construct SVG content
    svg_content = f"""
    <svg viewBox="0 0 1000 580" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="background-color: transparent;">
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
        <radialGradient id="bam-scraped" cx="240" cy="160" r="145" fx="200" fy="120" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#fffebd"/>
          <stop offset="50%" stop-color="#ffa726"/>
          <stop offset="100%" stop-color="#f57c00"/>
        </radialGradient>
        <radialGradient id="bam-unscraped" cx="240" cy="160" r="145" fx="200" fy="120" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#fffefb"/>
          <stop offset="70%" stop-color="#ffeed6"/>
          <stop offset="100%" stop-color="#ffe0b2"/>
        </radialGradient>
        
        <!-- Baania Radial Gradients (Bright Green) -->
        <radialGradient id="baania-scraped" cx="760" cy="160" r="140" fx="720" fy="120" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#f1fdf5"/>
          <stop offset="50%" stop-color="#66bb6a"/>
          <stop offset="100%" stop-color="#388e3c"/>
        </radialGradient>
        <radialGradient id="baania-unscraped" cx="760" cy="160" r="140" fx="720" fy="120" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#fafdfb"/>
          <stop offset="70%" stop-color="#e8f5e9"/>
          <stop offset="100%" stop-color="#c8e6c9"/>
        </radialGradient>
        
        <!-- LivingInsider Radial Gradients (Bright Red) -->
        <radialGradient id="living-scraped" cx="500" cy="360" r="175" fx="450" fy="310" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#fff5f5"/>
          <stop offset="50%" stop-color="#ef5350"/>
          <stop offset="100%" stop-color="#d32f2f"/>
        </radialGradient>
        <radialGradient id="living-unscraped" cx="500" cy="360" r="175" fx="450" fy="310" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#fffbfa"/>
          <stop offset="70%" stop-color="#ffe4e6"/>
          <stop offset="100%" stop-color="#ffcdd2"/>
        </radialGradient>
      </defs>
      
      {generate_bubble_markup(240, 160, 145, "BAM NPA", f"{bam_web_total:,}", scraped_bam, pct_bam, format_price_thai(bam_total_value), "bam-scraped", "bam-unscraped", "bubble-bam")}
      {generate_bubble_markup(760, 160, 140, "Baania NPA", baania_total_desc, scraped_baania, pct_baania, format_price_thai(baania_total_value), "baania-scraped", "baania-unscraped", "bubble-baania")}
      {generate_bubble_markup(500, 360, 175, "LivingInsider NPA", f"{living_web_total:,}", scraped_living, pct_living, format_price_thai(living_total_value), "living-scraped", "living-unscraped", "bubble-living")}
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
        #bubble-bam {{ transform-origin: 240px 160px; }}
        #bubble-baania {{ transform-origin: 760px 160px; }}
        #bubble-living {{ transform-origin: 500px 360px; }}
        
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
    </style>
    </head>
    <body>
    <div class="bubble-container">
        {svg_content}
    </div>
    </body>
    </html>
    """
    
    import streamlit.components.v1 as components
    components.html(html_content, height=560)


# ----------------- PAGE 2: SCRAPING SUCCESS AND PROGRESS METRICS -----------------
elif selected_page == "📊 สรุปความสำเร็จการดึงข้อมูล":
    st.markdown("""
    <div class="dashboard-header">
        <h1 class="dashboard-title">📊 สรุปความสำเร็จและเปรียบเทียบผลการดึงข้อมูล (Scraping Metrics)</h1>
        <p class="dashboard-subtitle">ข้อมูลเปรียบเทียบสัดส่วนและเป้าหมายการกวาดข้อมูล NPA จากผู้ให้บริการคู่แข่งในรูปแบบเชิงปริมาณ</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ----------------- KPI CARDS GRID -----------------
    col1, col2, col3, col4 = st.columns(4)

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
                <div class="kpi-pct" style="color: #f59e0b;">{pct_living:.2f}% Scraped</div>
                <div class="kpi-time">ไฟล์อัปเดต: {file_time_living}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        total_scraped = scraped_bam + scraped_baania + scraped_living
        overall_pct = ((scraped_bam + scraped_baania + scraped_living) / (bam_web_total + baania_web_total + living_web_total) * 100)
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
        [scraped_baania, pct_baania, format_price_thai(baania_total_value)]
    ]

    fig_treemap = go.Figure(go.Treemap(
        labels=["LivingInsider NPA", "BAM NPA", "Baania NPA"],
        parents=["", "", ""],
        values=[living_web_total, bam_web_total, baania_web_total], # sizes match web totals
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
                "#ef4444",  # LivingInsider (0.16%) - Red
                "#f59e0b" if pct_bam < 60 else "#84cc16",  # BAM (52.15%) - Amber
                "#10b981"   # Baania (100.00%) - Emerald Green
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
    selected_tab = st.radio("เลือกดูภาพรวมข้อมูลรายบริษัท:", ["BAM NPA", "Baania NPA", "LivingInsider NPA"], horizontal=True)

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
                    color_continuous_scale='Teals'
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
            
    st.markdown('</div>', unsafe_allow_html=True)
