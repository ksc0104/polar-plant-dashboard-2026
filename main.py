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
            zerolinecolor="rgba(45,122,184,0.15)",
            linecolor="rgba(45,122,184,0.15)",
            tickfont=dict(size=11, color="#5a7a94"),
        ),
        yaxis=dict(
            gridcolor="rgba(45,122,184,0.08)",
            zerolinecolor="rgba(45,122,184,0.15)",
            linecolor="rgba(45,122,184,0.15)",
            tickfont=dict(size=11, color="#5a7a94"),
        ),
        legend=dict(
            font=dict(size=11, color="#4a6a82", family="Inter, sans-serif"),
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor="rgba(45,122,184,0.15)",
            borderwidth=1,
            x=1.02, y=1,
        ),
    )
    return fig

# ─────────────────────────────────────────────
# 차트 헬퍼
# ─────────────────────────────────────────────
def make_scatter_with_trend(df, x_col, y_col, title, color_col=None):
    d = df[[x_col, y_col]].dropna()
    if len(d) < 3:
        return None
    scatter_kwargs = dict(
        x=x_col, y=y_col,
        labels={x_col: x_col, y_col: y_col},
        color_discrete_sequence=PLOTLY_COLORS,
    )
    if color_col and color_col in df.columns:
        scatter_kwargs["color"] = color_col
        scatter_kwargs["hover_name"] = color_col

    fig = px.scatter(d, **scatter_kwargs)
    fig.data[0].marker = dict(
        size=9, opacity=0.82,
        line=dict(width=1.2, color="white"),
        symbol="circle",
    )
    x_vals = d[x_col].values
    y_vals = d[y_col].values
    slope, intercept = np.polyfit(x_vals, y_vals, 1)
    line_x = np.linspace(x_vals.min(), x_vals.max(), 100)
    line_y = slope * line_x + intercept
    r, p_val = stats.pearsonr(x_vals, y_vals)
    fig.add_trace(go.Scatter(
        x=line_x, y=line_y, mode="lines",
        line=dict(color="#c0392b", width=2.5, dash="solid"),
        name=f"추세선  r = {r:.3f}",
        hoverinfo="skip",
    ))
    fig.add_annotation(
        x=0.96, y=0.06, xref="paper", yref="paper",
        text=f"r = {r:.3f}",
        font=dict(size=12, color="#c0392b", family="Inter, sans-serif", weight=600),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="rgba(192,57,43,0.3)",
        borderwidth=1,
        borderpad=4,
        showarrow=False,
    )
    fig = plotly_theme(fig, width=880, height=480)
    if show_title := True:
        fig.update_layout(title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=14, color="#1a5276", family="Inter, sans-serif", weight=700),
            x=0.04, xanchor="left",
        ))
    return fig

def make_line_chart(df, time_col, value_col, title, color_hex):
    d = df[[time_col, value_col]].dropna().sort_values(time_col)
    if len(d) < 2:
        return None
    fig = px.line(d, x=time_col, y=value_col,
                  color_discrete_sequence=[color_hex])
    fig.data[0].line = dict(width=2.2, color=color_hex)
    fig.data[0].hovertemplate = f"<b>%{{x|%Y-%m-%d %H:%M}}</b><br>{value_col}: %{{y:.1f}}<extra></extra>"
    fig = plotly_theme(fig, width=420, height=340, show_title=False)
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>",
                   font=dict(size=13, color="#1a5276", family="Inter, sans-serif", weight=700),
                   x=0.04, xanchor="left"),
        showlegend=False,
    )
    fig.update_xaxes(tickformat="%m/%d")
    return fig

def make_correlation_heatmap(df, cols):
    d = df[cols].dropna()
    if len(d) < 3 or len(cols) < 2:
        return None
    corr = d[cols].corr()
    fig = px.imshow(corr, text_auto=".3f",
                    color_continuous_scale=[
                        (0.00, "#c0392b"),
                        (0.25, "#f5b041"),
                        (0.50, "#ffffff"),
                        (0.75, "#5dade2"),
                        (1.00, "#1a5276"),
                    ],
                    zmin=-1, zmax=1,
                    labels=dict(x="", y=""),
                    color_continuous_midpoint=0)
    fig = plotly_theme(fig, width=620, height=520, show_title=False)
    fig.update_layout(
        title=dict(text="<b>변수 간 상관계수 행렬</b>",
                   font=dict(size=14, color="#1a5276", family="Inter, sans-serif", weight=700),
                   x=0.04, xanchor="left"),
        xaxis=dict(
            side="bottom",
            tickangle=30,
            tickfont=dict(size=10, color="#5a7a94", family="Inter, sans-serif"),
            # titlefont 제거됨 — 제목 폰트 필요 시 title=dict(font=...) 내부에서만 사용
        ),
        yaxis=dict(
            tickfont=dict(size=10, color="#5a7a94", family="Inter, sans-serif"),
        ),
        coloraxis_colorbar=dict(
            title=dict(text="r", font=dict(size=10, color="#4a6a82", family="Inter, sans-serif")),
            tickfont=dict(size=10, color="#5a7a94", family="Inter, sans-serif"),
            thickness=14, len=0.7,
        ),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False, autorange="reversed")
    return fig

# ─────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="sidebar-title-custom">🌿 데이터 업로드</p>', unsafe_allow_html=True)

    env_file = st.file_uploader("🌡️ 환경 데이터 (CSV)", type="csv",
                                help="형식: time, temperature, humidity, ph, ec 또는 categories, 온도, 습도, EC, PH",
                                key="env_uploader")
    growth_file = st.file_uploader("🌱 생육 결과 데이터 (CSV)", type="csv",
                                   help="열 이름: 개체번호, 잎 수, 지상부 길이, 지하부 길이, 생중량 또는 지상부/지하부 질량",
                                   key="growth_uploader")

    if env_file is not None:
        st.markdown(f'<p style="color:#5dade2;font-size:0.78rem;margin-top:0.2rem;">'
                    f'✅ {env_file.name}</p>', unsafe_allow_html=True)
    if growth_file is not None:
        st.markdown(f'<p style="color:#5dade2;font-size:0.78rem;margin-top:0.2rem;">'
                    f'✅ {growth_file.name}</p>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<p class="sidebar-title-custom" style="margin-top:0.5rem;">📐 생육 측정 항목</p>', unsafe_allow_html=True)

    if env_file is None and growth_file is None:
        st.markdown('<p style="color:#5a7a94;font-size:0.8rem;">CSV를 먼저 업로드해 주세요.</p>', unsafe_allow_html=True)
    else:
        env_df, growth_df = load_and_standardize(env_file, growth_file)
        measure_cols = [c for c in ["잎 수", "지상부 길이", "지하부 길이", "생중량", "지상부 질량", "지하부 질량"]
                        if c in growth_df.columns]
        if measure_cols:
            selected_measure = st.selectbox(
                "기본 지표 선택",
                measure_cols,
                format_func=lambda x: {
                    "잎 수": "🌿 잎 수",
                    "지상부 길이": "📏 지상부 길이",
                    "지하부 길이": "🌱 지하부 길이",
                    "생중량": "⚖️ 생중량",
                    "지상부 질량": "🏋️ 지상부 질량",
                    "지하부 질량": "🪱 지하부 질량",
                }.get(x, x),
                help="차트 전반의 기준이 되는 지표를 선택하세요.",
            )

    st.divider()
    st.markdown('<p class="sidebar-title-custom" style="margin-top:0.5rem;">📊 빠른 정보</p>', unsafe_allow_html=True)
    if env_file and growth_file:
        env_df, growth_df = load_and_standardize(env_file, growth_file)
        sn = get_school_name(env_file or growth_file)
        st.markdown(f'<p style="color:#7fb3d8;font-size:0.82rem;font-weight:600;">🏫 {sn}</p>', unsafe_allow_html=True)
        if not growth_df.empty:
            st.markdown(f'<p style="color:#a8c4d8;font-size:0.8rem;">개체 수: {len(growth_df)}개체</p>', unsafe_allow_html=True)
        if not env_df.empty:
            times = env_df["time"].dropna()
            if len(times) >= 2:
                st.markdown(f'<p style="color:#a8c4d8;font-size:0.8rem;">측정 기간: '
                            f'{times.min().strftime("%m/%d")}~{times.max().strftime("%m/%d")}</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#5a7a94;font-size:0.78rem;">파일 2개를 모두 업로드하면 정보가 표시됩니다.</p>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<p style="color:#3a5a72;font-size:0.7rem;text-align:center;margin-top:1rem;">'
                '극지식물 생육 분석 · 인천송천고</p>', unsafe_allow_html=True)

# 양쪽 파일 모두 없으면 정지
if env_file is None and growth_file is None:
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                min-height:60vh;text-align:center;padding:2rem;">
      <div style="font-size:4rem;margin-bottom:1rem;">🌿</div>
      <p style="font-family:'Inter',sans-serif;font-size:1.4rem;font-weight:700;color:#1a5276;margin-bottom:0.5rem;">
        데이터를 업로드해 주세요</p>
      <p style="font-family:'Noto Sans KR',sans-serif;font-size:0.95rem;color:#5a7a94;max-width:400px;">
        사이드바의 CSV 업로드 영역에 <b>환경 데이터</b>와 <b>생육 결과 데이터</b>를
        순서대로 올려주시면 대시보드가 바로 시작됩니다.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

env_df, growth_df = load_and_standardize(env_file, growth_file)
school_name = get_school_name(env_file or growth_file)

# ─────────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:1.5rem;">
  <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;">
    <span style="font-size:2.2rem;">🌿</span>
    <div>
      <div class="dashboard-title">{school_name} 극지식물 생육 분석</div>
      <div class="dashboard-subtitle">
        개체별 생육 차이 &amp; 환경 데이터 인사이트 대시보드
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 탭
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📋  개요 &amp; 환경 데이터",
    "📈  산점도 &amp; 상관 분석",
    "🎯  분석 결론",
])

# ══════════════════════════════════════════════
# 탭 1 — 개요 & 환경 데이터
# ══════════════════════════════════════════════
with tab1:
    try:
        if not env_df.empty:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🌡️ 환경 데이터 개요</div>', unsafe_allow_html=True)

            env_left, env_right = st.columns(2)
            with env_left:
                if "time" in env_df.columns and "temperature" in env_df.columns:
                    d = env_df[["time", "temperature"]].dropna().sort_values("time")
                    if len(d) >= 2:
                        fig = make_line_chart(env_df, "time", "temperature",
                                              "시간별 온도 변화 (℃)", PALETTE["sky"])
                        if fig:
                            st.plotly_chart(fig, width="stretch", key="env_temp")
                        else:
                            st.info("온도 데이터가 충분하지 않습니다.")
                    else:
                        st.info("온도 데이터가 충분하지 않습니다.")
                else:
                    st.info("온도 데이터가 없습니다.")

            with env_right:
                if "time" in env_df.columns and "humidity" in env_df.columns:
                    d = env_df[["time", "humidity"]].dropna().sort_values("time")
                    if len(d) >= 2:
                        fig = make_line_chart(env_df, "time", "humidity",
                                              "시간별 습도 변화 (%)", PALETTE["ice"])
                        if fig:
                            st.plotly_chart(fig, width="stretch", key="env_hum")
                        else:
                            st.info("습도 데이터가 충분하지 않습니다.")
                    else:
                        st.info("습도 데이터가 충분하지 않습니다.")
                else:
                    st.info("습도 데이터가 없습니다.")

            numeric_env = [c for c in ["temperature", "humidity", "ph", "ec"] if c in env_df.columns]
            if numeric_env:
                stat_cols = st.columns(len(numeric_env))
                label_map = {
                    "temperature": ("평균 온도", "℃",   "accent-blue"),
                    "humidity":    ("평균 습도", "%",    "accent-lime"),
                    "ph":          ("평균 pH",   "-",    "accent-gold"),
                    "ec":          ("평균 EC",   "mS/cm", "accent-coral"),
                }
                for col, sc in zip(numeric_env, stat_cols):
                    vals = env_df[col].dropna()
                    if len(vals) >= 1:
                        _, unit, cls = label_map.get(col, (col, "", ""))
                        mean_v = vals.mean()
                        std_v  = vals.std() if len(vals) >= 2 else 0
                        sc.markdown(f"""
                        <div class="stat-card">
                          <div class="stat-card-label">{label_map[col][0]}</div>
                          <div class="stat-card-value {cls}">
                            {mean_v:.1f}<span style="font-size:0.85rem;color:#8aa0b5;font-weight:400;"> ± {std_v:.1f} {unit}</span>
                          </div>
                        </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-card">🌡️ 환경 데이터가 아직 업로드되지 않았습니다. 사이드바에서 CSV 파일을 올려주세요.</div>', unsafe_allow_html=True)

        st.divider()

        if not growth_df.empty:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🌱 생육 결과 데이터</div>', unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            indicators = []
            if "생중량" in growth_df.columns:
                bw = growth_df["생중량"].dropna()
                if len(bw) >= 1:
                    indicators.append(("개체 수", str(len(growth_df)), "accent-blue"))
                    indicators.append(("평균 생중량", f"{bw.mean():.2f}g", "accent-coral"))
            else:
                indicators.append(("개체 수", str(len(growth_df)), "accent-blue"))
                if {"지상부 질량", "지하부 질량"} <= set(growth_df.columns):
                    gmm = (growth_df["지상부 질량"] + growth_df["지하부 질량"]).dropna()
                    if len(gmm) >= 1:
                        indicators.append(("평균 생중량\n(계산)", f"{gmm.mean():.2f}g", "accent-coral"))

            if "잎 수" in growth_df.columns:
                lv = growth_df["잎 수"].dropna()
                if len(lv) >= 1:
                    indicators.append(("평균 잎 수", f"{lv.mean():.1f}장", "accent-lime"))

            if "지상부 길이" in growth_df.columns:
                sl = growth_df["지상부 길이"].dropna()
                if len(sl) >= 1:
                    indicators.append(("평균 지상부 길이", f"{sl.mean():.1f}mm", "accent-blue"))

            for i, (label, value, cls) in enumerate(indicators[:4]):
                if i < 4:
                    col_idx = f"c{i+1}"
                    locals()[col_idx].markdown(f"""
                    <div class="stat-card">
                      <div class="stat-card-label">{label.replace(chr(10),'<br>')}</div>
                      <div class="stat-card-value {cls}">{value}</div>
                    </div>""", unsafe_allow_html=True)

            st.divider()
            st.markdown('<div class="section-title">🔬 우리의 가설</div>', unsafe_allow_html=True)

            hypotheses = [
                ("지상부 길이와 지하부 길이는 양의 상관관계가 있다.",
                 "잎이 자라는 만큼 뿌리도 함께 자라는 극지식물의 특징을 반영합니다."),
                ("잎의 개수와 생중량의 관계가 식물의 생장을 가장 잘 나타낸다.",
                 "잎 수는 광합성 기관과 직결되므로 전체 생체량을 설명하는 주요 지표입니다."),
                ("지상부 길이와 생중량, 지하부 길이와 생중량은 약한 상관관계가 있다.",
                 "길이만으로는 부피·밀도를 반영하기 어려워 상관계수가 상대적으로 낮게 나타납니다."),
            ]
            for i, (title, desc) in enumerate(hypotheses, 1):
                st.markdown(f"""
                <div class="hypothesis-card" style="display:flex;align-items:flex-start;">
                  <span class="hypothesis-num">{i}</span>
                  <div>
                    <p style="font-family:'Inter',sans-serif;font-weight:600;font-size:0.92rem;
                              color:#1a2a3a;margin:0 0 0.2rem;">{title}</p>
                    <p style="font-family:'Noto Sans KR',sans-serif;font-size:0.82rem;
                              color:#5a7a94;margin:0;">{desc}</p>
                  </div>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-card">🌱 생육 결과 데이터가 아직 업로드되지 않았습니다. 사이드바에서 CSV 파일을 올려주세요.</div>', unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")

# ══════════════════════════════════════════════
# 탭 2 — 산점도 & 상관 분석
# ══════════════════════════════════════════════
with tab2:
    try:
        if growth_df.empty and env_df.empty:
            st.markdown('<div class="info-card">📈 분석할 데이터가 업로드되지 않았습니다. 사이드바에서 CSV 파일 2개를 모두 올려주세요.</div>', unsafe_allow_html=True)
        else:
            if not growth_df.empty:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">📊 생육 지표 간 관계 — 산점도</div>', unsafe_allow_html=True)

                scatter_configs = [
                    ("생중량",        "잎 수",         "잎 수 vs 생중량 — 생장 대표 지표"),
                    ("생중량",        "지상부 길이",   "지상부 길이 vs 생중량"),
                    ("생중량",        "지하부 길이",   "지하부 길이 vs 생중량"),
                    ("지하부 길이",   "지상부 길이",   "지상부 길이 vs 지하부 길이"),
                ]
                for y_col, x_col, title in scatter_configs:
                    if y_col in growth_df.columns and x_col in growth_df.columns:
                        fig = make_scatter_with_trend(growth_df, x_col, y_col, title)
                        if fig:
                            st.plotly_chart(fig, width="stretch", key=f"scatter_{x_col}_{y_col}")
                        else:
                            st.info(f"{x_col} vs {y_col} — 데이터가 충분하지 않습니다.")
                    else:
                        st.info(f"{x_col} 또는 {y_col} 데이터가 없습니다.")

                st.markdown('</div>', unsafe_allow_html=True)
                st.divider()

            if not growth_df.empty:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">🔢 상관계수 행렬</div>', unsafe_allow_html=True)

                corr_cols = [c for c in ["잎 수", "지상부 길이", "지상부 질량", "지하부
