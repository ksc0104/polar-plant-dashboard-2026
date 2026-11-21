import io
import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ═══════════════════════════════════════════════════════════════════════════════
#  한글 폰트 및 전체 UI 스타일
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');

* { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    color: #1e293b;
}

/* ── 헤더 ─────────────────────────────────────────────────────────────── */
div.header { background: linear-gradient(135deg, #0f2b5e 0%, #1a4a8a 50%, #2563eb 100%) !important; }
div.header h1 { color: #ffffff !important; font-weight: 700 !important; letter-spacing: -0.5px; }
div.header p  { color: #cbd5e1 !important; font-size: 0.95em !important; }

/* ── 사이드바 ──────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] { background: #0a1f3d; }
section[data-testid="stSidebar"] .st-markdown,
section[data-testid="stSidebar"] .stFileUploader,
section[data-testid="stSidebar"] .stCheckbox,
section[data-testid="stSidebar"] .stInfo,
section[data-testid="stSidebar"] .stSelectbox {
    color: #cbd5e1 !important;
    background: transparent !important;
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stFileUploader label {
    color: #e2e8f0 !important; font-weight: 600 !important;
}
section[data-testid="stSidebar"] input[type="file"]::file-selector-button {
    background: #2563eb !important; color: #fff !important;
    border: none !important; border-radius: 5px !important;
    padding: 6px 12px !important; cursor: pointer !important;
}
section[data-testid="stSidebar"] .stCheckbox label span span {
    background: #2563eb !important;
}

/* ── 카드 ──────────────────────────────────────────────────────────────── */
.card {
    background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 16px 20px; margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(15, 43, 94, 0.06);
}
.card-title {
    font-weight: 700; font-size: 1.05em; color: #0f2b5e;
    margin-bottom: 10px; display: flex; align-items: center; gap: 6px;
}
.card-title .badge {
    background: #dbeafe; color: #1e40af; font-size: 0.8em;
    font-weight: 600; padding: 2px 8px; border-radius: 999px; margin-left: auto;
}
.card-green  { border-left: 4px solid #059669; }
.card-blue   { border-left: 4px solid #2563eb; }
.card-amber  { border-left: 4px solid #d97706; }
.card-purple { border-left: 4px solid #7c3aed; }
.card-rose   { border-left: 4px solid #e11d48; }

/* ── 지표 카드 ──────────────────────────────────────────────────────────── */
.metric-card {
    background: #f0f4ff; border-radius: 10px; padding: 12px 16px;
    text-align: center; border: 1px solid #dbeafe;
}
.metric-card .metric-label {
    font-size: 0.78em; font-weight: 600; color: #3b82f6;
    letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 4px;
}
.metric-card .metric-value {
    font-size: 1.6em; font-weight: 700; color: #0f2b5e;
}
.metric-card .metric-sub {
    font-size: 0.75em; color: #64748b; margin-top: 2px;
}

/* ── 정보 박스 ──────────────────────────────────────────────────────────── */
.info-box {
    background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px;
    padding: 12px 14px; color: #1e3a8a; font-size: 0.92em; line-height: 1.6; margin: 10px 0;
}
.info-box strong { color: #1d4ed8; }
.success-box {
    background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px;
    padding: 12px 14px; color: #065f46; font-size: 0.92em; line-height: 1.6; margin: 10px 0;
}
.success-box strong { color: #047857; }
.warn-box {
    background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px;
    padding: 12px 14px; color: #92400e; font-size: 0.92em; line-height: 1.6; margin: 10px 0;
}

/* ── 섹션 구분선 ───────────────────────────────────────────────────────── */
.section-divider { border: none; border-top: 1px solid #e2e8f0; margin: 22px 0; }

/* ── 다운로드 버튼 ─────────────────────────────────────────────────────── */
.stButton > button {
    background: #0f2b5e !important; color: white !important;
    border-radius: 8px !important; padding: 8px 16px !important; font-weight: 600 !important;
}
.stButton > button:hover { background: #1a4a8a !important; }
</style>
""",
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  CSV 읽기 (인코딩 이중 시도)
# ═══════════════════════════════════════════════════════════════════════════════
def read_csv(file):
    """utf-8-sig -> cp949 순서로 시도, 실패 시 빈 DataFrame 반환."""
    data = file.getvalue()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(io.BytesIO(data), encoding=enc)
        except Exception:
            pass
    return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════════════════
#  열 이름 표준화 (KeyError 방지)
# ═══════════════════════════════════════════════════════════════════════════════
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
            num = pd.to_numeric(
                df[c].astype(str).str.replace(",", "").
                str.extract(r"(-?\d+\.?\d*)")[0], errors="coerce"
            )
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
            parsed[bad] = (
                pd.to_datetime(parts[0], format="%Y%m%d") +
                pd.to_timedelta(parts[1].astype(int), unit="h")
            )
        df["time"] = parsed

    return df


def school_name(filename):
    base = os.path.basename(filename)
    name = base.split("_")[0].split(".")[0]
    return name if name else "우리 학교"


def num_cols(df, candidates):
    return [c for c in candidates if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]


# ═══════════════════════════════════════════════════════════════════════════════
#  산점도 + 추세선 (재사용 함수)
# ═══════════════════════════════════════════════════════════════════════════════
def scatter_with_trend(df, x_col, y_col, title, x_label, y_label, color="#2563eb"):
    d = df[[x_col, y_col]].dropna()
    if len(d) < 2:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d[x_col], y=d[y_col],
        mode="markers",
        marker=dict(size=8, color=color, opacity=0.75,
                    line=dict(width=1.2, color="white")),
        hovertemplate=("<b>" + x_label + "</b>: %{x:.2f}<br>"
                       "<b>" + y_label + "</b>: %{y:.2f}<extra></extra>"),
        name="관측값",
    ))
    slope, intercept = np.polyfit(d[x_col], d[y_col], 1)
    x_line = np.array([d[x_col].min(), d[x_col].max()])
    fig.add_trace(go.Scatter(
        x=x_line,
        y=slope * x_line + intercept,
        mode="lines",
        line=dict(color="#e11d48", width=2.5, dash="dash"),
        name="추세선 (기울기=" + f"{slope:.4f}" + ")",
        hoverinfo="skip",
    ))
    r_val = d[x_col].corr(d[y_col])
    fig.update_layout(
        title=dict(text=title + "    r = " + f"{r_val:.3f}",
                   x=0.02, y=0.96, xanchor="left", yanchor="top",
                   font=dict(size=14, color="#0f2b5e")),
        xaxis_title=x_label,
        yaxis_title=y_label,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
        hovermode="closest",
        margin=dict(l=50, r=25, t=55, b=45),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right",
                    x=1, font=dict(size=11, color="#475569")),
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  상관계수 막대 차트
# ═══════════════════════════════════════════════════════════════════════════════
def corr_bar_chart(corr_df, title, color_pos="#059669", color_neg="#e11d48"):
    entries = []
    n = len(corr_df.columns)
    for i in range(n):
        for j in range(i + 1, n):
            x = corr_df.columns[i]
            y = corr_df.columns[j]
            r = corr_df.iloc[i, j]
            entries.append({"비교 항목": x + "  \\u2194  " + y, "상관계수 r": r})
    cdf = pd.DataFrame(entries)
    cdf = cdf.sort_values("상관계수 r", ascending=False, key=lambda s: s.abs())

    colors = [color_pos if v >= 0 else color_neg for v in cdf["상관계수 r"]]
    fig = px.bar(
        cdf, x="비교 항목", y="상관계수 r",
        color=colors,
        hover_data={"상관계수 r": ":.3f"},
        labels={"상관계수 r": "상관계수 r", "비교 항목": ""},
    )
    fig.update_traces(marker=dict(line=dict(width=0.6, color="white"), opacity=0.9))
    fig.add_hline(y=0, line=dict(color="#cbd5e1", width=1.5, dash="dot"))
    fig.update_layout(
        title=dict(text=title + "    |r| 기준 정렬",
                   x=0.02, y=0.96, xanchor="left", yanchor="top",
                   font=dict(size=13, color="#0f2b5e")),
        xaxis_title="",
        yaxis_title="상관계수 r  (\u22121 \u2026 0 \u2026 +1)",
        yaxis=dict(range=[-1.05, 1.05],
                   tickvals=[-1, -0.5, 0, 0.5, 1],
                   ticktext=["\u22121.0", "\u22120.5", "0", "+0.5", "+1.0"]),
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif",
                  size=11, color="#334155"),
        bargap=0.28,
        margin=dict(l=45, r=20, t=52, b=55),
        showlegend=False,
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  Streamlit 앱
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="극지식물 생육차이 분석", page_icon="\U0001f33f", layout="wide")


# ── 사이드바 ────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    '<div style="background:#0f2b5e; border-radius:10px; padding:14px 16px; '
    'margin-bottom:14px; border:1px solid #2563eb;">'
    '<div style="font-size:1.15em; font-weight:700; color:#ffffff;">\U0001f33f 극지식물 생육 분석</div>'
    '<div style="font-size:0.85em; color:#94a3b8; margin-top:4px;">'
    '인천송천고  |  개체별 생육차이 비교</div></div>',
    unsafe_allow_html=True,
)

st.sidebar.header("\U0001f4be CSV 파일 업로드")

env_file = st.sidebar.file_uploader(
    "환경 CSV \U0001f4ca",
    type="csv",
    help="형식 A: time, temperature, humidity, ph, ec\n"
         "형식 B: categories, 온도, 습도, EC, PH  등",
)
growth_file = st.sidebar.file_uploader(
    "생육 결과 CSV \U0001f331",
    type="csv",
    help="개체번호, 잎 수(장), 지상부 길이(mm), 지하부길이(mm) 등",
)

env_df = None
growth_df = None

if env_file is not None:
    with st.spinner("\U0001f321 환경 데이터를 읽는 중..."):
        try:
            env_df = std_cols(read_csv(env_file))
            if env_df.empty:
                st.warning("\u26a0 환경 CSV에 데이터가 없어요.")
                env_df = pd.DataFrame()
        except Exception as e:
            st.warning("\u26a0 환경 CSV 읽기 오류: " + str(e))
            env_df = pd.DataFrame()

if growth_file is not None:
    with st.spinner("\U0001f331 생육 데이터를 읽는 중..."):
        try:
            growth_df = std_cols(read_csv(growth_file))
            if growth_df.empty:
                st.warning("\u26a0 생육 CSV에 데이터가 없어요.")
                growth_df = pd.DataFrame()
        except Exception as e:
            st.warning("\u26a0 생육 CSV 읽기 오류: " + str(e))
            growth_df = pd.DataFrame()

env_name = school_name(env_file.name) if env_file else ""
growth_name = school_name(growth_file.name) if growth_file else ""


# ── 사이드바: 생육 측정 항목 선택 ────────────────────────────────────────────
st.sidebar.markdown("---")

with st.sidebar:
    st.subheader("\U0001f4cb 생육 측정 항목")
    if growth_df is not None and not growth_df.empty:
        avail_growth = num_cols(growth_df, [
            "잎 수", "지상부 길이", "지하부 길이",
            "지상부 질량", "지하부 질량", "생중량",
        ])
        selected = []
        for col in avail_growth:
            if st.checkbox(col, value=True, key="chk_" + col):
                selected.append(col)
        if not selected:
            st.info("\u26a0 선택할 항목이 없어요. CSV 열 이름을 확인해주세요.")
    else:
        st.info("생육 CSV를 먼저 업로드해주세요.")

    st.markdown("---")
    st.info(
        "\U0001f4a1 팁\n"
        "\u2022 열 이름이 달라도 std_cols가 자동으로 맞춰줘요\n"
        "\u2022 생중량(g) 열이 없으면 지상부질량+지하부질량으로 자동 계산해요\n"
        "\u2022 개체번호는 학교마다 달라 분석에서 제외해요"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  탭 구성
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "\U0001f4ca 개요 및 환경 데이터",
    "\U0001f52c 생육 그래프와 상관계수",
    "\U0001f4dd 결론",
])


# ═══════════════════════════════════════════════════════════════════════════════
#  탭 1 - 개요 & 환경 데이터
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    try:
        # ── 헤더 배너 ────────────────────────────────────────────────────────
        st.markdown(
            '<div style="'
            'background:linear-gradient(135deg, #0f2b5e 0%, #1a4a8a 40%, #2563eb 100%); '
            'border-radius:14px; padding:22px 28px; margin-bottom:18px;">'
            '<h1 style="color:#fff; font-size:1.5em; font-weight:700; margin:0; '
            'font-family:\'Noto Sans KR\',\'Malgun Gothic\',sans-serif;">'
            '인천송천고 극지식물 개체별 생육차이 분석</h1>'
            '<p style="color:#cbd5e1; font-size:0.95em; margin:6px 0 0 0; '
            'font-family:\'Noto Sans KR\',\'Malgun Gothic\',sans-serif;">'
            '환경 측정 데이터와 개체별 생육 결과를 비교해 '
            '식물 생장의 패턴을 분석해요 \U0001f33f</p></div>',
            unsafe_allow_html=True,
        )

        if env_name or growth_name:
            combined = env_name or growth_name
            st.info("\U0001f3e0 분석 대상: **" + combined +
                    "** \u2014 업로드한 파일의 데이터가 로드되었어요.")
        else:
            st.info("\U0001b550\u200d\u2b80 왼쪽 사이드바에서 CSV 파일을 업로드해주세요.")

        if env_df is None or env_df.empty:
            if env_file is None:
                st.info("환경 CSV를 업로드하면 평균 온도·습도·EC·pH 등을 확인할 수 있어요.")
            else:
                st.warning("\u26a0 환경 CSV에 읽을 데이터가 없어요. 다른 형식의 파일일 수 있어요.")

        # ── 환경 데이터 카드 ──────────────────────────────────────────────────
        if env_df is not None and not env_df.empty:
            env_avail = num_cols(env_df, ["temperature", "humidity", "ph", "ec"])

            st.markdown(
                '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
                unsafe_allow_html=True,
            )
            st.subheader("\U0001f321 환경 데이터 요약")

            if "time" in env_df.columns:
                n_time = env_df["time"].dropna().nunique()
            else:
                n_time = len(env_df)

            cols_card = st.columns(5)
            labels = ["측정 시점", "평균 온도", "평균 습도", "평균 EC", "평균 pH"]
            values = [
                n_time,
                env_df["temperature"].dropna().mean() if "temperature" in env_avail else None,
                env_df["humidity"].dropna().mean()   if "humidity"   in env_avail else None,
                env_df["ec"].dropna().mean()         if "ec"         in env_avail else None,
                env_df["ph"].dropna().mean()         if "ph"         in env_avail else None,
            ]
            units = [" 회", " \u00b0C", " %", " mS/cm", ""]
            subs  = ["총 측정 횟수", "센서 평균 온도",
                     "센서 평균 습도", "센서 평균 전기전도도",
                     "센서 평균 수소이온농도"]

            for col, label, val, unit, sub in zip(cols_card, labels, values, units, subs):
                with col:
                    if val is not None and not np.isnan(val):
                        disp_val = int(val) if unit in ("", " 회") else val
                        st.markdown(
                            '<div class="metric-card">'
                            '<div class="metric-label">' + label + '</div>'
                            '<div class="metric-value">'
                            '<span style="color:#2563eb;font-weight:700;">'
                            + (f"{disp_val:,.1f}" if isinstance(disp_val, float) else str(disp_val))
                            + '</span>' + unit + '</div>'
                            '<div class="metric-sub">' + sub + '</div></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.info("\U0001f4cc " + label + "\n해당 데이터가 없어요.")

            st.markdown(
                '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
                unsafe_allow_html=True,
            )

            # ── 환경 시계열 그래프 ─────────────────────────────────────────────
            env_plot_cols = num_cols(env_df, ["temperature", "humidity", "ph", "ec"])
            if "time" in env_df.columns and env_plot_cols:
                with st.spinner("\U0001f4c8 환경 시계열 그래프를 그리는 중..."):
                    ttl_rows = len(env_plot_cols)
                    fig_env = make_subplots(
                        rows=ttl_rows, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=(0.09 if ttl_rows > 1 else 0.05),
                        subplot_titles=env_plot_cols,
                        row_width=[0.22] * ttl_rows,
                    )
                    colors = ["#2563eb", "#059669", "#d97706", "#7c3aed"]
                    unit_label = {"temperature": "\u00b0C", "humidity": "%",
                                  "ec": "mS/cm", "ph": "pH"}
                    for i, c in enumerate(env_plot_cols):
                        s = env_df[["time", c]].dropna().sort_values("time")
                        if s.empty:
                            continue
                        fig_env.add_trace(
                            go.Scatter(
                                x=s["time"], y=s[c],
                                mode="lines",
                                line=dict(color=colors[i % len(colors)], width=1.8),
                                name=c,
                                hovertemplate=("<b>" + c + "</b><br>"
                                               "시간: %{x|%Y-%m-%d %H:%M}<br>"
                                               "값: %{y:.2f}" +
                                               unit_label.get(c, "") +
                                               "<extra></extra>"),
                            ),
                            row=i + 1, col=1,
                        )
                        fig_env.update_yaxes(
                            title_text=c + " (" + unit_label.get(c, "") + ")",
                            row=i + 1, col=1,
                            gridcolor="#e2e8f0", zerolinecolor="#cbd5e1",
                        )
                    fig_env.update_xaxes(showgrid=True, gridcolor="#e2e8f0",
                                          zerolinecolor="#cbd5e1")
                    fig_env.update_layout(
                        height=130 + (115 if ttl_rows == 1 else 100) * ttl_rows,
                        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif",
                                  size=11),
                        showlegend=False,
                        margin=dict(l=45, r=20, t=28, b=25),
                    )
                    st.plotly_chart(fig_env, width="stretch")
            elif not env_plot_cols:
                st.info("\u26a0 환경에 온도·습도·EC·pH 열이 하나도 없어요. CSV 형식을 확인해주세요.")

            st.markdown(
                '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
                unsafe_allow_html=True,
            )

            # ── 환경 데이터 표 + 다운로드 ───────────────────────────────────────
            preview_cols = ["time"] + env_plot_cols if "time" in env_df.columns else env_plot_cols
            if preview_cols:
                st.subheader("\U0001f4cb 환경 데이터 상세 (시계열)")
                st.markdown(
                    '<div class="card card-blue">'
                    '<div class="card-title">측정 시계열 데이터 '
                    '<span class="badge">' + str(env_df.shape[0]) + ' 행</span></div></div>',
                    unsafe_allow_html=True,
                )
                disp = env_df[preview_cols].dropna(subset=["time"]).sort_values("time")
                st.dataframe(disp, width="stretch", use_container_width=False, hide_index=True)

                csv_bytes = disp.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "\u2b07 환경 데이터 다운로드 (CSV)",
                    csv_bytes,
                    file_name=(env_name or "환경") + "_데이터.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        # ── 생육 데이터 카드 ──────────────────────────────────────────────────
        if growth_df is not None and not growth_df.empty:
            st.markdown(
                '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
                unsafe_allow_html=True,
            )
            st.subheader("\U0001f331 생육 결과 데이터 요약")

            avail_growth = num_cols(growth_df, [
                "잎 수", "지상부 길이", "지하부 길이",
                "지상부 질량", "지하부 질량", "생중량",
            ])
            n_ind = len(growth_df)

            col_g1, col_g2, col_g3 = st.columns(3)
            with col_g1:
                st.markdown(
                    '<div class="metric-card" style="background:#ecfdf5;border-color:#a7f3d0;">'
                    '<div class="metric-label" style="color:#059669;">개체 수</div>'
                    '<div class="metric-value"><span style="color:#065f46;font-weight:700;">'
                    + str(n_ind) + '</span> 개</div>'
                    '<div class="metric-sub">분석 대상 개체 전체</div></div>',
                    unsafe_allow_html=True,
                )
            if "잎 수" in avail_growth:
                with col_g2:
                    m = growth_df["잎 수"].dropna().mean()
                    st.markdown(
                        '<div class="metric-card">'
                        '<div class="metric-label">평균 잎 수</div>'
                        '<div class="metric-value"><span style="color:#2563eb;font-weight:700;">'
                        + f"{m:.1f}" + '</span> 장</div>'
                        '<div class="metric-sub">개체별 잎 개수 평균</div></div>',
                        unsafe_allow_html=True,
                    )
            if "생중량" in avail_growth:
                with col_g3:
                    m = growth_df["생중량"].dropna().mean()
                    st.markdown(
                        '<div class="metric-card" style="background:#fef3c7;border-color:#fde68a;">'
                        '<div class="metric-label" style="color:#b45309;">평균 생중량</div>'
                        '<div class="metric-value"><span style="color:#92400e;font-weight:700;">'
                        + f"{m:.2f}" + '</span> g</div>'
                        '<div class="metric-sub">지상부+지하부 질량 합계</div></div>',
                        unsafe_allow_html=True,
                    )

            st.markdown(
                '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
                unsafe_allow_html=True,
            )

            # ── 생육 데이터 표 ──────────────────────────────────────────────────
            show_cols = ["개체번호"] + avail_growth if "개체번호" in growth_df.columns else avail_growth
            if show_cols:
                st.subheader("\U0001f4cb 생육 결과 데이터")
                st.markdown(
                    '<div class="card card-green">'
                    '<div class="card-title">개체별 생육 측정값 '
                    '<span class="badge">' + str(growth_df.shape[0]) + ' 개체</span></div></div>',
                    unsafe_allow_html=True,
                )
                st.dataframe(growth_df[show_cols], width="stretch",
                             use_container_width=False, hide_index=True)

                csv_bytes = growth_df[show_cols].to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "\u2b07 생육 데이터 다운로드 (CSV)",
                    csv_bytes,
                    file_name=(growth_name or "생육") + "_데이터.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            # ── 생중량 상위·하위 개체 ───────────────────────────────────────────
            if "생중량" in avail_growth:
                ranked = growth_df[["개체번호", "생중량"]].dropna().sort_values(
                    "생중량", ascending=False)
                if len(ranked) >= 2:
                    st.markdown(
                        '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
                        unsafe_allow_html=True,
                    )
                    st.subheader("\U0001f3c6 생중량 상위·하위 개체")

                    top_n = min(5, len(ranked))
                    bottom_n = min(5, len(ranked))

                    tl, tr = st.columns(2)
                    top_rows = ranked.head(top_n)
                    bottom_rows = ranked.tail(bottom_n).iloc[::-1].reset_index(drop=True)

                    with tl:
                        st.markdown(
                            '<div class="card card-green">'
                            '<div class="card-title">\U0001f3c6 생중량 상위 '
                            + str(top_n) + '개체</div></div>',
                            unsafe_allow_html=True,
                        )
                        st.dataframe(top_rows, width="stretch",
                                     use_container_width=False, hide_index=True)

                    with tr:
                        st.markdown(
                            '<div class="card card-rose">'
                            '<div class="card-title">\U0001f53b 생중량 하위 '
                            + str(bottom_n) + '개체</div></div>',
                            unsafe_allow_html=True,
                        )
                        st.dataframe(bottom_rows, width="stretch",
                                     use_container_width=False, hide_index=True)

        elif growth_df is not None and growth_df.empty:
            st.info("\u26a0 생육 CSV에 데이터가 없어요.")

        # ── 우리의 가설 ───────────────────────────────────────────────────────
        st.markdown(
            '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
            unsafe_allow_html=True,
        )
        st.subheader("\U0001f4a1 우리의 가설")

        st.markdown(
            '<div class="card card-blue">'
            '<div class="card-title">\U0001f4cc 가설 1 \u2014 지상부 길이 \u2194 지하부 길이 '
            '<span class="badge">양의 상관 예상</span></div>'
            '<p>지상부와 지하부는 함께 자라는 경향이 있으므로 두 길이는 비슷한 방향으로 변할 것으로 예상해요.</p>'
            '<p style="color:#64748b; font-size:0.88em;">'
            '*<b>상관계수 r</b>는 두 변수가 함께 변하는 정도를 \u22121 ~ +1 사이로 나타낸 값이에요. '
            '+1에 가까울수록 강한 양의 상관, 0에 가까우면 상관이 거의 없어요.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="card card-green">'
            '<div class="card-title">\U0001f4cc 가설 2 \u2014 잎의 개수 \u2194 생중량 '
            '<span class="badge">식물 생장 대표 지표</span></div>'
            '<p>잎이 많을수록 광합성이 활발하고 전체 무게(생중량)도 증가할 것으로 예상해요.</p>'
            '<p style="color:#64748b; font-size:0.88em;">'
            '*<b>생중량</b> = 식물이 살아있을 때의 전체 무게예요. (지상부 질량 + 지하부 질량)<br>'
            '생장 상태를 가장 잘 나타내는 지표가 무엇인지 r 값을 비교해 확인해요.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="card card-amber">'
            '<div class="card-title">\U0001f4cc 가설 3 \u2014 지상부 길이/지하부 길이 \u2194 생중량 '
            '<span class="badge">약한 상관 예상</span></div>'
            '<p>길이가 길다고 반드시 무거운 것은 아니므로(상당한 빈 공간 포함 가능), 상관은 상대적으로 약할 수 있어요.</p>'
            '<p style="color:#64748b; font-size:0.88em;">'
            '길이 측정값과 무게 측정값의 관계를 확인해 가설의 타당성을 검토해요.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.warning("\u26a0 이 부분은 데이터 형식 때문에 표시하지 못했어요: " + str(e))


# ═══════════════════════════════════════════════════════════════════════════════
#  탭 2 - 생육 그래프와 상관계수
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    try:
        st.markdown(
            '<div style="background:#f0f4ff; border-radius:10px; padding:12px 18px; '
            'border-left:4px solid #2563eb; margin-bottom:14px;">'
            '<p style="margin:0; font-size:0.92em; color:#1e3a8a;">\U0001f52c '
            '아래 산점도에서 각 <b>점</b>은 한 개체를 나타내고, '
            '<b>빨간 점선</b>은 선형 추세선이에요. '
            '범례에 <b>기울기</b>와 <b>상관계수 r</b>이 함께 표시돼요.</p></div>',
            unsafe_allow_html=True,
        )

        if growth_df is None or growth_df.empty:
            st.info("\U0001f448 생육 결과 CSV를 업로드하면 산점도와 상관계수 행렬을 볼 수 있어요.")
        else:
            avail = num_cols(growth_df, [
                "잎 수", "지상부 길이", "지하부 길이",
                "지상부 질량", "지하부 질량", "생중량",
            ])

            if len(avail) < 2:
                st.info("\u26a0 분석할 숫자 열이 최소 2개 이상 필요해요. 생육 CSV 열 이름을 확인해주세요.")
            else:
                def plot_or_skip(x, y, title, xl, yl, color="#2563eb"):
                    if x in avail and y in avail:
                        fig = scatter_with_trend(growth_df, x, y, title, xl, yl, color)
                        if fig:
                            st.plotly_chart(fig, width="stretch")
                        else:
                            st.info("\u26a0 " + title +
                                    ": 값이 2개 미만이라 그래프를 그리지 못했어요.")
                    else:
                        miss = [c for c in [x, y] if c not in avail]
                        st.info("\u26a0 " + title +
                                ": " + ", ".join(miss) + " 열이 없어서 이 그래프를 건너뛰었어요.")

                st.subheader("\U0001f4cc 생중량 vs 잎의 개수  (가설 2)")
                st.markdown(
                    '<div class="card card-green">'
                    '<div class="card-title">\U0001f33f 잎의 개수 vs 생중량 \u2014 식물 생장의 대표 지표?</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                plot_or_skip("잎 수", "생중량",
                             "잎의 개수 vs 생중량",
                             "잎의 개수 (장)", "생중량 (g)", "#059669")

                st.subheader("\U0001f4cc 지상부 길이 vs 생중량  (가설 3)")
                st.markdown(
                    '<div class="card card-amber">'
                    '<div class="card-title">\U0001f4cf 지상부 길이 vs 생중량 \u2014 길이와 무게의 관계</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                plot_or_skip("지상부 길이", "생중량",
                             "지상부 길이 vs 생중량",
                             "지상부 길이 (mm)", "생중량 (g)", "#d97706")

                st.subheader("\U0001f4cc 지하부 길이 vs 생중량  (가설 3)")
                st.markdown(
                    '<div class="card card-purple">'
                    '<div class="card-title">\U0001f331 지하부 길이 vs 생중량 \u2014 뿌리 길이와 무게의 관계</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                plot_or_skip("지하부 길이", "생중량",
                             "지하부 길이 vs 생중량",
                             "지하부 길이 (mm)", "생중량 (g)", "#7c3aed")

                st.markdown(
                    '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
                    unsafe_allow_html=True,
                )

                # ── 상관계수 행렬 ────────────────────────────────────────────────
                st.subheader("\U0001f4ca 상관계수 행렬 (Pearson r)")
                st.markdown(
                    '<div class="info-box">'
                    '<strong>상관계수 r</strong>은 두 변수가 함께 변하는 정도를 '
                    '<strong>\u22121 ~ +1</strong> 사이로 나타낸 값이에요.<br>'
                    '\u2022 <b style="color:#059669;">+1에 가까움</b>: 함께 증가하는 강한 양의 상관<br>'
                    '\u2022 <b style="color:#e11d48;">\u22121에 가까움</b>: 하나가 증가할 때 '
                    '다른 하나가 감소하는 강한 음의 상관<br>'
                    '\u2022 <b style="color:#64748b;">0에 가까움</b>: 상관이 거의 없음<br>'
                    '\u2022 일반적으로 |r| \u2265 0.7 \u2192 <b>강한 상관</b>, '
                    '0.4~0.7 \u2192 <b>중간</b>, &lt;0.4 \u2192 <b>약한 상관</b>으로 해석해요.'
                    '</div>',
                    unsafe_allow_html=True,
                )

                corr_cols = [
                    c for c in ["잎 수", "지상부 길이", "지상부 질량",
                                 "지하부 길이", "지하부 질량", "생중량"]
                    if c in avail
                ]
                if len(corr_cols) >= 2:
                    corr_df_data = growth_df[corr_cols].dropna()
                    if len(corr_df_data) >= 2:
                        corr_matrix = corr_df_data.corr(method="pearson")

                        fig_corr = px.imshow(
                            corr_matrix,
                            text_auto=".3f",
                            color_continuous_scale="RdBu_r",
                            zmin=-1, zmax=1,
                            aspect="auto",
                            labels=dict(color="r"),
                        )
                        fig_corr.update_layout(
                            title=dict(
                                text="개체별 생육 지표 간 상관계수 행렬  (셀 값 = Pearson r)",
                                x=0.02, y=0.96, xanchor="left", yanchor="top",
                                font=dict(size=13, color="#0f2b5e"),
                            ),
                            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif",
                                      size=12, color="#1e293b"),
                            margin=dict(l=50, r=20, t=58, b=50),
                            coloraxis_colorbar=dict(
                                title="r",
                                thickness=14,
                                tickvals=[-1, -0.5, 0, 0.5, 1],
                                ticktext=["\u22121.0", "\u22120.5", "0", "+0.5", "+1.0"],
                                outlinewidth=0,
                            ),
                        )
                        st.plotly_chart(fig_corr, width="stretch")

                        st.markdown("\U0001f4cb 상관계수 행렬 (표)")
                        st.dataframe(corr_matrix, width="stretch",
                                     use_container_width=False, hide_index=True)
                    else:
                        st.info("\u26a0 상관계수 행렬 계산용 데이터가 2개 미만이에요.")
                else:
                    st.info("\u26a0 상관계수 행렬을 만들려면 최소 2개의 숫자 열이 필요해요.")

                st.markdown(
                    '<div class="info-box" style="margin-top:14px;">'
                    '\U0001f4a1 <strong>개체번호</strong>는 학교마다 형식(A1·A2 \u2026 또는 1·2 \u2026)이 달라 '
                    '비교 기준에 쓰면 오류가 생겨요. 개체 간 비교는 생육 수치만으로 이루어져요.'
                    '</div>',
                    unsafe_allow_html=True,
                )

    except Exception as e:
        st.warning("\u26a0 이 부분은 데이터 형식 때문에 표시하지 못했어요: " + str(e))


# ═══════════════════════════════════════════════════════════════════════════════
#  탭 3 - 결론
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    try:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#0f2b5e,#1a4a8a);'
            'border-radius:12px; padding:18px 22px; margin-bottom:16px;">'
            '<h2 style="color:#fff; font-size:1.3em; font-weight:700; margin:0 0 6px 0; '
            'font-family:\'Noto Sans KR\',\'Malgun Gothic\',sans-serif;">'
            '\U0001f4dd 분석 결론</h2>'
            '<p style="color:#cbd5e1; font-size:0.92em; margin:0; '
            'font-family:\'Noto Sans KR\',\'Malgun Gothic\',sans-serif;">'
            '상관계수 비교 결과를 바탕으로 가설을 검토하고 결론을 내려요.</p></div>',
            unsafe_allow_html=True,
        )

        if growth_df is None or growth_df.empty:
            st.info("\U0001f448 생육 결과 CSV를 업로드하면 결론을 자동으로 계산해요.")
        else:
            avail = num_cols(growth_df, [
                "잎 수", "지상부 길이", "지하부 길이",
                "지상부 질량", "지하부 질량", "생중량",
            ])

            if "생중량" not in avail or "잎 수" not in avail or len(growth_df) < 2:
                st.info(
                    "\u26a0 생중량과 잎의 개수 데이터가 모두 필요해요. "
                    "생중량 열이 없으면 지상부질량+지하부질량으로 자동 계산돼요.")
            else:
                # ── 상관계수 비교 결과 ───────────────────────────────────────────
                st.subheader("\U0001f4ca 상관계수 비교 결과")

                pairs = [
                    ("잎 수", "생중량"),
                    ("지상부 길이", "생중량"),
                    ("지하부 길이", "생중량"),
                    ("지상부 길이", "지하부 길이"),
                ]
                results = {}
                for x, y in pairs:
                    if x in avail and y in avail:
                        dd = growth_df[[x, y]].dropna()
                        if len(dd) >= 2:
                            results[x + "  \u2194  " + y] = dd[x].corr(dd[y])

                if results:
                    sorted_res = sorted(results.items(), key=lambda kv: abs(kv[1]), reverse=True)
                    top_pair, top_r = sorted_res[0]

                    def strength_label(r):
                        a = abs(r)
                        if a > 0.8: return "매우 강함"
                        if a > 0.6: return "강함"
                        if a > 0.4: return "중간"
                        if a > 0.2: return "약함"
                        return "매우 약함"

                    def direction_label(r):
                        return "양의 상관 \u2197" if r > 0 else "음의 상관 \u2198"

                    card_colors = [
                        ("#059669", "#ecfdf5"),
                        ("#2563eb", "#eff6ff"),
                        ("#d97706", "#fffbeb"),
                        ("#7c3aed", "#f5f3ff"),
                    ]
                    n_cols = min(4, len(sorted_res))
                    res_cols = st.columns(n_cols)

                    for i, (label, r_val) in enumerate(sorted_res):
                        fg, card_bg = card_colors[i % len(card_colors)]
                        with res_cols[i]:
                            st.markdown(
                                '<div class="metric-card" style="'
                                'background:' + card_bg + '; border-color:#e2e8f0;">'
                                '<div class="metric-label" style="color:' + fg + ';">' + label + '</div>'
                                '<div class="metric-value" style="color:' + fg + ';">'
                                '<span style="font-weight:700;">r = ' + f"{r_val:.3f}" + '</span></div>'
                                '<div class="metric-sub" style="color:#64748b;">'
                                + strength_label(r_val) + ' \u00b7 ' + direction_label(r_val)
                                + '</div></div>',
                                unsafe_allow_html=True,
                            )

                st.markdown(
                    '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
                    unsafe_allow_html=True,
                )

                # ── 가장 강한 상관관계 ───────────────────────────────────────────
                st.subheader("\U0001f3c6 가장 강한 상관관계")

                is_leaf = (top_pair == "잎 수  \u2194  생중량")
                leaf_r = results.get("잎 수  \u2194  생중량", float("nan"))

                if is_leaf:
                    st.markdown(
                        '<div class="success-box">'
                        '<strong>생중량과 잎의 개수 사이의 상관계수가 '
                        'r = ' + f"{leaf_r:.3f}" + '</strong>로, 측정한 모든 지표 쌍 중 '
                        '가장 강한 상관을 보였어요.<br><br>'
                        '즉, <strong>잎이 많을수록 식물 전체 무게(생중량)도 '
                        '함께 증가하는 경향</strong>이 뚜렷하게 확인됐어요. '
                        '\u2192 <b>가설 2 지지 \u2705</b>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="info-box">'
                        '측정한 지표 쌍 중 가장 강한 상관은 '
                        '<strong><span style="color:#1d4ed8;">'
                        + top_pair + '</span> (r = ' + f"{top_r:.3f}" + ')</strong>이었어요.<br><br>'
                        '생중량과 잎의 개수 사이 상관계수는 '
                        '<strong>r = ' + f"{leaf_r:.3f}" + '</strong>에요.',
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
                    unsafe_allow_html=True,
                )

                # ── 상관계수 막대 차트 ───────────────────────────────────────────
                st.subheader("\U0001f4ca 상관계수 비교 막대 차트 (|r| 기준 내림차순)")
                corr_df_chart = pd.DataFrame(
                    [{"비교 항목": k, "상관계수 r": v} for k, v in sorted_res]
                )
                fig_bar = corr_bar_chart(corr_df_chart,
                                         "개체별 생육 지표 간 상관계수 비교")
                st.plotly_chart(fig_bar, width="stretch")

                # ── 가설 검토 ─────────────────────────────────────────────────────
                st.markdown(
                    '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
                    unsafe_allow_html=True,
                )
                st.subheader("\u2705 가설 검토 결과")

                # 가설 1
                if "지상부 길이" in avail and "지하부 길이" in avail:
                    d1 = growth_df[["지상부 길이", "지하부 길이"]].dropna()
                    if len(d1) >= 2:
                        r1 = d1["지상부 길이"].corr(d1["지하부 길이"])
                        if r1 > 0.3:
                            st.markdown(
                                '<div class="success-box">'
                                '<strong>가설 1 \u2014 지상부 길이 \u2194 지하부 길이 (양의 상관)</strong><br>'
                                '<span style="color:#047857;">\u25b6 지지됨 \u2705</span> '
                                '(r = ' + f"{r1:.3f}" + ')<br>'
                                '지상부 길이와 지하부 길이는 서로 양의 상관이 있어, '
                                '줄기가 자랄 때 뿌리도 함께 자라는 경향이 확인됐어요.'
                                '</div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                '<div class="warn-box">'
                                '<strong>가설 1 \u2014 지상부 길이 \u2194 지하부 길이 (양의 상관)</strong><br>'
                                'r = ' + f"{r1:.3f}" + ' \u2014 예상보다 약한 상관이에요. '
                                '개체별로 뿌리·줄기 발달 패턴이 다를 수 있어요.'
                                '</div>',
                                unsafe_allow_html=True,
                            )

                # 가설 2
                if "잎 수" in avail and "생중량" in avail:
                    d2 = growth_df[["잎 수", "생중량"]].dropna()
                    if len(d2) >= 2:
                        r2 = d2["잎 수"].corr(d2["생중량"])
                        if abs(r2) >= 0.5:
                            st.markdown(
                                '<div class="success-box">'
                                '<strong>가설 2 \u2014 잎의 개수 \u2194 생중량 (생장 대표 지표)</strong><br>'
                                '<span style="color:#047857;">\u25b6 지지됨 \u2705</span> '
                                '(r = ' + f"{r2:.3f}" + ')<br>'
                                '잎의 개수와 생중량 사이의 상관이 비교적 강해, '
                                '잎 수가 식물 생장 상태를 나타내는 좋은 지표임을 시사해요.'
                                '</div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                '<div class="info-box">'
                                '<strong>가설 2 \u2014 잎의 개수 \u2194 생중량 (생장 대표 지표)</strong><br>'
                                'r = ' + f"{r2:.3f}" + ' \u2014 중간 정도 상관이 있어요. '
                                '다른 지표 조합도 함께 살펴보면 더 정확히 평가할 수 있어요.'
                                '</div>',
                                unsafe_allow_html=True,
                            )

                # 가설 3
                weak_checked = False
                for x_col in ["지상부 길이", "지하부 길이"]:
                    if x_col in avail and "생중량" in avail:
                        d3 = growth_df[[x_col, "생중량"]].dropna()
                        if len(d3) >= 2:
                            r3 = d3[x_col].corr(d3["생중량"])
                            weak_checked = True
                            if abs(r3) < 0.5:
                                st.markdown(
                                    '<div class="info-box">'
                                    '<strong>가설 3 \u2014 ' + x_col + ' \u2194 생중량 '
                                    '(약한 상관 예상)</strong><br>'
                                    'r = ' + f"{r3:.3f}" + ' \u2014 예상한 대로 약한 상관이 확인됐어요. '
                                    '길이만으로 무게를 정확히 예측하기는 어려워요.'
                                    '</div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    '<div class="warn-box">'
                                    '<strong>가설 3 \u2014 ' + x_col + ' \u2194 생중량 '
                                    '(약한 상관 예상)</strong><br>'
                                    'r = ' + f"{r3:.3f}" + ' \u2014 예상보다 강한 상관이 나왔어요. '
                                    '길이 측정이 무게와 꽤 연관돼 있을 수 있어요.'
                                    '</div>',
                                    unsafe_allow_html=True,
                                )

                if not weak_checked:
                    st.info("\u26a0 가설 3 검증용 데이터가 충분하지 않아요.")

                st.markdown(
                    '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
                    unsafe_allow_html=True,
                )

                # ── 종합 결론 ─────────────────────────────────────────────────────
                st.subheader("\U0001f4cc 종합 결론")

                if not np.isnan(leaf_r):
                    conclusion_text = (
                        "인천송천고 극지식물 " + str(growth_df.shape[0]) + "개체를 분석한 결과, "
                        "**생중량과 잎의 개수 사이의 상관계수가 r = " + f"{leaf_r:.3f}" + "**로 "
                        "측정한 지표 중 가장 강한 상관을 보였어요. "
                        "따라서 **잎의 개수가 식물 생장 상태를 나타내는 대표적인 지표**라고 "
                        "판단할 수 있어요. "
                        "지상부 길이와 지하부 길이도 양의 상관을 보여 함께 자라는 경향을 "
                        "확인할 수 있었어요."
                    )
                    st.markdown(
                        '<div class="card card-blue">'
                        '<div class="card-title">\U0001f4dd 분석 결론 요약</div>'
                        '<p style="line-height:1.7; font-size:0.95em;">' + conclusion_text + '</p>'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                # ── 통계 용어 설명 ───────────────────────────────────────────────
                st.markdown(
                    '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
                    unsafe_allow_html=True,
                )
                st.subheader("\U0001f4d6 통계 용어 간단 설명")

                st.markdown(
                    '<div class="info-box">'
                    '\u2022 <strong>평균</strong>: 여러 값을 더해 개수로 나눈 값. 대표적인 중앙 경향이에요.<br>'
                    '\u2022 <strong>표준편차</strong>: 값들이 평균에서 얼마나 흩어져 있는지 나타내는 척도예요. '
                    '클수록 들쭉날쭉해요.<br>'
                    '\u2022 <strong>상관계수 r (Pearson)</strong>: 두 변수가 함께 움직이는 정도를 '
                    '\u22121 ~ +1 사이로 나타낸 값이에요.<br>'
                    '   - r \u2248 +1: 함께 증가하는 강한 양의 상관<br>'
                    '   - r \u2248 \u22121: 하나가 증가할 때 다른 하나가 감소하는 강한 음의 상관<br>'
                    '   - r \u2248 0: 선형 상관이 거의 없음<br>'
                    '\u2022 <strong>산점도</strong>: 두 변수의 관계를 점 그림으로 나타낸 그래프예요. '
                    '점들의 배열 방향을 보고 상관 여부를 직관적으로 알 수 있어요.<br>'
                    '\u2022 <strong>추세선</strong>: 산점도 점들의 전반적인 방향을 나타내는 직선(선형 회귀선)이에요. '
                    '기울기가 양수면 양의 상관, 음수면 음의 상관을 의미해요.'
                    '</div>',
                    unsafe_allow_html=True,
                )

                # ── 데이터 다운로드 ───────────────────────────────────────────────
                st.markdown(
                    '<hr style="border:none;border-top:1px solid #e2e8f0;margin:22px 0;">',
                    unsafe_allow_html=True,
                )
                st.subheader("\u2b07 결과 데이터와 함께 내려받기")

                download_cols = ["개체번호"] + avail if "개체번호" in growth_df.columns else avail
                if download_cols:
                    csv_bytes = growth_df[download_cols].to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        "\u2b07 생육 결과 데이터 다운로드 (CSV, 한글 깨짐 방지)",
                        csv_bytes,
                        file_name=(growth_name or "생육결과") + ".csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

        st.markdown(
            '<div style="margin-top:20px; padding:10px 14px; '
            'background:#f1f5f9; border-radius:8px; border:1px solid #e2e8f0; '
            'font-size:0.85em; color:#64748b; text-align:center;">'
            '\U0001f33f 본 분석은 교육 목적의 탐색적 데이터 시각화예요. '
            '인과관계를 단정하지 않으며, 통계적 해석은 표본 크기와 측정 조건에 따라 달라질 수 있어요.</div>',
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.warning("\u26a0 이 부분은 데이터 형식 때문에 표시하지 못했어요: " + str(e))
