import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# ===== 브랜드 팔레트 =====
WHITE   = "#FFFFFF"   # 하얀색(배경)
GREEN1  = "#7EB900"   # 연두색1(주색)
GREEN2  = "#80B70B"   # 연두색2(보조색)
GRAYBG  = "#F1F3F3"   # 회색빛 흰색(보조 배경)
AMBER   = "#FDB803"   # 노란색(강조)
TEXT    = "#1C1C1C"   # 텍스트(가독성 좋은 짙은 회색)

# Plotly 전역 스타일(배경/폰트/색상 시퀀스)
pio.templates["brand"] = pio.templates["plotly_white"]
pio.templates["brand"]["layout"].update(
    paper_bgcolor=WHITE,
    plot_bgcolor=GRAYBG,
    font_color=TEXT,
    colorway=[GREEN1, GREEN2, AMBER],  # 기본 시리즈 색
    margin=dict(l=20, r=20, t=10, b=20),
)
px.defaults.template = "brand"

st.set_page_config(page_title="월별 매출 대시보드", layout="wide")
st.markdown(
    f"""
    <style>
    /* 배경/표 스타일 보완 */
    .stApp {{ background: {WHITE}; color: {TEXT}; }}
    .stDataFrame tbody tr td {{ color: {TEXT}; }}
    .stDataFrame thead tr th {{ color: {TEXT}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 월별 매출 대시보드 (Streamlit)")
st.caption("CSV 업로드 후 4가지 시각화가 자동 생성됩니다. 컬럼: 월(YYYY-MM), 매출액, 전년동월, 증감률(%). 미입력 시 증감률은 전년동월로 자동 계산합니다.")

SAMPLE_CSV = (
    "월,매출액,전년동월,증감률\n"
    "2024-01,12000000,10500000,14.3\n"
    "2024-02,13500000,11200000,20.5\n"
    "2024-03,11000000,12800000,-14.1\n"
    "2024-04,18000000,15200000,18.4\n"
    "2024-05,21000000,18500000,13.5\n"
    "2024-06,22000000,19000000,15.8\n"
    "2024-07,25000000,20500000,22.0\n"
    "2024-08,28000000,24500000,14.3\n"
    "2024-09,24000000,21000000,14.3\n"
    "2024-10,23000000,20000000,15.0\n"
    "2024-11,19500000,17500000,11.4\n"
    "2024-12,17000000,16500000,3.0\n"
)

@st.cache_data
def read_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    return df

@st.cache_data
def parse_sample(sample_text: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(sample_text))

@st.cache_data
def enrich_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # 표준화된 컬럼명 가정: 월, 매출액, 전년동월, 증감률
    df["월"] = df["월"].astype(str).str.strip()
    # 날짜 정렬용 컬럼
    df["_date"] = pd.to_datetime(df["월"], format="%Y-%m", errors="coerce")
    df = df.sort_values("_date").reset_index(drop=True)
    # 숫자 캐스팅
    for c in ["매출액", "전년동월"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "증감률" in df.columns:
        df["증감률"] = pd.to_numeric(df.get("증감률"), errors="coerce")
    else:
        df["증감률"] = np.nan
    # 증감률 자동 계산
    missing_mask = df["증감률"].isna()
    df.loc[missing_mask & df["전년동월"].ne(0), "증감률"] = (
        (df.loc[missing_mask, "매출액"] - df.loc[missing_mask, "전년동월"]) / df.loc[missing_mask, "전년동월"] * 100
    )
    df["증감률"] = df["증감률"].fillna(0)
    # 분기 계산
    df["분기"] = df["_date"].dt.quarter
    return df

# Sidebar: 파일 업로드 / 샘플 버튼 / KPI 목표
with st.sidebar:
    st.header("⚙️ 설정")
    uploaded = st.file_uploader("CSV 업로드", type=["csv"], accept_multiple_files=False)
    use_sample = st.checkbox("샘플 데이터 불러오기", value=True if uploaded is None else False)
    target = st.number_input("KPI 목표 매출 (원)", min_value=0, value=20_000_000, step=100_000)

# Load data
if uploaded is not None:
    df_raw = read_csv(uploaded)
elif use_sample:
    df_raw = parse_sample(SAMPLE_CSV)
else:
    st.info("좌측에서 CSV를 업로드하거나 '샘플 데이터 불러오기'를 선택하세요.")
    st.stop()

# Enrich
try:
    df = enrich_df(df_raw)
except Exception as e:
    st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
    st.stop()

# KPI Cards (색상 이모지로 톤 통일)
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_sales = int(df["매출액"].sum())
    st.metric("총합 매출", f"{total_sales:,.0f}원")
with col2:
    avg_yoy = float(df["증감률"].mean())
    st.metric("평균 증감률", f"{avg_yoy:.1f}%")
with col3:
    max_idx = df["매출액"].idxmax()
    st.metric("최고 매출 (월)", f"{df.loc[max_idx,'월']} · {df.loc[max_idx,'매출액']:,.0f}원")
with col4:
    min_idx = df["매출액"].idxmin()
    st.metric("최저 매출 (월)", f"{df.loc[min_idx,'월']} · {df.loc[min_idx,'매출액']:,.0f}원")

st.divider()

# 1) 월별 매출 추이 (이중선)
with st.container():
    st.subheader("1) 월별 매출 추이 (매출액 vs 전년동월)")
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=df["월"], y=df["매출액"],
        mode="lines+markers", name="매출액",
        line=dict(color=GREEN1, width=3), marker=dict(color=GREEN1, size=8)
    ))
    fig_trend.add_trace(go.Scatter(
        x=df["월"], y=df["전년동월"],
        mode="lines+markers", name="전년동월",
        line=dict(color=GREEN2, dash="dash", width=2), marker=dict(color=GREEN2, size=7)
    ))
    # 마커(최고/최저)
    fig_trend.add_trace(go.Scatter(
        x=[df.loc[max_idx, "월"]], y=[df.loc[max_idx, "매출액"]],
        mode="markers+text", name="최고",
        marker=dict(color=AMBER, size=12, symbol="star"),
        text=["최고"], textposition="top center"
    ))
    fig_trend.add_trace(go.Scatter(
        x=[df.loc[min_idx, "월"]], y=[df.loc[min_idx, "매출액"]],
        mode="markers+text", name="최저",
        marker=dict(color=AMBER, size=10, symbol="triangle-down"),
        text=["최저"], textposition="bottom center"
    ))
    fig_trend.update_layout(yaxis_title="매출액 (원)", xaxis_title="월")
    st.plotly_chart(fig_trend, use_container_width=True)

# 2) 전년 대비 증감률 (막대)
with st.container():
    st.subheader("2) 전년 대비 증감률")
    # 양수는 연두(GREEN1), 음수는 노랑(AMBER)로 '주의' 톤 표시
    bar_colors = [GREEN1 if v >= 0 else AMBER for v in df["증감률"]]
    fig_yoy = go.Figure(go.Bar(
        x=df["월"], y=df["증감률"], marker_color=bar_colors, name="증감률",
        marker_line=dict(width=0.5, color=WHITE)
    ))
    fig_yoy.update_layout(yaxis_title="증감률 (%)", xaxis_title="월")
    st.plotly_chart(fig_yoy, use_container_width=True)

# 3) 분기별 매출 분포 (Boxplot)
with st.container():
    st.subheader("3) 분기별 매출 분포 (Boxplot)")
    # 박스/아웃라이어 색 맞춤
    fig_box = px.box(df, x="분기", y="매출액", points="all", color_discrete_sequence=[GREEN2])
    fig_box.update_traces(marker=dict(color=AMBER, line=dict(color=WHITE, width=0.5)))
    fig_box.update_layout(yaxis_title="매출액 (원)", xaxis_title="분기")
    st.plotly_chart(fig_box, use_container_width=True)

# 4) 월별 KPI 달성률 (라인 + 목표선)
with st.container():
    st.subheader("4) 월별 KPI 달성률 (목표선 100%)")
    rate = (df["매출액"] / (target if target else 1)) * 100.0
    fig_kpi = go.Figure()
    fig_kpi.add_trace(go.Scatter(
        x=df["월"], y=rate, mode="lines+markers", name="달성률",
        line=dict(color=GREEN1, width=3), marker=dict(color=GREEN1, size=8)
    ))
    fig_kpi.add_hline(
        y=100, line_dash="dash", line_color=AMBER,
        annotation_text="목표 100%", annotation_position="top left",
        annotation=dict(font=dict(color=TEXT, size=12), bgcolor=WHITE)
    )
    fig_kpi.update_layout(yaxis_title="달성률 (%)", xaxis_title="월")
    st.plotly_chart(fig_kpi, use_container_width=True)

st.divider()
st.subheader("데이터 미리보기")
st.dataframe(
    df.drop(columns=["_date"]),
    use_container_width=True,
)

st.caption("Tip: 좌측 사이드바에서 KPI 목표를 바꾸면 달성률 차트가 즉시 반영됩니다. 업로드 파일은 동일 스키마를 유지해주세요.")
