import io
import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── 한글 폰트 (Streamlit CSS) ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
   font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ── CSV 읽기 (인코딩 이중 시도) ─────────────────────────────────────────────
def read_csv(file):
    """utf-8-sig -> cp949 순서로 시도, 실패 시 빈 DataFrame 반환."""
    data = file.getvalue()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(io.BytesIO(data), encoding=enc)
        except Exception:
            pass
    return pd.DataFrame()

# ── 열 이름 표준화 (KeyError 방지) ──────────────────────────────────────────
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

# ── 학교명 추출 (파일명에서) ─────────────────────────────────────────────────
def school_name(filename):
    base = os.path.basename(filename)
    name = base.split("_")[0].split(".")[0]
    return name if name else "우리 학교"

# ── 숫자형 열만 골라 리스트 반환 ─────────────────────────────────────────────
def num_cols(df, candidates):
    return [c for c in candidates if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]

# ── 산점도 + 추세선 (재사용 함수) ────────────────────────────────────────────
def scatter_with_trend(df, x_col, y_col, title, x_label, y_label):
    d = df[[x_col, y_col]].dropna()
    if len(d) < 2:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d[x_col], y=d[y_col],
        mode="markers",
        marker=dict(size=7, color="#2563EB", opacity=0.7),
        hovertemplate=f"{x_label}: %{{x:.2f}}<br>{y_label}: %{{y:.2f}}<extra></extra>",
    ))
    slope, intercept = np.polyfit(d[x_col], d[y_col], 1)
    x_line = np.array([d[x_col].min(), d[x_col].max()])
    fig.add_trace(go.Scatter(
        x=x_line,
        y=slope * x_line + intercept,
        mode="lines",
        line=dict(color="#DC2626", width=2, dash="dash"),
        hoverinfo="skip",
    ))
    r = d[x_col].corr(d[y_col])
    fig.update_layout(
        title=f"{title}  (r = {r:.3f})",
        xaxis_title=x_label,
        yaxis_title=y_label,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
        hovermode="closest",
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig

# ─────────────────────────────────────────────────────────────────────────────
#  Streamlit 앱
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="극지식물 생육차이 분석", layout="wide")
st.title("인천송천고 극지식물 개체별 생육차이 분석")

st.sidebar.header("데이터 업로드")
env_file    = st.sidebar.file_uploader("환경 CSV 업로드", type="csv")
growth_file = st.sidebar.file_uploader("생육 결과 CSV 업로드", type="csv")

env_df    = None
growth_df = None

if env_file is not None:
    with st.spinner("환경 데이터를 읽는 중..."):
        try:
            env_df = std_cols(read_csv(env_file))
        except Exception as e:
            st.warning(f"경고: 환경 CSV를 읽지 못했어요: {e}")
            env_df = pd.DataFrame()

if growth_file is not None:
    with st.spinner("생육 결과 데이터를 읽는 중..."):
        try:
            growth_df = std_cols(read_csv(growth_file))
        except Exception as e:
            st.warning(f"경고: 생육 CSV를 읽지 못했어요: {e}")
            growth_df = pd.DataFrame()

env_name    = school_name(env_file.name)    if env_file    else ""
growth_name = school_name(growth_file.name) if growth_file else ""

# ── 사이드바: 생육 측정 항목 선택 ────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.subheader("생육 측정 항목")
growth_candidates = [
    "잎 수", "지상부 길이", "지하부 길이",
    "지상부 질량", "지하부 질량", "생중량",
]
selected = []
for col in growth_candidates:
    if growth_df is not None and col in growth_df.columns:
        if st.sidebar.checkbox(col, value=True, key=f"chk_{col}"):
            selected.append(col)
if growth_df is None:
    st.sidebar.info("생육 CSV를 먼저 업로드해주세요.")

st.sidebar.markdown("---")
st.sidebar.info(
    "팁: 열 이름이 달라도 앱이 알아서 맞춰 읽어요.\n"
    "   생중량(g) 열이 없으면 지상부 질량 + 지하부 질량으로 자동 계산해요."
)

# ═════════════════════════════════════════════════════════════════════════════
#  탭 1 - 개요 & 환경 데이터
# ═════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["개요 및 환경 데이터", "생육 그래프와 상관계수", "결론"])

with tab1:
    try:
        st.header("개요 및 환경 데이터")

        if env_name or growth_name:
            nm = env_name or growth_name
            st.info(f"분석 대상: {nm}")
        else:
            st.info("왼쪽 사이드바에서 CSV 파일을 업로드해주세요.")

        env_has_data = env_df is not None and not env_df.empty
        if env_has_data:
            st.subheader("환경 데이터 요약")

            avail_env = num_cols(env_df, ["temperature", "humidity", "ph", "ec"])

            col1, col2, col3, col4, col5 = st.columns(5)
            if "time" in env_df.columns:
                n_time = env_df["time"].dropna().nunique()
                with col1:
                    st.metric("측정 시점 수", f"{n_time} 회")
            if "temperature" in avail_env:
                t_mean = env_df["temperature"].dropna().mean()
                with col2:
                    st.metric("평균 온도", f"{t_mean:.1f} C")
            if "humidity" in avail_env:
                h_mean = env_df["humidity"].dropna().mean()
                with col3:
                    st.metric("평균 습도", f"{h_mean:.1f} %")
            if "ec" in avail_env:
                ec_mean = env_df["ec"].dropna().mean()
                with col4:
                    st.metric("평균 EC", f"{ec_mean:.2f} mS/cm")
            if "ph" in avail_env:
                ph_mean = env_df["ph"].dropna().mean()
                with col5:
                    st.metric("평균 pH", f"{ph_mean:.2f}")

            st.markdown("---")

            env_plot_cols = num_cols(env_df, ["temperature", "humidity", "ph", "ec"])
            if "time" in env_df.columns and env_plot_cols:
                with st.spinner("환경 그래프를 그리는 중..."):
                    fig_env = make_subplots(
                        rows=len(env_plot_cols), cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.08,
                        subplot_titles=[
                            c + (" C" if c == "temperature" else " %" if c == "humidity" else " mS/cm" if c == "ec" else " pH")
                            for c in env_plot_cols
                        ],
                    )
                    colors = ["#2563EB", "#059669", "#D97706", "#7C3AED"]
                    for i, c in enumerate(env_plot_cols):
                        s = env_df[["time", c]].dropna().sort_values("time")
                        if s.empty:
                            continue
                        fig_env.add_trace(
                            go.Scatter(
                                x=s["time"], y=s[c],
                                mode="lines",
                                line=dict(color=colors[i % len(colors)], width=1.5),
                                name=c,
                                hovertemplate=c + ": %{{y:.2f}}<extra></extra>",
                            ),
                            row=i+1, col=1,
                        )
                    fig_env.update_layout(
                        height=280 + 120 * len(env_plot_cols),
                        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                        showlegend=False,
                        margin=dict(l=40, r=20, t=20, b=20),
                    )
                    st.plotly_chart(fig_env, width="stretch")
            elif not env_plot_cols:
                st.info("환경에 온도·습도·EC·pH 열이 없어요. 다른 형식의 CSV일 수 있어요.")

            st.markdown("---")
            st.subheader("환경 데이터 미리보기")
            preview_cols = ["time"] + num_cols(env_df, ["temperature", "humidity", "ph", "ec"])
            if preview_cols:
                st.dataframe(
                    env_df[preview_cols].dropna(subset=["time"]).sort_values("time").head(20),
                    width="stretch",
                    use_container_width=False,
                )
                csv_bytes = env_df[preview_cols].to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "환경 데이터 다운로드 (CSV)",
                    csv_bytes,
                    file_name=(env_name or "환경") + "_데이터.csv",
                    mime="text/csv",
                )
        else:
            st.info("환경 CSV를 업로드하면 평균 온도·습도·EC·pH 등을 볼 수 있어요.")

        if growth_df is not None and not growth_df.empty:
            st.markdown("---")
            st.subheader("생육 결과 데이터 요약")

            avail_growth = num_cols(growth_df, [
                "잎 수", "지상부 길이", "지하부 길이",
                "지상부 질량", "지하부 질량", "생중량",
            ])

            n_individuals = len(growth_df)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("개체 수", f"{n_individuals} 개")
            if "잎 수" in avail_growth:
                with c2:
                    st.metric("평균 잎 수", f"{growth_df['잎 수'].dropna().mean():.1f} 장")
            if "생중량" in avail_growth:
                with c3:
                    st.metric("평균 생중량", f"{growth_df['생중량'].dropna().mean():.2f} g")

            st.markdown("---")
            st.subheader("생육 결과 데이터 미리보기")
            show_cols = ["개체번호"] + avail_growth if "개체번호" in growth_df.columns else avail_growth
            if show_cols:
                st.dataframe(growth_df[show_cols], width="stretch", use_container_width=False)
                csv_bytes = growth_df[show_cols].to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "생육 데이터 다운로드 (CSV)",
                    csv_bytes,
                    file_name=(growth_name or "생육") + "_데이터.csv",
                    mime="text/csv",
                )

            if "생중량" in avail_growth:
                st.markdown("---")
                st.subheader("생중량 상위·하위 개체")
                ranked = growth_df[["개체번호", "생중량"]].dropna().sort_values("생중량", ascending=False)
                if len(ranked) >= 2:
                    top_n = min(5, len(ranked))
                    bottom_n = min(5, len(ranked))
                    top_rows = ranked.head(top_n)
                    bottom_rows = ranked.tail(bottom_n).iloc[::-1]

                    tl, tr = st.columns(2)
                    with tl:
                        st.write("생중량 상위 " + str(top_n) + "개체")
                        st.dataframe(top_rows, width="stretch", use_container_width=False)
                    with tr:
                        st.write("생중량 하위 " + str(bottom_n) + "개체")
                        st.dataframe(bottom_rows, width="stretch", use_container_width=False)

        elif growth_df is not None and growth_df.empty:
            st.info("생육 CSV에 데이터가 없어요.")

        st.markdown("---")
        st.subheader("우리의 가설")
        st.markdown("""
        1. **지상부 길이와 지하부 길이는 양의 상관관계가 있을 것이다.**  
           잎과 뿌리가 함께 자라는 경향이 있으므로 두 길이는 서로 비슷한 방향으로 변할 것으로 예상해요.  
           *상관계수(r)*가 +1에 가까울수록 강한 양의 상관, 0에 가까우면 상관이 약해요.

        2. **잎의 개수와 생중량의 관계가 식물 생장을 가장 잘 나타낼 것이다.**  
           잎이 많을수록 광합성이 활발하고 전체 무게(생중량)도 증가할 것으로 예상해요.

        3. **지상부 길이와 생중량, 지하부 길이와 생중량은 약한 상관관계가 있을 것이다.**  
           길이가 길다고 반드시 무거운 것은 아니므로(상당한 빈 공간 포함 가능), 상관은 상대적으로 약할 수 있어요.
        """)
    except Exception as e:
        st.warning("경고: 이 부분은 데이터 형식 때문에 표시하지 못했어요: " + str(e))

# ═════════════════════════════════════════════════════════════════════════════
#  탭 2 - 생육 그래프와 상관계수
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    try:
        st.header("생육 그래프와 상관계수")

        if growth_df is None or growth_df.empty:
            st.info("생육 결과 CSV를 업로드하면 산점도와 상관계수 행렬을 볼 수 있어요.")
        else:
            avail = num_cols(growth_df, [
                "잎 수", "지상부 길이", "지하부 길이",
                "지상부 질량", "지하부 질량", "생중량",
            ])

            if len(avail) < 2:
                st.info("분석할 숫자 열이 충분하지 않아요. 생육 CSV 열 이름을 확인해주세요.")
            else:
                st.subheader("생중량 vs 잎의 개수")
                if "생중량" in avail and "잎 수" in avail:
                    fig1 = scatter_with_trend(
                        growth_df, "잎 수", "생중량",
                        "잎의 개수 vs 생중량",
                        "잎의 개수 (장)", "생중량 (g)",
                    )
                    if fig1:
                        st.plotly_chart(fig1, width="stretch")
                    else:
                        st.info("데이터가 부족해서 그래프를 그리지 못했어요.")
                else:
                    missing = []
                    if "생중량" not in avail:
                        missing.append("생중량")
                    if "잎 수" not in avail:
                        missing.append("잎 수")
                    st.info("? " + ", ".join(missing) + " 열이 없어서 이 그래프를 건너뛰었어요.")

                st.subheader("지상부 길이 vs 생중량")
                if "지상부 길이" in avail and "생중량" in avail:
                    fig2 = scatter_with_trend(
                        growth_df, "지상부 길이", "생중량",
                        "지상부 길이 vs 생중량",
                        "지상부 길이 (mm)", "생중량 (g)",
                    )
                    if fig2:
                        st.plotly_chart(fig2, width="stretch")
                    else:
                        st.info("데이터가 부족해서 그래프를 그리지 못했어요.")
                else:
                    missing = []
                    if "지상부 길이" not in avail:
                        missing.append("지상부 길이")
                    if "생중량" not in avail:
                        missing.append("생중량")
                    st.info("? " + ", ".join(missing) + " 열이 없어서 이 그래프를 건너뛰었어요.")

                st.subheader("지하부 길이 vs 생중량")
                if "지하부 길이" in avail and "생중량" in avail:
                    fig3 = scatter_with_trend(
                        growth_df, "지하부 길이", "생중량",
                        "지하부 길이 vs 생중량",
                        "지하부 길이 (mm)", "생중량 (g)",
                    )
                    if fig3:
                        st.plotly_chart(fig3, width="stretch")
                    else:
                        st.info("데이터가 부족해서 그래프를 그리지 못했어요.")
                else:
                    missing = []
                    if "지하부 길이" not in avail:
                        missing.append("지하부 길이")
                    if "생중량" not in avail:
                        missing.append("생중량")
                    st.info("? " + ", ".join(missing) + " 열이 없어서 이 그래프를 건너뛰었어요.")

                st.markdown("---")
                st.subheader("상관계수 행렬 (Pearson r)")
                st.markdown("""
                **상관계수(r)** 는 두 변수가 함께 변하는 정도를 -1 ~ +1 사이로 나타낸 값이에요.  
                +1에 가까우면 함께 증가(양의 상관), -1에 가까우면 하나가 증가할 때 다른 하나가 감소(음의 상관),  
                0에 가까우면 상관이 거의 없어요.
                """)

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
                        )
                        fig_corr.update_layout(
                            title="개체별 생육 지표 간 상관계수 행렬",
                            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                            margin=dict(l=40, r=20, t=50, b=40),
                        )
                        st.plotly_chart(fig_corr, width="stretch")
                        st.dataframe(corr_matrix, width="stretch", use_container_width=False)
                    else:
                        st.info("상관계수 계산용 데이터가 부족해요.")
                else:
                    st.info("상관계수 행렬을 만들려면 최소 2개의 숫자 열이 필요해요.")

                st.markdown("---")
                st.info(
                    "개체번호는 분석에서 제외했어요. 학교마다 A1/A2 형태나 1/2 형태 등 달라서\n"
                    "비교 기준에 쓰면 오류가 생기기 때문이에요. 개체 간 비교는 순수하게 생육 수치만으로 해요."
                )
    except Exception as e:
        st.warning("경고: 이 부분은 데이터 형식 때문에 표시하지 못했어요: " + str(e))

# ═════════════════════════════════════════════════════════════════════════════
#  탭 3 - 결론
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    try:
        st.header("결론")

        if growth_df is None or growth_df.empty:
            st.info("생육 결과 CSV를 업로드하면 결론을 자동으로 계산해요.")
        else:
            avail = num_cols(growth_df, [
                "잎 수", "지상부 길이", "지하부 길이",
                "지상부 질량", "지하부 질량", "생중량",
            ])

            if "생중량" in avail and "잎 수" in avail and len(growth_df) >= 2:
                d = growth_df[["잎 수", "생중량"]].dropna()
                r_leaves = d["잎 수"].corr(d["생중량"])

                results = {}
                pairs = [
                    ("잎 수", "생중량"),
                    ("지상부 길이", "생중량"),
                    ("지하부 길이", "생중량"),
                    ("지상부 길이", "지하부 길이"),
                ]
                for x, y in pairs:
                    if x in avail and y in avail:
                        dd = growth_df[[x, y]].dropna()
                        if len(dd) >= 2:
                            results[x + " <-> " + y] = dd[x].corr(dd[y])

                if results:
                    sorted_res = sorted(results.items(), key=lambda kv: abs(kv[1]), reverse=True)
                    top_pair, top_r = sorted_res[0]

                    st.subheader("상관계수 비교 결과")

                    n_cols = min(4, len(results))
                    res_cols = st.columns(n_cols)
                    for i, (label, r_val) in enumerate(sorted_res):
                        with res_cols[i]:
                            direction = "양의 상관" if r_val > 0 else "음의 상관"
                            strength = (
                                "매우 강함" if abs(r_val) > 0.8 else
                                "강함" if abs(r_val) > 0.6 else
                                "중간" if abs(r_val) > 0.4 else
                                "약함" if abs(r_val) > 0.2 else "매우 약함"
                            )
                            st.metric(label, "r = " + f"{r_val:.3f}", delta=strength + " · " + direction)

                    st.markdown("---")
                    st.subheader("가장 강한 상관관계")
                    st.markdown(
                        "위 결과에서 **가장 강한 상관관계**는\n\n"
                        "### **" + top_pair + "  (r = " + f"{top_r:.3f}" + ")**\n\n"
                        "이에요."
                    )

                    if "잎 수" in avail and "생중량" in avail:
                        d2 = growth_df[["잎 수", "생중량"]].dropna()
                        r_lw = d2["잎 수"].corr(d2["생중량"])
                        if abs(r_lw) >= abs(top_r) or top_pair == "잎 수 <-> 생중량":
                            st.markdown(
                                "**생중량과 잎의 개수 사이의 상관계수가 r = " + f"{r_lw:.3f}" +
                                "**로, 측정한 지표 중 가장 강한 상관을 보였어요.\n\n"
                                "즉, **잎이 많을수록 식물 전체 무게(생중량)도 함께 증가하는 경향**이 뚜렷해요."
                            )
                        else:
                            st.markdown(
                                "생중량과 잎의 개수 사이 상관계수는 r = " + f"{r_lw:.3f}" +
                                "이에요.\n"
                                "가장 강한 상관은 **" + top_pair + " (r = " + f"{top_r:.3f}" + ")였어요."
                            )
                else:
                    st.info("상관계수를 계산할 수 있는 지표 쌍이 부족해요.")

                st.markdown("---")
                st.subheader("가설 검토")

                if "지상부 길이" in avail and "지하부 길이" in avail:
                    d3 = growth_df[["지상부 길이", "지하부 길이"]].dropna()
                    if len(d3) >= 2:
                        r1 = d3["지상부 길이"].corr(d3["지하부 길이"])
                        if r1 > 0.3:
                            st.success(
                                "가설 1 (지상부 길이와 지하부 길이의 양의 상관): 지지됨 (r = " + f"{r1:.3f}" + ")"
                            )
                        else:
                            st.info(
                                "가설 1: r = " + f"{r1:.3f}" +
                                "로 예상보다 약한 상관이에요. 개체별로 뿌리·줄기 발달 패턴이 다를 수 있어요."
                            )

                if "잎 수" in avail and "생중량" in avail:
                    d4 = growth_df[["잎 수", "생중량"]].dropna()
                    if len(d4) >= 2:
                        r2 = d4["잎 수"].corr(d4["생중량"])
                        if abs(r2) >= 0.5:
                            st.success(
                                "가설 2 (잎의 개수-생중량 관계가 가장 잘 나타냄): 지지됨 (r = " + f"{r2:.3f}" + ")"
                            )
                        else:
                            st.info(
                                "가설 2: r = " + f"{r2:.3f}" +
                                "로 중간 정도 상관이 있어요. 다른 지표 조합도 함께 살펴보면 좋아요."
                            )

                weak_found = False
                for x_col in ["지상부 길이", "지하부 길이"]:
                    if x_col in avail and "생중량" in avail:
                        d5 = growth_df[[x_col, "생중량"]].dropna()
                        if len(d5) >= 2:
                            r3 = d5[x_col].corr(d5["생중량"])
                            if abs(r3) < 0.5:
                                weak_found = True
                                st.info(
                                    "가설 3 (" + x_col + " <-> 생중량의 약한 상관): "
                                    "r = " + f"{r3:.3f}" + "로 약한 상관이 확인됐어요."
                                )
                if not weak_found:
                    st.info("가설 3 검증용 데이터가 충분하지 않아요.")

                st.markdown("---")
                st.info(
                    "개체번호는 학교마다 형식이 달라 분석에서 제외했어요. (A1·A2 형태 또는 1·2 형태 등)\n"
                    "개체 간 비교는 생육 수치만으로 이루어졌어요.",
                )
            else:
                st.info(
                    "생중량과 잎의 개수 데이터가 필요해요. 생육 CSV에 해당 열이 있는지 확인해주세요.\n"
                    "(생중량 열이 없으면 지상부질량 + 지하부질량으로 자동 계산돼요.)"
                )
    except Exception as e:
        st.warning("경고: 이 부분은 데이터 형식 때문에 표시하지 못했어요: " + str(e))
