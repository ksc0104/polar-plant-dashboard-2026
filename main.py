import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
import io

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="극지식물 생육 분석 대시보드",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# 테마 CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

  * { box-sizing: border-box; }

  html, body, [class*="css"], .stApp {
    font-family: 'Inter', 'Noto Sans KR', sans-serif !important;
    background: #f0f4f8 !important;
    color: #1a2a3a !important;
  }

  .main .block-container {
    background: linear-gradient(160deg, #f0f4f8 0%, #e8eef5 50%, #f5f0f0 100%) !important;
    border-radius: 0 !important;
  }

  [data-testid="stHeader"] { display: none; }

  .dashboard-title {
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    font-size: 2rem;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #0d2137 0%, #1a5276 50%, #2d7ab8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.25em;
  }

  .dashboard-subtitle {
    font-family: 'Noto Sans KR', sans-serif;
    font-weight: 400;
    font-size: 0.95rem;
    color: #5a6f82;
    margin-bottom: 1.5rem;
    border-left: 3px solid #2d7ab8;
    padding-left: 12px;
  }

  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1f2d 0%, #142a3d 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
  }

  .sidebar-title-custom {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    color: #7fb3d8;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(127,179,216,0.15);
  }

  .stat-card {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.5);
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    box-shadow: 0 4px 16px rgba(13,33,55,0.07), 0 1px 3px rgba(13,33,55,0.04);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
    height: 100%;
  }
  .stat-card:hover {
    box-shadow: 0 8px 28px rgba(13,33,55,0.11), 0 2px 6px rgba(13,33,55,0.06);
    transform: translateY(-2px);
  }
  .stat-card-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6b8aa0;
    margin-bottom: 0.35rem;
  }
  .stat-card-value {
    font-family: 'Inter', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: #0d2137;
    line-height: 1.1;
  }
  .stat-card-value.accent-blue  { color: #1a5276; }
  .stat-card-value.accent-coral { color: #c0392b; }
  .stat-card-value.accent-lime  { color: #1d6f42; }
  .stat-card-value.accent-gold  { color: #8b6914; }

  .section-card {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.6);
    border-radius: 14px;
    padding: 1.3rem 1.4rem;
    box-shadow: 0 4px 14px rgba(13,33,55,0.05);
  }
  .section-title {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #4a6a82;
    margin-bottom: 0.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid rgba(45,122,184,0.2);
  }

  .hypothesis-card {
    background: linear-gradient(135deg, rgba(26,82,118,0.04) 0%, rgba(45,122,184,0.06) 100%);
    border-left: 3px solid #2d7ab8;
    border-radius: 0 10px 10px 0;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
  }
  .hypothesis-num {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    color: #2d7ab8;
    background: rgba(45,122,184,0.12);
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-right: 0.5rem;
    flex-shrink: 0;
  }

  [data-testid="stTabs"] button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.04em !important;
    padding: 0.65rem 1.2rem !important;
    border-radius: 8px 8px 0 0 !important;
    color: #5a7a94 !important;
    background: transparent !important;
  }
  [data-testid="stTabs"] button[aria-selected="true"] {
    background: rgba(255,255,255,0.9) !important;
    color: #1a5276 !important;
    box-shadow: 0 2px 8px rgba(13,33,55,0.08) !important;
    border-bottom: 2px solid #2d7ab8 !important;
  }
  [data-testid="stTabs"] button:hover:not([aria-selected="true"]) {
    background: rgba(255,255,255,0.5) !important;
    color: #1a5276 !important;
  }

  .info-card {
    background: rgba(255,255,255,0.7);
    border: 1px dashed rgba(45,122,184,0.3);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    color: #5a7a94;
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 0.88rem;
  }

  .history-banner {
    background: linear-gradient(90deg, rgba(26,82,118,0.08) 0%, rgba(45,122,184,0.12) 50%, rgba(26,82,118,0.08) 100%);
    border-radius: 10px;
    padding: 0.7rem 1.2rem;
    border: 1px solid rgba(45,122,184,0.15);
  }

  .stDataFrame { font-family: 'Inter', sans-serif !important; }
  .stDataFrame table { font-size: 0.82rem !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 데이터 로딩
# ─────────────────────────────────────────────
@st.cache_data
def load_and_standardize(env_file, growth_file):
    env_df = read_csv(env_file) if env_file is not None else pd.DataFrame()
    growth_df = read_csv(growth_file) if growth_file is not None else pd.DataFrame()
    if not env_df.empty:
        env_df = std_cols(env_df)
    if not growth_df.empty:
        growth_df = std_cols(growth_df)
    return env_df, growth_df

def read_csv(file):
    data = file.getvalue()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(io.BytesIO(data), encoding=enc)
        except Exception:
            pass
    return pd.DataFrame()

def std_cols(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    rename = {}
    for c in df.columns:
        k = c.lower().replace(" ", "")
        if k in ("time", "categories", "시간", "날짜", "datetime", "date"):
            rename[c] = "time"
        elif k in ("temperature", "온도"):
            rename[c] = "temperature"
        elif k in ("humidity", "습도"):
            rename[c] = "humidity"
        elif k == "ph":
            rename[c] = "ph"
        elif k == "ec":
            rename[c] = "ec"
        elif "생중량" in k:
            rename[c] = "생중량"
        elif "잎" in k:
            rename[c] = "잎 수"
        elif "지상부" in k and "길이" in k:
            rename[c] = "지상부 길이"
        elif "지하부" in k and "길이" in k:
            rename[c] = "지하부 길이"
        elif "지상부" in k and ("질량" in k or "무게" in k):
            rename[c] = "지상부 질량"
        elif "지하부" in k and ("질량" in k or "무게" in k):
            rename[c] = "지하부 질량"
        elif "개체" in k:
            rename[c] = "개체번호"
    df = df.rename(columns=rename)
    for c in df.columns:
        if c in ("time", "개체번호"):
            continue
        if not pd.api.types.is_numeric_dtype(df[c]):
            num = pd.to_numeric(df[c].astype(str).str.replace(",", "").str.extract(r"(-?\d+\.?\d*)")[0], errors="coerce")
            if num.notna().mean() >= 0.5:
                df[c] = num
    if "생중량" not in df.columns and {"지상부 질량", "지하부 질량"} <= set(df.columns):
        df["생중량"] = df["지상부 질량"] + df["지하부 질량"]
    if "time" in df.columns:
        t = df["time"].astype(str).str.strip()
        parsed = pd.to_datetime(t, errors="coerce", format="mixed")
        bad = parsed.isna() & t.str.match(r"^\d{8}_\d{1,2}$")
        if bad.any():
            parts = t[bad].str.split("_", expand=True)
            parsed[bad] = pd.to_datetime(parts[0], format="%Y%m%d") + pd.to_timedelta(parts[1].astype(int), unit="h")
        df["time"] = parsed
    return df

def get_school_name(file):
    if file is None:
        return "우리 학교"
    name = file.name
    for sep in ["_", "-"]:
        if sep in name:
            return name.split(sep)[0]
    return name.replace(".csv", "")

# ─────────────────────────────────────────────
# 색상
# ─────────────────────────────────────────────
PALETTE = {
    "deep":   "#0d2137",
    "ocean":  "#1a5276",
    "sky":    "#2d7ab8",
    "ice":    "#5dade2",
    "coral":  "#c0392b",
    "lime":   "#1d6f42",
    "gold":   "#8b6914",
}

PLOTLY_COLORS = ["#1a5276", "#2d7ab8", "#5dade2", "#c0392b", "#1d6f42", "#8b6914", "#e67e22", "#8e44ad"]

def plotly_theme(fig, width=900, height=480, show_title=True):
    fig.update_layout(
        font=dict(family="Inter, 'Noto Sans KR', sans-serif", color="#1a2a3a"),
        plot_bgcolor="rgba(255,255,255,0.95)",
        paper_bgcolor="rgba(255,255,255,0.95)",
        margin=dict(l=60, r=30, t=50, b=50),
        width=width, height=height,
        hoverlabel=dict(bgcolor="#0d2137", font_color="white",
                        font_family="Inter, 'Noto Sans KR', sans-serif",
                        font_size=12),
        xaxis=dict(
            gridcolor="rgba(45,122,184,0.08)",
            zerolinecolor="rgba
