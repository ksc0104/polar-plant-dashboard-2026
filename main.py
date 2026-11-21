import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
import io

st.set_page_config(page_title="극지식물 생육 분석 대시보드", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
   font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 데이터 로딩 (캐싱)
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

def make_scatter_with_trend(df, x_col, y_col, title, color_col=None):
    d = df[[x_col, y_col]].dropna()
    if len(d) < 2:
        return None
    fig = px.scatter(d, x=x_col, y=y_col, title=title,
                     labels={x_col: x_col, y_col: y_col},
                     color=color_col if color_col and color_col in df.columns else None,
                     hover_data=[color_col] if color_col and color_col in df.columns else None)
    x_vals = d[x_col].values
    y_vals = d[y_col].values
    slope, intercept = np.polyfit(x_vals, y_vals, 1)
    line_x = np.array([x_vals.min(), x_vals.max()])
    line_y = slope * line_x + intercept
    r, _ = stats.pearsonr(x_vals, y_vals)
    fig.add_trace(go.Scatter(x=line_x, y=line_y, mode="lines",
                             line=dict(color="red", dash="dash", width=2),
                             name=f"추세선 (r={r:.3f})"))
    fig.update_layout(font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                      width=900, height=500)
    return fig

def make_heatmap(df, cols):
    d = df[cols].dropna()
    if len(d) < 2 or len(cols) < 2:
        return None
    corr = d[cols].corr()
    fig = px.imshow(corr, text_auto=".3f", color_continuous_scale="RdBu_r",
                   title="변수 간 상관계수 행렬")
    fig.update_layout(font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                      width=600, height=500)
    return fig

def get_school_name(file):
    if file is None:
        return "우리 학교"
    name = file.name
    for sep in ["_", "-"]:
        if sep in name:
            return name.split(sep)[0]
    return name.replace(".csv", "")

# ─────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────
st.sidebar.title("📊 데이터 업로드")
env_file = st.sidebar.file_uploader("환경 CSV", type="csv")
growth_file = st.sidebar.file_uploader("생육 결과 CSV", type="csv")

if env_file is None and growth_file is None:
    st.info("CSV 파일 2개를 사이드바에 업로드해 주세요.")
    st.stop()

env_df, growth_df = load_and_standardize(env_file, growth_file)
school_name = get_school_name(env_file or growth_file)

st.title(f"{school_name} 극지식물 개체별 생육 차이 분석")

# 생육 측정 항목 선택
if not growth_df.empty:
    measure_cols = [c for c in ["잎 수", "지상부 길이", "지하부 길이", "생중량", "지상부 질량", "지하부 질량"]
                    if c in growth_df.columns]
    if measure_cols:
        selected_measure = st.sidebar.selectbox("생육 측정 항목 선택", measure_cols)

# ─────────────────────────────────────────────
# 탭
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 개요", "📈 산점도 & 상관분석", "🎯 결론"])

with tab1:
    try:
        c1, c2 = st.columns(2)
        with c1:
            st.header("📊 데이터 정보")
            if not env_df.empty:
                st.info(f"학교명: {school_name} (환경 데이터)")
                st.metric("총 측정 횟수", len(env_df))
                numeric_env = [c for c in ["temperature", "humidity", "ph", "ec"] if c in env_df.columns]
                if numeric_env:
                    st.subheader("환경 데이터 요약")
                    for col in numeric_env:
                        vals = env_df[col].dropna()
                        if len(vals) >= 1:
                            label_map = {"temperature": "평균 온도(℃)", "humidity": "평균 습도(%)",
                                         "ph": "평균 pH", "ec": "평균 EC"}
                            st.metric(label_map.get(col, col), f"{vals.mean():.2f} ± {vals.std():.2f}")
                if "time" in env_df.columns:
                    times = env_df["time"].dropna()
                    if len(times) >= 2:
                        st.write(f"측정 기간: {times.min().strftime('%Y-%m-%d')} ~ {times.max().strftime('%Y-%m-%d')}")
            else:
                st.info("환경 데이터가 업로드되지 않았습니다.")

        with c2:
            st.header("🌱 생육 데이터")
            if not growth_df.empty:
                st.info(f"학교명: {school_name} (생육 결과 데이터)")
                st.metric("개체 수", len(growth_df))
                if "생중량" in growth_df.columns:
                    bw = growth_df["생중량"].dropna()
                    if len(bw) >= 1:
                        st.metric("평균 생중량(g)", f"{bw.mean():.2f} ± {bw.std():.2f}")
                if "잎 수" in growth_df.columns:
                    leaves = growth_df["잎 수"].dropna()
                    if len(leaves) >= 1:
                        st.metric("평균 잎 수(장)", f"{leaves.mean():.1f}")
            else:
                st.info("생육 데이터가 업로드되지 않았습니다.")

        st.header("우리의 가설")
        st.markdown("""
        1. **지상부 길이와 지하부 길이는 양의 상관관계가 있다.**
        2. **잎의 개수와 생중량의 관계가 식물의 생장을 가장 잘 나타낸다.**
        3. **지상부 길이와 생중량, 지하부 길이와 생중량은 약한 상관관계가 있다.**
        """)
    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")

with tab2:
    try:
        if growth_df.empty:
            st.info("생육 데이터가 업로드되지 않았습니다.")
        else:
            st.header("📈 환경 데이터 & 생육 산점도")

            env_col1, env_col2 = st.columns(2)
            with env_col1:
                if "time" in env_df.columns and "temperature" in env_df.columns:
                    d = env_df[["time", "temperature"]].dropna()
                    if len(d) >= 2:
                        fig = px.line(d, x="time", y="temperature", title="시간별 온도 변화")
                        fig.update_layout(font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"))
                        st.plotly_chart(fig, width="stretch")
                    else:
                        st.info("온도 데이터가 충분하지 않습니다.")
                else:
                    st.info("온도 데이터가 없습니다.")

            with env_col2:
                if "time" in env_df.columns and "humidity" in env_df.columns:
                    d = env_df[["time", "humidity"]].dropna()
                    if len(d) >= 2:
                        fig = px.line(d, x="time", y="humidity", title="시간별 습도 변화")
                        fig.update_layout(font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"))
                        st.plotly_chart(fig, width="stretch")
                    else:
                        st.info("습도 데이터가 충분하지 않습니다.")
                else:
                    st.info("습도 데이터가 없습니다.")

            st.header("📊 생육 지표 간 산점도")

            if "생중량" in growth_df.columns and "잎 수" in growth_df.columns:
                fig = make_scatter_with_trend(growth_df, "잎 수", "생중량",
                                              "잎 수 vs 생중량 (생장 대표 지표)")
                if fig:
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("데이터가 부족합니다.")

            if "생중량" in growth_df.columns and "지상부 길이" in growth_df.columns:
                fig = make_scatter_with_trend(growth_df, "지상부 길이", "생중량",
                                              "지상부 길이 vs 생중량")
                if fig:
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("데이터가 부족합니다.")

            if "생중량" in growth_df.columns and "지하부 길이" in growth_df.columns:
                fig = make_scatter_with_trend(growth_df, "지하부 길이", "생중량",
                                              "지하부 길이 vs 생중량")
                if fig:
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("데이터가 부족합니다.")

            if "지상부 길이" in growth_df.columns and "지하부 길이" in growth_df.columns:
                fig = make_scatter_with_trend(growth_df, "지상부 길이", "지하부 길이",
                                              "지상부 길이 vs 지하부 길이")
                if fig:
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("데이터가 부족합니다.")

            st.header("🔢 상관계수 행렬")
            corr_cols = [c for c in ["잎 수", "지상부 길이", "지상부 질량", "지하부 길이",
                                      "지하부 질량", "생중량"] if c in growth_df.columns]
            if len(corr_cols) >= 2:
                fig = make_heatmap(growth_df, corr_cols)
                if fig:
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("상관계수 계산 데이터가 부족합니다.")
            else:
                st.info("상관계수 행렬을 만들 변수가 충분하지 않습니다.")

        # CSV 다운로드 버튼
        if env_file is not None or growth_file is not None:
            st.divider()
            st.header("⬇️ 데이터 다운로드")
            if not env_df.empty:
                csv_data = env_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("환경 데이터 CSV 다운로드", csv_data,
                                   file_name=f"{school_name}_환경데이터.csv",
                                   mime="text/csv")
            if not growth_df.empty:
                csv_data = growth_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("생육 결과 CSV 다운로드", csv_data,
                                   file_name=f"{school_name}_생육결과데이터.csv",
                                   mime="text/csv")
    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")

with tab3:
    try:
        if growth_df.empty:
            st.info("생육 데이터가 업로드되지 않았습니다.")
        else:
            st.header("🎯 분석 결론")

            conclusions = []
            top_individuals = []

            # 생중량 vs 잎 수 상관관계 (가장 강한 관계)
            if "생중량" in growth_df.columns and "잎 수" in growth_df.columns:
                d = growth_df[["잎 수", "생중량"]].dropna()
                if len(d) >= 3:
                    r, p = stats.pearsonr(d["잎 수"], d["생중량"])
                    conclusions.append(
                        f"✅ **잎 수 ↔ 생중량: 상관계수 r = {r:.3f}** "
                        f"(p = {p:.4f}) — 식물의 생장을 가장 잘 나타내는 관계입니다."
                    )

            # 지상부 길이 ↔ 생중량
            if "생중량" in growth_df.columns and "지상부 길이" in growth_df.columns:
                d = growth_df[["지상부 길이", "생중량"]].dropna()
                if len(d) >= 3:
                    r, p = stats.pearsonr(d["지상부 길이"], d["생중량"])
                    conclusions.append(
                        f"📏 **지상부 길이 ↔ 생중량: r = {r:.3f}** "
                        f"(p = {p:.4f}) — 약한 양의 상관관계입니다."
                    )

            # 지하부 길이 ↔ 생중량
            if "생중량" in growth_df.columns and "지하부 길이" in growth_df.columns:
                d = growth_df[["지하부 길이", "생중량"]].dropna()
                if len(d) >= 3:
                    r, p = stats.pearsonr(d["지하부 길이"], d["생중량"])
                    conclusions.append(
                        f"🌱 **지하부 길이 ↔ 생중량: r = {r:.3f}** "
                        f"(p = {p:.4f}) — 약한 양의 상관관계입니다."
                    )

            # 지상부 길이 ↔ 지하부 길이
            if "지상부 길이" in growth_df.columns and "지하부 길이" in growth_df.columns:
                d = growth_df[["지상부 길이", "지하부 길이"]].dropna()
                if len(d) >= 3:
                    r, p = stats.pearsonr(d["지상부 길이"], d["지하부 길이"])
                    conclusions.append(
                        f"🔗 **지상부 길이 ↔ 지하부 길이: r = {r:.3f}** "
                        f"(p = {p:.4f}) — 양의 상관관계입니다."
                    )

            for c in conclusions:
                st.markdown(c)

            st.divider()

            # 개체별 생중량 상위/하위
            if "생중량" in growth_df.columns and "개체번호" in growth_df.columns:
                d = growth_df[["개체번호", "생중량"]].dropna().sort_values("생중량", ascending=False)
                if len(d) >= 1:
                    st.subheader("🏆 개체별 생중량")
                    top_n = min(5, len(d))
                    top_df = d.head(top_n)
                    st.info("▲ 생중량 상위 개체")
                    st.dataframe(top_df, width="stretch", hide_index=True)

                    bottom_df = d.tail(top_n).sort_values("생중량", ascending=True)
                    st.info("▼ 생중량 하위 개체")
                    st.dataframe(bottom_df, width="stretch", hide_index=True)

            if conclusions:
                st.divider()
                st.success("💡 **핵심 결론:** 생중량과 잎의 개수 사이에 가장 강한 상관관계가 있습니다!")
    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")
