import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import os

# ── 데이터 ──────────────────────────────────────────────────
env_raw   = open('/home/user/uploads/0___________.csv','rb').read()
growth_raw = open('/home/user/uploads/1______________.csv','rb').read()

def std_cols(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    rename = {}
    for c in df.columns:
        k = c.lower().replace(" ","")
        if k in ("time","categories","시간","날짜","datetime","date"):
            rename[c] = "time"
        elif k in ("temperature","온도"):
            rename[c] = "temperature"
        elif k in ("humidity","습도"):
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
        if c in ("time","개체번호"):
            continue
        if not pd.api.types.is_numeric_dtype(df[c]):
            num = pd.to_numeric(
                df[c].astype(str).str.replace(",","")
                .str.extract(r"(-?\d+\.?\d*)")[0],
                errors="coerce")
            if num.notna().mean() >= 0.5:
                df[c] = num
    if "생중량" not in df.columns and {"지상부 질량","지하부 질량"} <= set(df.columns):
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

env_df   = std_cols(pd.read_csv('/home/user/uploads/0___________.csv'))
growth_df = std_cols(pd.read_csv('/home/user/uploads/1______________.csv'))
SCHOOL = "인천송천고"

# ── 색상 ──────────────────────────────────────────────────
SKY="#2d7ab8"; ICE="#5dade2"; RED="#c0392b"
GREEN="#1d6f42"; GOLD="#8b6914"; BLUE="#1a5276"
PALETTE=[SKY,ICE,RED,GREEN,GOLD,BLUE]

def theme(fig,w=880,h=480):
    fig.update_layout(
        font=dict(family="Inter,'Noto Sans KR',sans-serif",color="#1a2a3a"),
        plot_bgcolor="rgba(255,255,255,0.95)",
        paper_bgcolor="rgba(255,255,255,0.95)",
        margin=dict(l=60,r=30,t=50,b=50),width=w,height=h,
        hoverlabel=dict(bgcolor="#0d2137",font_color="white",
                        font_family="Inter,'Noto Sans KR',sans-serif",font_size=12),
        xaxis=dict(gridcolor="rgba(45,122,184,0.08)",
                   zerolinecolor="rgba(45,122,184,0.15)",
                   linecolor="rgba(45,122,184,0.15)",
                   tickfont=dict(size=11,color="#5a7a94")),
        yaxis=dict(gridcolor="rgba(45,122,184,0.08)",
                   zerolinecolor="rgba(45,122,184,0.15)",
                   linecolor="rgba(45,122,184,0.15)",
                   tickfont=dict(size=11,color="#5a7a94")),
        legend=dict(font=dict(size=11,color="#4a6a82",family="Inter,sans-serif"),
                    bgcolor="rgba(255,255,255,0.7)",
                    bordercolor="rgba(45,122,184,0.15)",borderwidth=1,x=1.02,y=1),
    )
    return fig

def line_chart(df,tcol,vcol,title,color):
    d=df[[tcol,vcol]].dropna().sort_values(tcol)
    if len(d)<2: return None
    fig=px.line(d,x=tcol,y=vcol,color_discrete_sequence=[color])
    fig.data[0].line=dict(width=2.2,color=color)
    fig.data[0].hovertemplate=f"<b>%{{x|%Y-%m-%d %H:%M}}</b><br>{vcol}: %{{y:.1f}}<extra></extra>"
    theme(fig,440,300)
    fig.update_layout(title=dict(text=f"<b>{title}</b>",
        font=dict(size=13,color=BLUE,family="Inter,sans-serif",weight=700),x=0.04,xanchor="left"),
        showlegend=False)
    fig.update_xaxes(tickformat="%m/%d")
    return fig

def scatter_trend(df,x,y,title):
    d=df[[x,y]].dropna()
    if len(d)<3: return None
    fig=px.scatter(d,x=x,y=y,labels={x:x,y:y},color_discrete_sequence=PALETTE)
    fig.data[0].marker=dict(size=9,opacity=0.82,
        line=dict(width=1.2,color="white"),symbol="circle")
    xv,yv=d[x].values,d[y].values
    slope,intercept=np.polyfit(xv,yv,1)
    lx=np.linspace(xv.min(),xv.max(),100)
    ly=slope*lx+intercept
    r,_=stats.pearsonr(xv,yv)
    fig.add_trace(go.Scatter(x=lx,y=ly,mode="lines",
        line=dict(color=RED,width=2.5),name=f"추세선  r = {r:.3f}",hoverinfo="skip"))
    fig.add_annotation(x=0.96,y=0.06,xref="paper",yref="paper",
        text=f"r = {r:.3f}",
        font=dict(size=12,color=RED,family="Inter,sans-serif",weight=600),
        bgcolor="rgba(255,255,255,0.85)",bordercolor="rgba(192,57,43,0.3)",
        borderwidth=1,borderpad=4,showarrow=False)
    theme(fig,880,460)
    fig.update_layout(title=dict(text=f"<b>{title}</b>",
        font=dict(size=14,color=BLUE,family="Inter,sans-serif",weight=700),
        x=0.04,xanchor="left"))
    return fig

def corr_heatmap(df,cols):
    d=df[cols].dropna()
    if len(d)<3 or len(cols)<2: return None
    c=d[cols].corr()
    fig=px.imshow(c,text_auto=".3f",
        color_continuous_scale=[(0.00,RED),(0.25,"#f5b041"),(0.50,"#ffffff"),
                                 (0.75,ICE),(1.00,BLUE)],
        zmin=-1,zmax=1,labels=dict(x="",y=""),color_continuous_midpoint=0)
    theme(fig,620,500)
    fig.update_layout(title=dict(text="<b>변수 간 상관계수 행렬</b>",
        font=dict(size=14,color=BLUE,family="Inter,sans-serif",weight=700),
        x=0.04,xanchor="left"),
        xaxis=dict(side="bottom",tickangle=30,
                   tickfont=dict(size=10,color="#5a7a94",family="Inter,sans-serif")),
        yaxis=dict(tickfont=dict(size=10,color="#5a7a94",family="Inter,sans-serif")),
        coloraxis_colorbar=dict(title=dict(text="r",
            font=dict(size=10,color="#4a6a82",family="Inter,sans-serif")),
            tickfont=dict(size=10,color="#5a7a94",family="Inter,sans-serif"),
            thickness=14,len=0.7))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False,autorange="reversed")
    return fig

# ── 차트 생성 ──────────────────────────────────────────────────
fig_temp = line_chart(env_df,"time","temperature","시간별 온도 변화 (℃)",SKY)
fig_hum  = line_chart(env_df,"time","humidity","시간별 습도 변화 (%)",ICE)
fig_sc1  = scatter_trend(growth_df,"잎 수","생중량","잎 수 vs 생중량 — 생장 대표 지표")
fig_sc2  = scatter_trend(growth_df,"지상부 길이","생중량","지상부 길이 vs 생중량")
fig_sc3  = scatter_trend(growth_df,"지하부 길이","생중량","지하부 길이 vs 생중량")
fig_sc4  = scatter_trend(growth_df,"지상부 길이","지하부 길이","지상부 길이 vs 지하부 길이")
fig_heat = corr_heatmap(growth_df,
    [c for c in ["잎 수","지상부 길이","지상부 질량","지하부 길이","지하부 질량","생중량"]
     if c in growth_df.columns])

# ── 막대그래프 (상위/하위) ──────────────────────────────────────
d_bw = growth_df[["개체번호","생중량"]].dropna().sort_values("생중량",ascending=False)
n = min(5, len(d_bw))
top_df  = d_bw.head(n).reset_index(drop=True)
top_df.insert(0,"순위",range(1,len(top_df)+1))
top_df  = top_df.rename(columns={top_df.columns[2]:"생중량(g)"})
bot_df  = d_bw.tail(n).sort_values("생중량",ascending=True).reset_index(drop=True)
bot_df.insert(0,"순위",range(len(d_bw)-n+1,len(d_bw)+1))
bot_df  = bot_df.rename(columns={bot_df.columns[2]:"생중량(g)"})

def bar_chart(df, color, label):
    fig = px.bar(df, x="순위", y="생중량(g)",
                 color_discrete_sequence=[color],
                 labels={"순위":"개체 순위","생중량(g)":"생중량 (g)"})
    theme(fig, 420, 300)
    fig.data[0].marker = dict(line=dict(width=1, color="white"))
    fig.update_layout(
        title=dict(text=f"<b>{label}</b>",
                   font=dict(size=13, color=color,
                             family="Inter,sans-serif", weight=700),
                   x=0.04, xanchor="left"),
        showlegend=False,
        xaxis=dict(tickfont=dict(size=11, color="#5a7a94")))
    return fig

fig_top_bar = bar_chart(top_df, GREEN, f"▲ 생중량 상위 {n}개체")
fig_bot_bar = bar_chart(bot_df, RED,   f"▼ 생중량 하위 {n}개체")

# ── Plotly → HTML 조각 ─────────────────────────────────────────
def fig_html(fig):
    if fig is None:
        return ""
    return fig.to_html(include_plotlyjs="cdn", full_html=False,
                       config=dict(displayModeBar=False, responsive=True))

def safe(val, fmt=".2f"):
    try:
        return format(float(val), fmt)
    except Exception:
        return str(val)

# ── HTML 조립 ──────────────────────────────────────────────────
# 각 섹션별 HTML을 별도 변수에 담고, 탭 UI 없이 세 섹션을 모두 항상 노출
# (이전 버전의 f-string 중첩에서 생긴 스타일 파편 문제 해소)

env_stats_rows = [
    ("평균 온도",  f"{env_df['temperature'].mean():.1f} ± {env_df['temperature'].std():.1f} ℃",  "b"),
    ("평균 습도",  f"{env_df['humidity'].mean():.1f} ± {env_df['humidity'].std():.1f} %",        "g"),
    ("평균 pH",    f"{env_df['ph'].mean():.1f}",                                                    "o"),
    ("평균 EC",    f"{env_df['ec'].mean():.2f} mS/cm",                                              "r"),
]

growth_stats_rows = [
    ("개체 수",         str(len(growth_df)),               "b"),
    ("평균 생중량",     f"{growth_df['생중량'].mean():.2f} g", "r"),
    ("평균 잎 수",      f"{growth_df['잎 수'].mean():.1f} 장",  "g"),
    ("평균 지상부 길이", f"{growth_df['지상부 길이'].mean():.1f} mm","b"),
]

hypotheses = [
    ("1","지상부 길이와 지하부 길이는 양의 상관관계가 있다.",
     "잎이 자라는 만큼 뿌리도 함께 자라는 극지식물의 특징을 반영합니다."),
    ("2","잎의 개수와 생중량의 관계가 식물의 생장을 가장 잘 나타낸다.",
     "잎 수는 광합성 기관과 직결되므로 전체 생체량을 설명하는 주요 지표입니다."),
    ("3","지상부 길이와 생중량, 지하부 길이와 생중량은 약한 상관관계가 있다.",
     "길이만으로는 부피·밀도를 반영하기 어려워 상관계수가 상대적으로 낮습니다."),
]

conclusions = [
    (True, "🌿", GREEN,
     "잎 수 ↔ 생중량 — 가장 강한 관계",
     "상관계수 r = %.3f (p < 0.001)\n"
     "잎 수가 많을수록 생중량이 증가하며, 식물의 생장을 가장 잘 대표하는 지표입니다." % stats.pearsonr(
         growth_df["잎 수"].dropna(), growth_df["생중량"].dropna())[0]),
    (False,"📏", SKY,
     "지상부 길이 ↔ 생중량 — 중간~약한 양의 상관",
     "상관계수 r = %.3f (p = %.4f)\n"
     "길이만 측정하므로 부피·밀도까지 반영하지 못해 상관계수가 상대적으로 낮습니다." % (
         stats.pearsonr(growth_df["지상부 길이"].dropna(),
                        growth_df["생중량"].dropna())[0],
         stats.pearsonr(growth_df["지상부 길이"].dropna(),
                        growth_df["생중량"].dropna())[1])),
    (False,"🌱", ICE,
     "지하부 길이 ↔ 생중량 — 약한 양의 상관",
     "상관계수 r = %.3f (p = %.4f)\n"
     "지하부 길이도 생중량과 약한 양의 관계를 보입니다." % (
         stats.pearsonr(growth_df["지하부 길이"].dropna(),
                        growth_df["생중량"].dropna())[0],
         stats.pearsonr(growth_df["지하부 길이"].dropna(),
                        growth_df["생중량"].dropna())[1])),
    (False,"🔗", GOLD,
     "지상부 길이 ↔ 지하부 길이 — 양의 상관",
     "상관계수 r = %.3f (p = %.4f)\n"
     "지상부와 지하부는 함께 자라는 경향을 보이며, 극지식물의 균형 생장을 시사합니다." % (
         stats.pearsonr(growth_df["지상부 길이"].dropna(),
                        growth_df["지하부 길이"].dropna())[0],
         stats.pearsonr(growth_df["지상부 길이"].dropna(),
                        growth_df["지하부 길이"].dropna())[1])),
]

# 표 데이터 (상위/하위)
top_rows_html = "".join(
    "<tr><td>%d</td><td>%s</td><td>%s</td></tr>" % (
        row["순위"], row["개체번호"],
        safe(row["생중량(g)"])
    ) for _, row in top_df.iterrows()
)
bot_rows_html = "".join(
    "<tr><td>%d</td><td>%s</td><td>%s</td></tr>" % (
        row["순위"], row["개체번호"],
        safe(row["생중량(g)"])
    ) for _, row in bot_df.iterrows()
)

def stat_card(label, value, cls):
    return (
        '<div class="stat">'
        '<div class="stat-label">%s</div>'
        '<div class="stat-val %s">%s</div>'
        '</div>' % (label, cls, value)
    )

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
    body_html = body.replace("\n", "<br>")
    conc_html += (
        '<div class="%s" style="border-left-color:%s;">'
        '<div class="conc-inner">'
        '<span class="conc-icon">%s</span>'
        '<p class="conc-title" style="color:%s;">%s</p>'
        '<p class="conc-body">%s</p>'
        '</div></div>' % (cls, color, icon, color, title, body_html)
    )

env_stat_cards = "".join(stat_card(l, v, c) for l, v, c in env_stats_rows)
growth_stat_cards = "".join(stat_card(l, v, c) for l, v, c in growth_stats_rows)

# ── 최종 HTML ───────────────────────────────────────────────────
html = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>%s 극지식물 생육 분석 대시보드</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing:border-box; margin:0; padding:0; }
  body {
    font-family:'Inter','Noto Sans KR',sans-serif;
    background:linear-gradient(160deg,#f0f4f8 0%,#e8eef5 50%,#f5f0f0 100%);
    color:#1a2a3a;
    padding:2rem 2.5rem 3rem;
    line-height:1.6;
  }
  .container { max-width:1320px; margin:0 auto; }

  h1 {
    font-size:2rem; font-weight:800; letter-spacing:-0.03em;
    background:linear-gradient(135deg,#0d2137,#1a5276,#2d7ab8);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text; margin-bottom:0.2rem;
  }
  .subtitle {
    font-size:0.95rem; color:#5a6f82; margin-bottom:1.5rem;
    border-left:3px solid #2d7ab8; padding-left:12px;
  }
  .badge {
    display:inline-block; margin-left:0.75rem; vertical-align:middle;
    background:rgba(26,82,118,0.08);
    border:1px solid rgba(45,122,184,0.15);
    border-radius:8px; padding:0.3rem 0.9rem;
    font-size:0.8rem; font-weight:600; color:#1a5276;
    margin-bottom:1.5rem;
  }

  /* ── 탭 네비 (모든 탭 이름이 항상 보임) ── */
  .tab-nav {
    display:flex; gap:0; margin-bottom:1.5rem;
    border-bottom:2px solid rgba(45,122,184,0.2);
  }
  .tab-btn {
    background:transparent; border:none; cursor:pointer;
    padding:0.85rem 1.8rem; font-family:'Inter',sans-serif;
    font-size:0.9rem; font-weight:600; color:#5a7a94;
    border-bottom:3px solid transparent; margin-bottom:-2px;
    transition:color 0.15s, border-color 0.15s, background 0.15s;
  }
  .tab-btn:hover { color:#1a5276; background:rgba(255,255,255,0.5); }
  .tab-btn.active {
    color:#1a5276; border-bottom-color:#2d7ab8;
    background:rgba(255,255,255,0.9);
  }

  .section {
    background:rgba(255,255,255,0.9);
    backdrop-filter:blur(8px);
    border:1px solid rgba(255,255,255,0.6);
    border-radius:14px;
    padding:1.4rem 1.5rem;
    box-shadow:0 4px 14px rgba(13,33,55,0.05);
    margin-bottom:1.5rem;
  }
  .section-title {
    font-size:0.82rem; font-weight:700;
    text-transform:uppercase; letter-spacing:0.1em;
    color:#4a6a82; margin-bottom:1rem;
    padding-bottom:0.5rem;
    border-bottom:2px solid rgba(45,122,184,0.2);
  }
  .row { display:flex; gap:1.5rem; flex-wrap:wrap; }
  .col-2 { flex:1 1 45%; min-width:300px; }
  .col-3 { flex:1 1 30%; min-width:260px; }

  .stat {
    background:rgba(255,255,255,0.88);
    backdrop-filter:blur(8px);
    border:1px solid rgba(255,255,255,0.5);
    border-radius:14px;
    padding:0.9rem 1.1rem;
    box-shadow:0 4px 16px rgba(13,33,55,0.07);
    transition:transform 0.2s, box-shadow 0.2s;
  }
  .stat:hover { transform:translateY(-2px);
    box-shadow:0 8px 28px rgba(13,33,55,0.11); }
  .stat-label {
    font-size:0.7rem; font-weight:600;
    text-transform:uppercase; letter-spacing:0.08em;
    color:#6b8aa0; margin-bottom:0.3rem;
  }
  .stat-val { font-size:1.6rem; font-weight:700; color:#0d2137; line-height:1.1; }
  .stat-val.b { color:#1a5276; }
  .stat-val.r { color:#c0392b; }
  .stat-val.g { color:#1d6f42; }
  .stat-val.o { color:#8b6914; }

  .chart-wrap {
    background:rgba(255,255,255,0.85);
    border-radius:10px;
    padding:0.5rem;
    box-shadow:0 2px 8px rgba(13,33,55,0.06);
    margin-bottom:0.75rem;
  }
  .chart-wrap .js-plotly-plot .plotly .main-svg { border-radius:8px; }

  .hypothesis {
    background:linear-gradient(135deg,
      rgba(26,82,118,0.04) 0%, rgba(45,122,184,0.06) 100%);
    border-left:3px solid #2d7ab8;
    border-radius:0 10px 10px 0;
    padding:0.7rem 1rem;
    margin-bottom:0.5rem;
  }
  .h-num {
    display:inline-flex; align-items:center; justify-content:center;
    width:20px; height:20px; border-radius:50%;
    background:rgba(45,122,184,0.12); color:#2d7ab8;
    font-size:0.7rem; font-weight:700; margin-right:0.5rem; flex-shrink:0;
  }
  .hyp-title {
    font-weight:600; font-size:0.9rem; color:#1a2a3a;
    margin:0 0 0.2rem; padding-top:0.1rem;
  }
  .hyp-desc { font-size:0.82rem; color:#5a7a94; margin:0; }

  .conclusion {
    background:rgba(255,255,255,0.75);
    border-left:4px solid #5a7a94;
    border-radius:0 10px 10px 0;
    padding:1rem;
    margin-bottom:0.7rem;
  }
  .conclusion.strong {
    background:rgba(192,57,43,0.04);
    border-left-color:#c0392b;
  }
  .conc-inner { display:flex; align-items:flex-start; gap:0.6rem; }
  .conc-icon { font-size:1.5rem; line-height:1; flex-shrink:0; margin-top:0.1rem; }
  .conc-title {
    font-weight:700; font-size:0.95rem;
    margin:0 0 0.3rem; padding-top:0.1rem;
  }
  .conc-body {
    font-size:0.86rem; color:#3a5a72;
    line-height:1.65; white-space:normal;
  }

  .banner {
    background:linear-gradient(90deg,
      rgba(26,82,118,0.1) 0%, rgba(45,122,184,0.15) 50%,
      rgba(26,82,118,0.1) 100%);
    border:1px solid rgba(45,122,184,0.2);
    border-radius:12px;
    padding:1rem 1.4rem; text-align:center;
    margin-top:1.5rem;
  }
  .banner b { color:#1a5276; }

  .mini-table-title {
    font-size:0.72rem; font-weight:700;
    text-transform:uppercase; letter-spacing:0.08em;
    margin-bottom:0.4rem;
  }
  .mini-table-title.g { color:#1d6f42; }
  .mini-table-title.r { color:#c0392b; }

  .tbl {
    font-family:'Inter',sans-serif; font-size:0.82rem;
    border-collapse:collapse; width:100%;
  }
  .tbl th {
    background:rgba(45,122,184,0.08);
    padding:0.4rem 0.6rem; text-align:left;
    font-weight:600; color:#4a6a82;
  }
  .tbl td { padding:0.35rem 0.6rem;
    border-bottom:1px solid rgba(45,122,184,0.07);
    color:#1a2a3a; }
  .tbl tr:last-child td { border-bottom:none; }

  hr {
    border:none;
    border-top:1px solid rgba(45,122,184,0.12);
    margin:1.5rem 0;
  }

  .info-text {
    background:rgba(255,255,255,0.7);
    border:1px dashed rgba(45,122,184,0.3);
    border-radius:10px;
    padding:1rem 1.2rem;
    color:#5a7a94; font-size:0.9rem;
    margin-bottom:1.5rem;
  }
</style>
</head>
<body>
<div class="container">

  <h1>🌿 %s 극지식물 생육 분석</h1>
  <p class="subtitle">개체별 생육 차이 &amp; 환경 데이터 인사이트 대시보드</p>
  <span class="badge">🏫 %s · 개체 수 %d개체</span>

  <!-- ── 모든 탭 이름이 항상 보이는 탭 네비 ── -->
  <nav class="tab-nav" aria-label="섹션 이동">
    <button class="tab-btn active" onclick="showTab('tab1')">📋  개요 &amp; 환경 데이터</button>
    <button class="tab-btn" onclick="showTab('tab2')">📈  산점도 &amp; 상관분석</button>
    <button class="tab-btn" onclick="showTab('tab3')">🎯  분석 결론</button>
  </nav>

  <!-- ═══════════════════════════════════════
       탭 1 — 개요 & 환경 데이터  (항상 보임)
       ═══════════════════════════════════════ -->
  <section id="tab1" class="section">
    <div class="section-title">🌡️ 환경 데이터 개요</div>

    <div class="row">
      <div class="col-2">
        <div class="chart-wrap">%s</div>
      </div>
      <div class="col-2">
        <div class="chart-wrap">%s</div>
      </div>
    </div>

    <div class="row" style="margin-top:0.8rem;">
      <div class="col-2">
        <div style="display:flex;gap:0.7rem;flex-wrap:wrap;">
          %s
        </div>
      </div>
    </div>

    <hr style="margin:1.2rem 0;">

    <div class="section-title">🌱 생육 결과 데이터</div>

    <div style="display:flex;gap:0.7rem;flex-wrap:wrap;margin-bottom:0.5rem;">
      %s
    </div>

    <hr style="margin:1.2rem 0;">

    <div class="section-title">🔬 우리의 가설</div>
    %s
  </section>

  <!-- ═══════════════════════════════════════
       탭 2 — 산점도 & 상관분석  (항상 보임)
       ═══════════════════════════════════════ -->
  <section id="tab2" class="section" style="display:none;">
    <div class="section-title">📊 생육 지표 간 관계 — 산점도 &amp; 추세선</div>
    <div class="chart-wrap">%s</div>
    <div class="chart-wrap">%s</div>
    <div class="chart-wrap">%
