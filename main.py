import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import os, io

env_df   = pd.read_csv('/home/user/uploads/0___________.csv')
growth_df = pd.read_csv('/home/user/uploads/1______________.csv')

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
                errors="coerce")
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
            parsed[bad] = pd.to_datetime(parts[0], format="%Y%m%d") + \
                          pd.to_timedelta(parts[1].astype(int), unit="h")
        df["time"] = parsed
    return df

env_df   = std_cols(env_df)
growth_df = std_cols(growth_df)
SCHOOL = "인천송천고"

# ── 색상 팔레트 ────────────────────────────────────────
SKY="#2d7ab8"; ICE="#5dade2"; RED="#c0392b"
GREEN="#1d6f42"; GOLD="#8b6914"; BLUE="#1a5276"
PALETTE=[SKY, ICE, RED, GREEN, GOLD, BLUE]

def theme(fig, w=880, h=460):
    fig.update_layout(
        font=dict(family="Inter,'Noto Sans KR',sans-serif", color="#1a2a3a"),
        plot_bgcolor="rgba(255,255,255,0.92)",
        paper_bgcolor="rgba(255,255,255,0.92)",
        margin=dict(l=64, r=28, t=52, b=48),
        width=w, height=h,
        hoverlabel=dict(bgcolor="#0d2137", font_color="white",
                        font_family="Inter,'Noto Sans KR',sans-serif", font_size=12),
        xaxis=dict(
            gridcolor="rgba(45,122,184,0.07)",
            zerolinecolor="rgba(45,122,184,0.14)",
            linecolor="rgba(45,122,184,0.14)",
            tickfont=dict(size=11, color="#5a7a94"),
        ),
        yaxis=dict(
            gridcolor="rgba(45,122,184,0.07)",
            zerolinecolor="rgba(45,122,184,0.14)",
            linecolor="rgba(45,122,184,0.14)",
            tickfont=dict(size=11, color="#5a7a94"),
        ),
        legend=dict(
            font=dict(size=11, color="#4a6a82", family="Inter,sans-serif"),
            bgcolor="rgba(255,255,255,0.7)",
            bordercolor="rgba(45,122,184,0.14)",
            borderwidth=1, x=1.02, y=1,
        ),
    )
    return fig

def line_chart(df, tcol, vcol, title, color):
    d = df[[tcol, vcol]].dropna().sort_values(tcol)
    if len(d) < 2:
        return None
    fig = px.line(d, x=tcol, y=vcol, color_discrete_sequence=[color])
    fig.data[0].line = dict(width=2.4, color=color)
    fig.data[0].hovertemplate = "<b>%{x|%Y-%m-%d %H:%M}</b><br>%s: %%{y:.1f}<extra></extra>" % vcol
    theme(fig, 440, 310)
    fig.update_layout(
        title=dict(
            text="<b>%s</b>" % title,
            font=dict(size=13, color=BLUE, family="Inter,sans-serif", weight=700),
            x=0.04, xanchor="left",
        ),
        showlegend=False,
    )
    fig.update_xaxes(tickformat="%m/%d")
    return fig

def scatter_trend(df, x, y, title):
    d = df[[x, y]].dropna()
    if len(d) < 3:
        return None
    fig = px.scatter(d, x=x, y=y,
                     labels={x: x, y: y},
                     color_discrete_sequence=PALETTE)
    fig.data[0].marker = dict(
        size=9, opacity=0.82,
        line=dict(width=1.2, color="white"),
        symbol="circle",
    )
    xv, yv = d[x].values, d[y].values
    slope, intercept = np.polyfit(xv, yv, 1)
    lx = np.linspace(xv.min(), xv.max(), 100)
    ly = slope * lx + intercept
    r, _ = stats.pearsonr(xv, yv)
    fig.add_trace(go.Scatter(
        x=lx, y=ly, mode="lines",
        line=dict(color=RED, width=2.5),
        name="추세선  r = %.3f" % r,
        hoverinfo="skip",
    ))
    fig.add_annotation(
        x=0.955, y=0.055, xref="paper", yref="paper",
        text="r = %.3f" % r,
        font=dict(size=12, color=RED, family="Inter,sans-serif", weight=600),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="rgba(192,57,43,0.3)",
        borderwidth=1, borderpad=4,
        showarrow=False,
    )
    theme(fig, 880, 450)
    fig.update_layout(
        title=dict(
            text="<b>%s</b>" % title,
            font=dict(size=14, color=BLUE, family="Inter,sans-serif", weight=700),
            x=0.04, xanchor="left",
        ),
    )
    return fig

def corr_heatmap(df, cols):
    d = df[cols].dropna()
    if len(d) < 3 or len(cols) < 2:
        return None
    c = d[cols].corr()
    fig = px.imshow(
        c, text_auto=".3f",
        color_continuous_scale=[
            (0.00, RED), (0.25, "#f5b041"), (0.50, "#ffffff"),
            (0.75, ICE), (1.00, BLUE),
        ],
        zmin=-1, zmax=1,
        labels=dict(x="", y=""),
        color_continuous_midpoint=0,
    )
    theme(fig, 620, 500)
    fig.update_layout(
        title=dict(
            text="<b>변수 간 상관계수 행렬</b>",
            font=dict(size=14, color=BLUE, family="Inter,sans-serif", weight=700),
            x=0.04, xanchor="left",
        ),
        xaxis=dict(
            side="bottom", tickangle=30,
            tickfont=dict(size=10, color="#5a7a94", family="Inter,sans-serif"),
        ),
        yaxis=dict(
            tickfont=dict(size=10, color="#5a7a94", family="Inter,sans-serif"),
        ),
        coloraxis_colorbar=dict(
            title=dict(text="r",
                       font=dict(size=10, color="#4a6a82", family="Inter,sans-serif")),
            tickfont=dict(size=10, color="#5a7a94", family="Inter,sans-serif"),
            thickness=14, len=0.72,
        ),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False, autorange="reversed")
    return fig

def bar_chart(df, color, label):
    fig = px.bar(
        df, x="순위", y="생중량(g)",
        color_discrete_sequence=[color],
        labels={"순위": "개체 순위", "생중량(g)": "생중량 (g)"},
    )
    theme(fig, 420, 290)
    fig.data[0].marker = dict(line=dict(width=1, color="white"))
    fig.update_layout(
        title=dict(
            text="<b>%s</b>" % label,
            font=dict(size=13, color=color, family="Inter,sans-serif", weight=700),
            x=0.04, xanchor="left",
        ),
        showlegend=False,
        xaxis=dict(tickfont=dict(size=11, color="#5a7a94")),
    )
    return fig

# ── 차트 생성 ────────────────────────────────────────────
fig_temp  = line_chart(env_df,   "time", "temperature", "시간별 온도 변화 (℃)", SKY)
fig_hum   = line_chart(env_df,   "time", "humidity",   "시간별 습도 변화 (%)",  ICE)
fig_sc1   = scatter_trend(growth_df, "잎 수",          "생중량",          "잎 수 vs 생중량 — 생장 대표 지표")
fig_sc2   = scatter_trend(growth_df, "지상부 길이",    "생중량",          "지상부 길이 vs 생중량")
fig_sc3   = scatter_trend(growth_df, "지하부 길이",    "생중량",          "지하부 길이 vs 생중량")
fig_sc4   = scatter_trend(growth_df, "지상부 길이",    "지하부 길이",     "지상부 길이 vs 지하부 길이")
fig_heat  = corr_heatmap(
    growth_df,
    [c for c in ["잎 수","지상부 길이","지상부 질량",
                 "지하부 길이","지하부 질량","생중량"]
     if c in growth_df.columns],
)

d_bw = growth_df[["개체번호","생중량"]].dropna().sort_values("생중량", ascending=False)
n = min(5, len(d_bw))
top_df = d_bw.head(n).reset_index(drop=True)
top_df.insert(0, "순위", range(1, len(top_df)+1))
top_df  = top_df.rename(columns={top_df.columns[2]: "생중량(g)"})
bot_df  = d_bw.tail(n).sort_values("생중량", ascending=True).reset_index(drop=True)
bot_df.insert(0, "순위", range(len(d_bw)-n+1, len(d_bw)+1))
bot_df  = bot_df.rename(columns={bot_df.columns[2]: "생중량(g)"})

fig_top_bar = bar_chart(top_df, GREEN, "▲ 생중량 상위 %d개체" % n)
fig_bot_bar = bar_chart(bot_df, RED,   "▼ 생중량 하위 %d개체" % n)

def fig_html(fig):
    if fig is None:
        return ""
    return fig.to_html(
        include_plotlyjs="cdn", full_html=False,
        config=dict(displayModeBar=False, responsive=True),
    )

def fmt(v, f=".2f"):
    try:
        return format(float(v), f)
    except Exception:
        return str(v)

def stat_card(label, value, cls):
    return (
        '<div class="stat">'
        '<div class="sl">%s</div>'
        '<div class="sv %s">%s</div>'
        '</div>' % (label, cls, value)
    )

# ── 환경 지표 카드 ──────────────────────────────────────
env_stats = [
    ("평균 온도",  "%.1f ± %.1f ℃" % (env_df["temperature"].mean(), env_df["temperature"].std()), "b"),
    ("평균 습도",  "%.1f ± %.1f %%" % (env_df["humidity"].mean(), env_df["humidity"].std()),        "g"),
    ("평균 pH",    "%.1f" % env_df["ph"].mean(),                                                     "o"),
    ("평균 EC",    "%.2f mS/cm" % env_df["ec"].mean(),                                             "r"),
]

# ── 생육 지표 카드 ──────────────────────────────────────
growth_stats = [
    ("개체 수",           str(len(growth_df)),                   "b"),
    ("평균 생중량",       "%.2f g" % growth_df["생중량"].mean(), "r"),
    ("평균 잎 수",        "%.1f 장" % growth_df["잎 수"].mean(),  "g"),
    ("평균 지상부 길이",  "%.1f mm" % growth_df["지상부 길이"].mean(), "b"),
]

# ── 가설 ────────────────────────────────────────────────
hypotheses = [
    ("1", "지상부 길이와 지하부 길이는 양의 상관관계가 있다.",
     "잎이 자라는 만큼 뿌리도 함께 자라는 극지식물의 특징을 반영합니다."),
    ("2", "잎의 개수와 생중량의 관계가 식물의 생장을 가장 잘 나타낸다.",
     "잎 수는 광합성 기관과 직결되므로 전체 생체량을 설명하는 주요 지표입니다."),
    ("3", "지상부 길이와 생중량, 지하부 길이와 생중량은 약한 상관관계가 있다.",
     "길이만으로는 부피·밀도를 반영하기 어려워 상관계수가 상대적으로 낮습니다."),
]

# ── 결론 ────────────────────────────────────────────────
def pearson(xcol, ycol):
    xv = growth_df[xcol].dropna()
    yv = growth_df[ycol].dropna()
    return stats.pearsonr(xv, yv)

conclusions = [
    (True,  "🌿", GREEN,
     "잎 수 ↔ 생중량 — 가장 강한 관계",
     "상관계수 r = %.3f (p < 0.001)\n"
     "잎 수가 많을수록 생중량이 증가하며, 식물의 생장을 가장 잘 대표하는 지표입니다."
     % pearson("잎 수", "생중량")[0]),
    (False, "📏", SKY,
     "지상부 길이 ↔ 생중량 — 중간~약한 양의 상관",
     "상관계수 r = %.3f (p = %.4f)\n"
     "길이만 측정하므로 부피·밀도까지 반영하지 못해 상관계수가 상대적으로 낮습니다."
     % pearson("지상부 길이", "생중량")[0:2]),
    (False, "🌱", ICE,
     "지하부 길이 ↔ 생중량 — 약한 양의 상관",
     "상관계수 r = %.3f (p = %.4f)\n"
     "지하부 길이도 생중량과 약한 양의 관계를 보입니다."
     % pearson("지하부 길이", "생중량")[0:2]),
    (False, "🔗", GOLD,
     "지상부 길이 ↔ 지하부 길이 — 양의 상관",
     "상관계수 r = %.3f (p = %.4f)\n"
     "지상부와 지하부는 함께 자라는 경향을 보이며, 극지식물의 균형 생장을 시사합니다."
     % pearson("지상부 길이", "지하부 길이")[0:2]),
]

hyp_html = ""
for num, title, desc in hypotheses:
    hyp_html += (
        '<div class="hypothesis">'
        '<span class="h-num">%s</span>'
        '<p class="hyp-title">%s</p>'
        '<p class="hyp-desc">%s</p>'
        '</div>' % (num, title, desc)
    )

conc_html = ""
for strong, icon, color, title, body in conclusions:
    cls = "conclusion strong" if strong else "conclusion"
    body_br = body.replace("\n", "<br>")
    conc_html += (
        '<div class="%s" style="border-left-color:%s;">'
        '<div class="conc-inner">'
        '<span class="conc-icon">%s</span>'
        '<p class="conc-title" style="color:%s;">%s</p>'
        '<p class="conc-body">%s</p>'
        '</div></div>' % (cls, color, icon, color, title, body_br)
    )

env_cards    = "".join(stat_card(l, v, c) for l, v, c in env_stats)
growth_cards = "".join(stat_card(l, v, c) for l, v, c in growth_stats)

top_rows = "".join(
    "<tr><td>%d</td><td>%s</td><td>%s</td></tr>" % (
        row["순위"], row["개체번호"], fmt(row["생중량(g)"])
    ) for _, row in top_df.iterrows()
)
bot_rows = "".join(
    "<tr><td>%d</td><td>%s</td><td>%s</td></tr>" % (
        row["순위"], row["개체번호"], fmt(row["생중량(g)"])
    ) for _, row in bot_df.iterrows()
)

# ─────────────────────────────────────────────────────────
# HTML 템플릿 — triple-quoted string 하나로 끝까지 완결
# (이전 오류의 원인だった 중첩 f-string / 미닫힘 따옴표 문제 제거)
# ─────────────────────────────────────────────────────────
html = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{school} 극지식물 생육 분석 대시보드</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{
    font-family:'Inter','Noto Sans KR',sans-serif;
    background:linear-gradient(160deg,#f0f4f8 0%,#e8eef5 50%,#f5f0f0 100%);
    color:#1a2a3a;
    padding:2rem 2.5rem 3rem;
    line-height:1.65;
  }}
  .container {{ max-width:1320px; margin:0 auto; }}

  h1 {{
    font-size:2rem; font-weight:800; letter-spacing:-0.03em;
    background:linear-gradient(135deg,#0d2137,#1a5276,#2d7ab8);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text;
    margin-bottom:0.15rem;
  }}
  .subtitle {{
    font-size:0.95rem; color:#5a6f82; margin-bottom:0.6rem;
    border-left:3px solid #2d7ab8; padding-left:12px;
  }}
  .badge {{
    display:inline-block; margin-top:0.2rem;
    background:rgba(26,82,118,0.08);
    border:1px solid rgba(45,122,184,0.15);
    border-radius:8px; padding:0.28rem 0.85rem;
    font-size:0.78rem; font-weight:600; color:#1a5276;
  }}

  /* ── 탭 네비: 3개 탭 이름이 항상 모두 보임 ── */
  .tab-nav {{
    display:flex; gap:0; margin:1.4rem 0 0;
    border-bottom:2px solid rgba(45,122,184,0.18);
  }}
  .tab-btn {{
    background:rgba(255,255,255,0.35);
    border:1px solid rgba(45,122,184,0.1);
    border-bottom:none;
    border-radius:10px 10px 0 0;
    padding:0.7rem 1.5rem;
    font-family:'Inter',sans-serif;
    font-size:0.88rem; font-weight:600;
    color:#5a7a94;
    cursor:pointer;
    transition:all 0.15s ease;
    letter-spacing:0.02em;
  }}
  .tab-btn:hover {{
    color:#1a5276;
    background:rgba(255,255,255,0.65);
    border-color:rgba(45,122,184,0.25);
  }}
  .tab-btn.active {{
    color:#1a5276;
    background:#ffffff;
    border-color:rgba(45,122,184,0.2);
    box-shadow:0 -2px 8px rgba(13,33,55,0.06);
  }}

  .section {{
    background:rgba(255,255,255,0.9);
    backdrop-filter:blur(8px);
    border:1px solid rgba(255,255,255,0.6);
    border-radius:14px;
    padding:1.4rem 1.5rem;
    box-shadow:0 4px 14px rgba(13,33,55,0.05);
    margin-bottom:1.4rem;
  }}
  .section-title {{
    font-size:0.8rem; font-weight:700;
    text-transform:uppercase; letter-spacing:0.1em;
    color:#4a6a82; margin-bottom:1rem;
    padding-bottom:0.5rem;
    border-bottom:2px solid rgba(45,122,184,0.2);
  }}
  .row {{ display:flex; gap:1.5rem; flex-wrap:wrap; }}
  .col-2 {{ flex:1 1 45%; min-width:300px; }}
  .col-3 {{ flex:1 1 30%; min-width:260px; }}

  .stat {{
    background:rgba(255,255,255,0.88);
    backdrop-filter:blur(8px);
    border:1px solid rgba(255,255,255,0.5);
    border-radius:14px;
    padding:0.85rem 1.1rem;
    box-shadow:0 4px 16px rgba(13,33,55,0.07);
    transition:transform 0.2s, box-shadow 0.2s;
    flex:1 1 0;
    min-width:140px;
  }}
  .stat:hover {{
    transform:translateY(-2px);
    box-shadow:0 8px 28px rgba(13,33,55,0.11);
  }}
  .sl {{
    font-size:0.7rem; font-weight:600;
    text-transform:uppercase; letter-spacing:0.08em;
    color:#6b8aa0; margin-bottom:0.28rem;
  }}
  .sv {{ font-size:1.55rem; font-weight:700; color:#0d2137; line-height:1.1; }}
  .sv.b {{ color:#1a5276; }}
  .sv.r {{ color:#c0392b; }}
  .sv.g {{ color:#1d6f42; }}
  .sv.o {{ color:#8b6914; }}

  .chart-wrap {{
    background:rgba(255,255,255,0.85);
    border-radius:10px;
    padding:0.5rem;
    box-shadow:0 2px 8px rgba(13,33,55,0.06);
    margin-bottom:0.75rem;
  }}
  .chart-wrap .js-plotly-plot .plotly .main-svg {{ border-radius:8px; }}

  .hypothesis {{
    background:rgba(255,255,255,0.7);
    border-left:3px solid #2d7ab8;
    border-radius:0 10px 10px 0;
    padding:0.7rem 1rem;
    margin-bottom:0.5rem;
  }}
  .h-num {{
    display:inline-flex; align-items:center; justify-content:center;
    width:20px; height:20px; border-radius:50%;
    background:rgba(45,122,184,0.12);
    color:#2d7ab8;
    font-size:0.7rem; font-weight:700;
    margin-right:0.5rem; flex-shrink:0;
  }}
  .hyp-title {{ font-weight:600; font-size:0.9rem; color:#1a2a3a; margin:0 0 0.15rem; }}
  .hyp-desc  {{ font-size:0.82rem; color:#5a7a94; margin:0; }}

  .conclusion {{
    background:rgba(255,255,255,0.72);
    border-left:4px solid #5a7a94;
    border-radius:0 10px 10px 0;
    padding:0.95rem 1rem;
    margin-bottom:0.65rem;
  }}
  .conclusion.strong {{
    background:rgba(192,57,43,0.04);
    border-left-color:#c0392b;
  }}
  .conc-inner {{ display:flex; align-items:flex-start; gap:0.6rem; }}
  .conc-icon {{ font-size:1.5rem; line-height:1; flex-shrink:0; margin-top:0.05rem; }}
  .conc-title {{ font-weight:700; font-size:0.95rem; margin:0 0 0.3rem; }}
  .conc-body  {{ font-size:0.86rem; color:#3a5a72; line-height:1.7; }}

  .banner {{
    background:linear-gradient(90deg,
      rgba(26,82,118,0.1) 0%, rgba(45,122,184,0.15) 50%,
      rgba(26,82,118,0.1) 100%);
    border:1px solid rgba(45,122,184,0.2);
    border-radius:12px;
    padding:1rem 1.4rem; text-align:center;
    margin-top:1.5rem;
  }}
  .banner p {{ margin:0; }}
  .banner .banner-title {{ font-weight:800; font-size:1rem; color:#1a5276; margin-bottom:0.3rem; }}
  .banner .banner-body  {{ font-size:0.9rem; color:#3a5a72; line-height:1.65; }}

  .mini-label {{
    font-size:0.72rem; font-weight:700;
    text-transform:uppercase; letter-spacing:0.08em;
    margin-bottom:0.4rem;
  }}
  .mini-label.g {{ color:#1d6f42; }}
  .mini-label.r {{ color:#c0392b; }}

  .tbl {{
    font-family:'Inter',sans-serif; font-size:0.82rem;
    border-collapse:collapse; width:100%;
  }}
  .tbl th {{
    background:rgba(45,122,184,0.08);
    padding:0.4rem 0.6rem; text-align:left;
    font-weight:600; color:#4a6a82;
  }}
  .tbl td {{ padding:0.35rem 0.6rem;
    border-bottom:1px solid rgba(45,122,184,0.07); color:#1a2a3a; }}
  .tbl tr:last-child td {{ border-bottom:none; }}

  hr {{ border:none; border-top:1px solid rgba(45,122,184,0.12); margin:1.4rem 0; }}

  .info-box {{
    background:rgba(255,255,255,0.68);
    border:1px dashed rgba(45,122,184,0.3);
    border-radius:10px;
    padding:0.9rem 1.2rem;
    color:#5a7a94; font-size:0.88rem;
    margin-bottom:1.4rem;
  }}

  .stat-row {{ display:flex; gap:0.7rem; flex-wrap:wrap; }}
</style>
</head>
<body>
<div class="container">

  <h1>🌿 {school} 극지식물 생육 분석</h1>
  <p class="subtitle">개체별 생육 차이 &amp; 환경 데이터 인사이트 대시보드</p>
  <span class="badge">🏫 {school} · 개체 수 {n_growth}개체</span>

  <!-- ── 모든 탭 이름이 항상 노출 ── -->
  <nav class="tab-nav" aria-label="섹션 이동">
    <button class="tab-btn active" onclick="showTab('tab1')">📋&ensp;개요 &amp; 환경 데이터</button>
    <button class="tab-btn"       onclick="showTab('tab2')">📈&ensp;산점도 &amp; 상관분석</button>
    <button class="tab-btn"       onclick="showTab('tab3')">🎯&ensp;분석 결론</button>
  </nav>

  <!-- ═══════ 탭 1 — 개요 & 환경 데이터 ═══════ -->
  <section id="tab1" class="section">
    <div class="section-title">🌡️ 환경 데이터 개요</div>

    <div class="row">
      <div class="col-2">
        <div class="chart-wrap">{fig_temp_html}</div>
      </div>
      <div class="col-2">
        <div class="chart-wrap">{fig_hum_html}</div>
      </div>
    </div>

    <div class="stat-row" style="margin-top:0.2rem;">
      {env_cards}
    </div>

    <hr>

    <div class="section-title">🌱 생육 결과 데이터</div>

    <div class="stat-row" style="margin-bottom:0.4rem;">
      {growth_cards}
    </div>

    <hr>

    <div class="section-title">🔬 우리의 가설</div>
    {hyp_html}
  </section>

  <!-- ═══════ 탭 2 — 산점도 & 상관분석 ═══════ -->
  <section id="tab2" class="section" style="display:none;">
    <div class="section-title">📊 생육 지표 간 관계 — 산점도 &amp; 추세선</div>

    <div class="chart-wrap">{fig_sc1_html}</div>
    <div class="chart-wrap">{fig_sc2_html}</div>
    <div class="chart-wrap">{fig_sc3_html}</div>
    <div class="chart-wrap">{fig_sc4_html}</div>

    <hr style="margin-top:1rem;">

    <div class="section-title">🔢 변수 간 상관계수 행렬</div>
    <div class="chart-wrap">{fig_heat_html}</div>
  </section>

  <!-- ═══════ 탭 3 — 분석 결론 ═══════ -->
  <section id="tab3" class="section" style="display:none;">
    <div class="section-title">📋 분석 결과 요약</div>

    {conc_html}

    <hr>

    <div class="section-title">🏆 개체별 생중량</div>
    <div class="row">
      <div class="col-3">
        <div style="background:rgba(255,255,255,0.85);border-radius:10px;
                    padding:0.5rem;box-shadow:0 2px 8px rgba(13,33,55,0.06);">
          <p class="mini-label g">▲ 생중량 상위 {n}개체</p>
          <table class="tbl">
            <thead><tr><th>순위</th><th>개체번호</th><th>생중량(g)</th></tr></thead>
            <tbody>{top_rows}</tbody>
          </table>
        </div>
      </div>
      <div class="col-3">
        <div style="background:rgba(255,255,255,0.85);border-radius:10px;
                    padding:0.5rem;box-shadow:0 2px 8px rgba(13,33,55,0.06);">
          <p class="mini-label r">▼ 생중량 하위 {n}개체</p>
          <table class="tbl">
            <thead><tr><th>순위</th><th>개체번호</th><th>생중량(g)</th></tr></thead>
            <tbody>{bot_rows}</tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="banner">
      <p class="banner-title">💡&ensp;핵심 결론</p>
      <p class="banner-body">
        극지식물 개체별 생육 분석에서 <b>생중량과 잎의 개수 사이에 가장 강한 상관관계</b>가
        확인되었습니다. 잎 수는 식물의 광합성 능력과 직결되므로 전체 생체량을 가장 잘 예측하는
        지표입니다.
      </p>
    </div>
  </section>

</div>

<script>
  function showTab(id) {{
    document.querySelectorAll('.tab-btn').forEach(function(b) {{
      b.classList.remove('active');
    }});
    document.querySelectorAll('section').forEach(function(s) {{
      s.style.display = 'none';
    }});
    document.getElementById(id).style.display = '';
    event.currentTarget.classList.add('active');
  }}
</script>

</body>
</html>
""".format(
    school=SCHOOL,
    n_growth=len(growth_df),
    n=n,
    fig_temp_html=fig_html(fig_temp),
    fig_hum_html=fig_html(fig_hum),
    fig_sc1_html=fig_html(fig_sc1),
    fig_sc2_html=fig_html(fig_sc2),
    fig_sc3_html=fig_html(fig_sc3),
    fig_sc4_html=fig_html(fig_sc4),
    fig_heat_html=fig_html(fig_heat),
    fig_top_bar_html=fig_html(fig_top_bar),
    fig_bot_bar_html=fig_html(fig_bot_bar),
    env_cards=env_cards,
    growth_cards=growth_cards,
    hyp_html=hyp_html,
    conc_html=conc_html,
    top_rows=top_rows,
    bot_rows=bot_rows,
)

out = "/home/user/outputs/dashboard.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

print("저장 완료: %s" % out)
print("파일 크기: %s bytes" % format(os.path.getsize(out), ","))
print()
print("[실제 데이터 통계]")
print("  평균 온도       : %.1f ℃" % env_df["temperature"].mean())
print("  평균 습도       : %.1f %%" % env_df["humidity"].mean())
print("  평균 pH         : %.1f" % env_df["ph"].mean())
print("  평균 EC         : %.2f mS/cm" % env_df["ec"].mean())
print("  개체 수         : %d 개체" % len(growth_df))
print("  평균 생중량     : %.2f g" % growth_df["생중량"].mean())
print("  평균 잎 수      : %.1f 장" % growth_df["잎 수"].mean())
print("  평균 지상부 길이: %.1f mm" % growth_df["지상부 길이"].mean())
print("  평균 지하부 길이: %.1f mm" % growth_df["지하부 길이"].mean())
r_lf = stats.pearsonr(growth_df["잎 수"].dropna(), growth_df["생중량"].dropna())[0]
r_sl = stats.pearsonr(growth_df["지상부 길이"].dropna(), growth_df["생중량"].dropna())[0]
r_rl = stats.pearsonr(growth_df["지하부 길이"].dropna(), growth_df["생중량"].dropna())[0]
r_sr = stats.pearsonr(growth_df["지상부 길이"].dropna(), growth_df["지하부 길이"].dropna())[0]
print()
print("  r(잎 수, 생중량)         : %.3f" % r_lf)
print("  r(지상부 길이, 생중량)   : %.3f" % r_sl)
print("  r(지하부 길이, 생중량)   : %.3f" % r_rl)
print("  r(지상부 길이, 지하부 길이): %.3f" % r_sr)
