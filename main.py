
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# ── 한글 폰트 (Streamlit CSS) ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
   font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

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
                df[c].astype(str).str.replace(",", "")
                .str.extract(r"(-?\d+\.?\d*)")[0],
                errors="coerce"
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
                pd.to_datetime(parts[0], format="%Y%m%d")
                + pd.to_timedelta(parts[1].astype(int), unit="h")
            )
        df["time"] = parsed
    return df

# ── CSV 읽기 (인코딩 이중 시도) ─────────────────────────────────────────────
def read_csv(file):
    data = file.getvalue()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(io.BytesIO(data), encoding=enc)
        except Exception:
            pass
    return pd.DataFrame()

# ── CSV 다운로드 헬퍼 (utf-8-sig) ──────────────────────────────────────────
def csv_download(df, label):
    return st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{label}.csv",
        mime="text/csv",
    )

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  사이드바                                                              ║
# ╚══════════════════════════════════════════════════════════════════════════╝
st.sidebar.title("📁 데이터 업로드")
env_file = st.sidebar.file_uploader("환경 CSV", type="csv")
growth_file = st.sidebar.file_uploader("생육 결과 CSV", type="csv")

st.sidebar.markdown("---")
st.sidebar.title("📏 측정 항목 선택")
growth_metrics = st.sidebar.multiselect(
    "비교할 생육 지표",
    ["잎 수", "지상부 길이", "지하부 길이", "생중량"],
    default=["잎 수", "지상부 길이", "지하부 길이", "생중량"],
)

# ── 데이터 한 번만 로딩 ─────────────────────────────────────────────────────
@st.cache_data
def load_data(env_file, growth_file):
    env_df = pd.DataFrame()
    growth_df = pd.DataFrame()
    if env_file is not None:
        env_df = read_csv(env_file)
        env_df = std_cols(env_df)
    if growth_file is not None:
        growth_df = read_csv(growth_file)
        growth_df = std_cols(growth_df)
    return env_df, growth_df

with st.spinner("데이터를 불러오는 중..."):
    env_df, growth_df = load_data(env_file, growth_file)

# ── 학교명 추출 (파일명에서) ────────────────────────────────────────────────
school_name = "우리 학교"
if env_file is not None:
    nm = env_file.name.replace(".csv", "").replace("_환경데이터", "").replace("_환경", "")
    if nm:
        school_name = nm
elif growth_file is not None:
    nm = growth_file.name.replace(".csv", "").replace("_생육결과데이터", "").replace("_생육결과", "").replace("_생육", "")
    if nm:
        school_name = nm

st.markdown(f"# 🌱 {school_name} 극지식물 개체별 생육 차이 분석")
st.markdown("왼쪽 사이드바에서 CSV를 업로드하고 분석할 생육 지표를 선택해 주세요.")
st.markdown("---")

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  탭 1 — 실험 개요                                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝
tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

with tab1:
    try:
        st.header("📖 실험 개요")

        col_bg, col_purpose = st.columns(2)
        with col_bg:
            st.subheader("연구 배경")
            st.write(
                "극지성 식물은 추운 환경에서도 살아남는 강한 식물이에요. "
                "우리 학교에서는 이런 식물을 직접 재배하면서 개체마다 얼마나 다르게 자라는지 관찰했어요."
            )
        with col_purpose:
            st.subheader("연구 목적")
            st.write(
                "개체별로 잎 수, 줄기 길이, 무게가 어떻게 다른지 비교하고, "
                "환경 조건(온도·습도 등)과 생육의 관계를 살펴보아요."
            )

        st.markdown("---")
        st.subheader("데이터 요약")

        rows = []

        # 총 개체 수
        if not growth_df.empty and "개체번호" in growth_df.columns:
            rows.append(["총 개체 수", f"{growth_df['개체번호'].nunique()}개체"])
        else:
            rows.append(["총 개체 수", "데이터 없음"])

        # 측정 기간
        if not env_df.empty and "time" in env_df.columns:
            t_min = env_df["time"].min()
            t_max = env_df["time"].max()
            if pd.notna(t_min) and pd.notna(t_max):
                rows.append([
                    "측정 기간",
                    f"{t_min.strftime('%Y-%m-%d')} ~ {t_max.strftime('%Y-%m-%d')}",
                ])
            else:
                rows.append(["측정 기간", "확인 불가"])
        else:
            rows.append(["측정 기간", "데이터 없음"])

        # 환경 측정 항목
        env_cols_list = [c for c in ["temperature", "humidity", "ph", "ec"] if c in env_df.columns]
        if env_cols_list:
            names_map = {"temperature": "온도", "humidity": "습도", "ph": "pH", "ec": "EC"}
            rows.append(["환경 측정 항목", ", ".join(names_map[c] for c in env_cols_list)])
        else:
            rows.append(["환경 측정 항목", "데이터 없음"])

        # 생육 측정 항목
        growth_cols_list = [c for c in ["잎 수", "지상부 길이", "지하부 길이", "생중량"] if c in growth_df.columns]
        if growth_cols_list:
            rows.append(["생육 측정 항목", ", ".join(growth_cols_list)])
        else:
            rows.append(["생육 측정 항목", "데이터 없음"])

        st.dataframe(pd.DataFrame(rows, columns=["항목", "내용"]), width="stretch", hide_index=True)

        st.markdown("---")
        st.subheader("주요 지표")

        m1, m2, m3, m4 = st.columns(4)

        with m1:
            if not growth_df.empty and "개체번호" in growth_df.columns:
                st.metric("총 개체수", f"{growth_df['개체번호'].nunique()}개체")
            else:
                st.metric("총 개체수", "데이터 없음")

        with m2:
            if not env_df.empty and "temperature" in env_df.columns:
                tv = env_df["temperature"].dropna()
                if len(tv) > 0:
                    st.metric("평균 온도", f"{tv.mean():.1f}℃")
                else:
                    st.metric("평균 온도", "데이터 없음")
            else:
                st.metric("평균 온도", "데이터 없음")

        with m3:
            if not env_df.empty and "humidity" in env_df.columns:
                hv = env_df["humidity"].dropna()
                if len(hv) > 0:
                    st.metric("평균 습도", f"{hv.mean():.1f}%")
                else:
                    st.metric("평균 습도", "데이터 없음")
            else:
                st.metric("평균 습도", "데이터 없음")

        with m4:
            if not growth_df.empty and "생중량" in growth_df.columns:
                gv = growth_df["생중량"].dropna()
                if len(gv) > 0:
                    st.metric("평균 생중량", f"{gv.mean():.2f}g")
                else:
                    st.metric("평균 생중량", "데이터 없음")
            else:
                st.metric("평균 생중량", "데이터 없음")

    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  탭 2 — 환경 데이터                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝
with tab2:
    try:
        st.header("🌡️ 환경 데이터")

        if env_df.empty:
            st.info("📁 사이드바에서 환경 CSV를 업로드해 주세요.")
        else:
            # ── 환경 요약 표 ──────────────────────────────────────────────
            st.subheader("환경 요약")
            env_summary_cols = [
                c for c in ["temperature", "humidity", "ph", "ec"] if c in env_df.columns
            ]
            if env_summary_cols:
                summary_data = []
                label_map = {"temperature": "온도(℃)", "humidity": "습도(%)", "ph": "pH", "ec": "EC"}
                for col in env_summary_cols:
                    vals = env_df[col].dropna()
                    if len(vals) > 0:
                        summary_data.append(
                            [label_map[col], f"{vals.mean():.2f}", f"{vals.min():.2f}", f"{vals.max():.2f}"]
                        )
                if summary_data:
                    st.dataframe(
                        pd.DataFrame(summary_data, columns=["항목", "평균", "최소", "최대"]),
                        width="stretch",
                        hide_index=True,
                    )
                else:
                    st.info("환경 데이터가 충분하지 않아요.")
            else:
                st.info("환경 데이터에 인식할 수 있는 열이 없어요.")

            st.markdown("---")
            st.subheader("날짜별 시계열")

            if "time" in env_df.columns:
                env_daily = env_df.copy()
                env_daily["date"] = env_daily["time"].dt.date

                # 온도 시계열
                if "temperature" in env_df.columns:
                    daily_temp = env_daily.groupby("date")["temperature"].mean().reset_index()
                    if len(daily_temp) > 0:
                        fig_t = px.line(daily_temp, x="date", y="temperature", markers=True)
                        fig_t.update_layout(
                            title="일별 평균 온도 변화",
                            xaxis_title="날짜",
                            yaxis_title="온도 (℃)",
                            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                        )
                        st.plotly_chart(fig_t, width="stretch")

                # 습도 시계열
                if "humidity" in env_df.columns:
                    daily_hum = env_daily.groupby("date")["humidity"].mean().reset_index()
                    if len(daily_hum) > 0:
                        fig_h = px.line(daily_hum, x="date", y="humidity", markers=True)
                        fig_h.update_layout(
                            title="일별 평균 습도 변화",
                            xaxis_title="날짜",
                            yaxis_title="습도 (%)",
                            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                        )
                        st.plotly_chart(fig_h, width="stretch")

                # pH·EC 변화 (열이 있을 때만)
                ph_ec_cols = [c for c in ["ph", "ec"] if c in env_df.columns]
                if ph_ec_cols:
                    daily_pe = env_daily.groupby("date")[ph_ec_cols].mean().reset_index()
                    if len(daily_pe) > 0:
                        fig_pe = make_subplots(specs=[[{"secondary_y": False}]])
                        pe_labels = {"ph": "pH", "ec": "EC"}
                        for col in ph_ec_cols:
                            fig_pe.add_trace(
                                go.Scatter(
                                    x=daily_pe["date"],
                                    y=daily_pe[col],
                                    mode="lines+markers",
                                    name=pe_labels[col],
                                ),
                                row=1,
                                col=1,
                            )
                        fig_pe.update_layout(
                            title="일별 pH·EC 변화",
                            xaxis_title="날짜",
                            yaxis_title="값",
                            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                        )
                        st.plotly_chart(fig_pe, width="stretch")
                else:
                    st.info("🔍 이 학교에는 pH·EC 데이터가 없어요.")
            else:
                st.info("시간 데이터가 없어서 시계열 그래프를 그릴 수 없어요.")

            with st.expander("📋 환경 데이터 원본 테이블"):
                st.dataframe(env_df, width="stretch")
                csv_download(env_df, "환경 데이터 다운로드")

    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  탭 3 — 생육 결과                                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝
with tab3:
    try:
        st.header("📊 생육 결과")

        if growth_df.empty:
            st.info("📁 사이드바에서 생육 결과 CSV를 업로드해 주세요.")
        else:
            # ── 핵심 결과 카드 ────────────────────────────────────────────
            st.subheader("🥇 핵심 결과")

            if "생중량" in growth_df.columns:
                gv = growth_df["생중량"].dropna()
                if len(gv) > 0:
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("평균 생중량", f"{gv.mean():.2f}g")
                    with c2:
                        idx_max = growth_df["생중량"].idxmax()
                        lbl_max = growth_df.loc[idx_max, "개체번호"]
                        st.metric("최대 생중량 개체", f"{lbl_max} ({gv.max():.2f}g)")
                    with c3:
                        idx_min = growth_df["생중량"].idxmin()
                        lbl_min = growth_df.loc[idx_min, "개체번호"]
                        st.metric("최소 생중량 개체", f"{lbl_min} ({gv.min():.2f}g)")
                else:
                    st.info("생중량 데이터가 충분하지 않아요.")
            else:
                st.info("생중량 데이터가 없어요.")

            st.markdown("---")
            st.subheader("개체별 생육 비교")

            available_metrics = [c for c in growth_metrics if c in growth_df.columns]

            if available_metrics:
                for metric in available_metrics:
                    vals = growth_df[metric].dropna()
                    if len(vals) >= 2:
                        d = growth_df.dropna(subset=[metric])
                        fig_bar = px.bar(
                            d,
                            x="개체번호",
                            y=metric,
                            labels={"개체번호": "개체", metric: metric},
                            title=f"개체별 {metric}",
                        )
                        fig_bar.update_layout(
                            xaxis_title="개체",
                            yaxis_title=metric,
                            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                        )
                        st.plotly_chart(fig_bar, width="stretch")
                    else:
                        st.info(f"{metric} 데이터가 충분하지 않아요.")
            else:
                st.info("선택한 생육 지표가 데이터에 없어요.")

            st.markdown("---")
            st.subheader("생중량 분포")

            if "생중량" in growth_df.columns:
                gv = growth_df["생중량"].dropna()
                if len(gv) >= 2:
                    fig_box = px.box(
                        growth_df.dropna(subset=["생중량"]),
                        y="생중량",
                        labels={"생중량": "생중량(g)"},
                    )
                    fig_box.update_layout(
                        title="생중량 분포 (박스플롯)",
                        yaxis_title="생중량 (g)",
                        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                    )
                    st.plotly_chart(fig_box, width="stretch")
                else:
                    st.info("생중량 데이터가 충분하지 않아요.")
            else:
                st.info("생중량 데이터가 없어요.")

            st.markdown("---")
            st.subheader("상관관계 분석")

            # ── 잎 수 vs 생중량 ───────────────────────────────────────────
            if "잎 수" in growth_df.columns and "생중량" in growth_df.columns:
                d1 = growth_df[["잎 수", "생중량"]].dropna()
                if len(d1) >= 2:
                    r1 = d1["잎 수"].corr(d1["생중량"])
                    slope1, intercept1 = np.polyfit(d1["잎 수"], d1["생중량"], 1)
                    x_fit1 = np.linspace(d1["잎 수"].min(), d1["잎 수"].max(), 100)
                    y_fit1 = slope1 * x_fit1 + intercept1
                    fig_s1 = px.scatter(
                        d1,
                        x="잎 수",
                        y="생중량",
                        labels={"잎 수": "잎 수", "생중량": "생중량(g)"},
                    )
                    fig_s1.add_trace(
                        go.Scatter(
                            x=x_fit1,
                            y=y_fit1,
                            mode="lines",
                            name=f"추세선 (r={r1:.2f})",
                            line=dict(color="red"),
                        )
                    )
                    fig_s1.update_layout(
                        title=f"잎 수 vs 생중량 (상관계수 r = {r1:.2f})",
                        xaxis_title="잎 수",
                        yaxis_title="생중량 (g)",
                        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                    )
                    st.plotly_chart(fig_s1, width="stretch")
                    st.write(f"**상관계수(r)**: {r1:.2f}")
                    st.write(
                        "→ r이 1에 가까울수록 잎 수가 많을수록 생중량이 증가하는 경향이 있어요. "
                        "0에 가까우면 관계가 거의 없어요."
                    )
                else:
                    st.info("잎 수와 생중량 데이터가 충분하지 않아요.")
            else:
                st.info("잎 수와 생중량 데이터가 둘 다 필요해요.")

            st.markdown("---")

            # ── 지상부 길이 vs 생중량 ─────────────────────────────────────
            if "지상부 길이" in growth_df.columns and "생중량" in growth_df.columns:
                d2 = growth_df[["지상부 길이", "생중량"]].dropna()
                if len(d2) >= 2:
                    r2 = d2["지상부 길이"].corr(d2["생중량"])
                    slope2, intercept2 = np.polyfit(d2["지상부 길이"], d2["생중량"], 1)
                    x_fit2 = np.linspace(d2["지상부 길이"].min(), d2["지상부 길이"].max(), 100)
                    y_fit2 = slope2 * x_fit2 + intercept2
                    fig_s2 = px.scatter(
                        d2,
                        x="지상부 길이",
                        y="생중량",
                        labels={"지상부 길이": "지상부 길이(mm)", "생중량": "생중량(g)"},
                    )
                    fig_s2.add_trace(
                        go.Scatter(
                            x=x_fit2,
                            y=y_fit2,
                            mode="lines",
                            name=f"추세선 (r={r2:.2f})",
                            line=dict(color="red"),
                        )
                    )
                    fig_s2.update_layout(
                        title=f"지상부 길이 vs 생중량 (상관계수 r = {r2:.2f})",
                        xaxis_title="지상부 길이 (mm)",
                        yaxis_title="생중량 (g)",
                        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                    )
                    st.plotly_chart(fig_s2, width="stretch")
                    st.write(f"**상관계수(r)**: {r2:.2f}")
                    st.write(
                        "→ r이 1에 가까울수록 지상부가 길수록 생중량이 증가하는 경향이 있어요."
                    )
                else:
                    st.info("지상부 길이와 생중량 데이터가 충분하지 않아요.")
            else:
                st.info("지상부 길이와 생중량 데이터가 둘 다 필요해요.")

            st.markdown("---")

            # ── 상위 25% vs 하위 25% 비교 ────────────────────────────────
            if "생중량" in growth_df.columns:
                gv = growth_df["생중량"].dropna()
                if len(gv) >= 4:
                    q75 = gv.quantile(0.75)
                    q25 = gv.quantile(0.25)
                    top = growth_df[growth_df["생중량"] >= q75].dropna(subset=["생중량"])
                    bottom = growth_df[growth_df["생중량"] <= q25].dropna(subset=["생중량"])

                    st.subheader("📈 생중량 상위 25% vs 하위 25% 비교")

                    comp_cols = [c for c in ["잎 수", "지상부 길이", "지하부 길이"] if c in growth_df.columns]
                    if comp_cols:
                        comp_data = []
                        for col in comp_cols:
                            top_mean = top[col].dropna().mean() if len(top[col].dropna()) > 0 else np.nan
                            bottom_mean = bottom[col].dropna().mean() if len(bottom[col].dropna()) > 0 else np.nan
                            comp_data.append(
                                [
                                    col,
                                    f"{top_mean:.1f}" if pd.notna(top_mean) else "N/A",
                                    f"{bottom_mean:.1f}" if pd.notna(bottom_mean) else "N/A",
                                ]
                            )
                        st.dataframe(
                            pd.DataFrame(comp_data, columns=["지표", "상위 25% 평균", "하위 25% 평균"]),
                            width="stretch",
                            hide_index=True,
                        )
                    else:
                        st.info("비교할 생육 지표가 없어요.")
                else:
                    st.info("개체 수가 너무 적어서 상위/하위 25%를 나눌 수 없어요.")

            with st.expander("📋 생육 데이터 원본 테이블"):
                st.dataframe(growth_df, width="stretch")
                csv_download(growth_df, "생육 데이터 다운로드")

    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")
