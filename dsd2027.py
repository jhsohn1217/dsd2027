import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# ===== 브랜드 팔레트 & 공통 스타일 =====
WHITE   = "#FFFFFF"   # 하얀색
GREEN1  = "#7EB900"   # 연두색1(주색)
GREEN2  = "#80B70B"   # 연두색2(보조)
GRAYBG  = "#F1F3F3"   # 회색빛 흰색(보조 배경)
AMBER   = "#FDB803"   # 노란색(강조)
TEXT    = "#1C1C1C"   # 텍스트

# Plotly 전역 템플릿 정의
pio.templates["brand"] = pio.templates["plotly_white"]
pio.templates["brand"]["layout"].update(
    paper_bgcolor=WHITE,
    plot_bgcolor=GRAYBG,
    font_color=TEXT,
    colorway=[GREEN1, GREEN2, AMBER],  # 기본 시리즈 팔레트
    margin=dict(l=20, r=20, t=10, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
px.defaults.template = "brand"

# ===== 페이지/헤더 =====
st.set_page_config(page_title="월별 매출 대시보드", layout="wide")
st.title("📊 월별 매출 대시보드 (Streamlit)")
st.caption("CSV 업로드 후 4가지 시각화가 자동 생성됩니다. 컬럼: 월(YYYY-MM), 매출액, 전년동월, 증감률(%). 미입력 시 증감률은 전년동월로 자동 계산합니다.")

# ===== 샘플 CSV =====
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

# ===== 유틸 =====
def fmt_won(x: float) -> str:
    try:
        return f"{int(x):,}원"
    except Exception:
        return "-"

def read_csv_safely(file) -> pd.DataFrame:
    """인코딩 추정: utf-8 → utf-8-sig → cp949 순서로 시도"""
    for enc in ("utf-8", "utf-8-sig", "cp949"):
        try:
            file.seek(0)
            return pd.read_csv(file, encoding=enc)
        except Exception:
            continue
    file.seek(0)
    return pd.read_csv(file)  # 마지막 fallback

@st.cache_data(show_spinner=False)
def parse_sample(sample_text: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(sample_text))

@st.cache_data(show_spinner=False)
def enrich_df(df: pd.DataFrame) -> pd.DataFrame:
    need_cols = {"월", "매출액", "전년동월"}
    if not need_cols.issubset(df.columns):
        missing = ", ".join(sorted(list(need_cols - set(df.columns))))
        raise ValueError(f"필수 컬럼 누락: {missing}")

    df = df.copy()
    df["월"] = df["월"].astype(str).str.strip()
    df["_date"] = pd.to_datetime(df["월"], format="%Y-%m", errors="coerce")
    if df["_date"].isna().any():
        bad_rows = df.loc[df["_date"].isna(), "월"].unique().tolist()
        raise ValueError(f"월 형식 오류(YYYY-MM): {bad_rows}")

    df = df.sort_values("_date").reset_index(drop=True)

    for c in ["매출액", "전년동월"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "증감률" in df.columns:
        df["증감률"] = pd.to_numeric(df["증감률"], errors="coerce")
    else:
        df["증감률"] = np.nan

    # 증감률 자동 계산
    missing_mask = df["증감률"].isna()
    denom = df.loc[missing_mask, "전년동월"].replace(0, np.nan)
    df.loc[missing_mask & denom.notna(), "증감률"] = (
        (df.loc[missing_mask, "매출액"] - df.loc[missing_mask, "전년동월"])
        / df.loc[missing_mask, "전년동월"] * 100
    )
    df["증감률"] = df["증감률"].fillna(0.0)

    # 분기
    df["분기"] = df["_date"].dt.quarter
    return df

# ===== 사이드바 =====
with st.sidebar:
    st.header("⚙️ 설정")
    uploaded = st.file_uploader("CSV 업로드", type=["csv"], accept_multiple_files=False)
    use_sample = st.checkbox("샘플 데이터 불러오기", value=(uploaded is None))
    target = st.number_input("KPI 목표 매출 (원)", min_value=0, value=20_000_000, step=100_000)
    accent_choice = st.radio("그래프 강조색", ["연두(GREEN1)", "노랑(AMBER)"], horizontal=True)
    show_ma = st.checkbox("이동평균(3개월) 표시", value=True)
    ma_window = st.slider("이동평균 기간(개월)", 2, 6, 3, disabled=not show_ma)

    st.download_button(
        "샘플 CSV 다운로드", data=SAMPLE_CSV.encode("utf-8-sig"),
        file_name="sample_sales.csv", mime="text/csv"
    )

ACCENT = GREEN1 if "GREEN1" in accent_choice else AMBER

# ===== 데이터 로딩 =====
if uploaded is not None:
    try:
        df_raw = read_csv_safely(uploaded)
    except Exception as e:
        st.error(f"CSV 읽기 오류: {e}")
        st.stop()
elif use_sample:
    df_raw = parse_sample(SAMPLE_CSV)
else:
    st.info("좌측에서 CSV를 업로드하거나 '샘플 데이터 불러오기'를 선택하세요.")
    st.stop()

# ===== 전처리 =====
try:
    df = enrich_df(df_raw)
except Exception as e:
    st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
    st.stop()

# ===== KPI =====
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_sales = float(df["매출액"].sum())
    st.metric("총합 매출", fmt_won(total_sales))
with col2:
    avg_yoy = float(df["증감률"].mean())
    st.metric("평균 증감률", f"{avg_yoy:.1f}%")
with col3:
    max_idx = int(df["매출액"].idxmax())
    st.metric("최고 매출 (월)", f"{df.loc[max_idx,'월']} · {fmt_won(df.loc[max_idx,'매출액'])}")
with col4:
    min_idx = int(df["매출액"].idxmin())
    st.metric("최저 매출 (월)", f"{df.loc[min_idx,'월']} · {fmt_won(df.loc[min_idx,'매출액'])}")

st.divider()

# ===== 탭 구성 =====
tab1, tab2, tab3, tab4 = st.tabs([
    "① 월별 매출 추이", "② 전년 대비 증감률", "③ 분기별 매출 분포", "④ KPI 달성률"
])

# ① 월별 매출 추이 (이중선 + (선택)이동평균)
with tab1:
    st.subheader("월별 매출 추이 (매출액 vs 전년동월)")
    fig_trend = go.Figure()

    fig_trend.add_trace(go.Scatter(
        x=df["월"], y=df["매출액"],
        mode="lines+markers", name="매출액",
        line=dict(color=GREEN1, width=3), marker=dict(color=GREEN1, size=8),
        hovertemplate="월=%{x}<br>매출액="+ "%{y:,.0f}원" +"<extra></extra>"
    ))
    fig_trend.add_trace(go.Scatter(
        x=df["월"], y=df["전년동월"],
        mode="lines+markers", name="전년동월",
        line=dict(color=GREEN2, dash="dash", width=2), marker=dict(color=GREEN2, size=7),
        hovertemplate="월=%{x}<br>전년동월="+ "%{y:,.0f}원" +"<extra></extra>"
    ))

    if show_ma:
        ma = df["매출액"].rolling(ma_window, min_periods=1).mean()
        fig_trend.add_trace(go.Scatter(
            x=df["월"], y=ma, mode="lines", name=f"이동평균({ma_window}개월)",
            line=dict(color=AMBER, width=2, dash="dot"),
            hovertemplate="월=%{x}<br>이동평균="+ "%{y:,.0f}원" +"<extra></extra>"
        ))

    # 최고/최저 마커
    fig_trend.add_trace(go.Scatter(
        x=[df.loc[max_idx, "월"]], y=[df.loc[max_idx, "매출액"]],
        mode="markers+text", name="최고",
        marker=dict(color=AMBER, size=12, symbol="star"),
        text=["최고"], textposition="top center",
        hoverinfo="skip"
    ))
    fig_trend.add_trace(go.Scatter(
        x=[df.loc[min_idx, "월"]], y=[df.loc[min_idx, "매출액"]],
        mode="markers+text", name="최저",
        marker=dict(color=AMBER, size=10, symbol="triangle-down"),
        text=["최저"], textposition="bottom center",
        hoverinfo="skip"
    ))

    fig_trend.update_layout(yaxis_title="매출액 (원)", xaxis_title="월")
    st.plotly_chart(fig_trend, use_container_width=True)

# ② 전년 대비 증감률 (막대)
with tab2:
    st.subheader("전년 대비 증감률")
    bar_colors = [GREEN1 if v >= 0 else AMBER for v in df["증감률"]]
    fig_yoy = go.Figure(go.Bar(
        x=df["월"], y=df["증감률"], marker_color=bar_colors, name="증감률",
        marker_line=dict(width=0.5, color=WHITE),
        hovertemplate="월=%{x}<br>증감률=%{y:.1f}%<extra></extra>"
    ))
    fig_yoy.add_hline(y=0, line_width=1, line_color=TEXT, opacity=0.3)
    fig_yoy.update_layout(yaxis_title="증감률 (%)", xaxis_title="월")
    st.plotly_chart(fig_yoy, use_container_width=True)

# ③ 분기별 매출 분포 (Boxplot)
with tab3:
    st.subheader("분기별 매출 분포 (Boxplot)")
    fig_box = px.box(df, x="분기", y="매출액", points="all", color_discrete_sequence=[GREEN2])
    fig_box.update_traces(
        marker=dict(color=AMBER, line=dict(color=WHITE, width=0.5)),
        hovertemplate="분기=%{x}<br>매출액="+ "%{y:,.0f}원" +"<extra></extra>"
    )
    fig_box.update_layout(yaxis_title="매출액 (원)", xaxis_title="분기")
    st.plotly_chart(fig_box, use_container_width=True)

# ④ KPI 달성률 (라인 + 목표선)
with tab4:
    st.subheader("월별 KPI 달성률 (목표선 100%)")
    denom = target if target else 1
    rate = (df["매출액"] / denom) * 100.0

    fig_kpi = go.Figure()
    fig_kpi.add_trace(go.Scatter(
        x=df["월"], y=rate, mode="lines+markers", name="달성률",
        line=dict(color=ACCENT, width=3), marker=dict(color=ACCENT, size=8),
        hovertemplate="월=%{x}<br>달성률=%{y:.1f}%<extra></extra>"
    ))
    fig_kpi.add_hline(
        y=100, line_dash="dash", line_color=AMBER,
        annotation_text="목표 100%", annotation_position="top left",
        annotation=dict(font=dict(color=TEXT, size=12), bgcolor=WHITE)
    )
    fig_kpi.update_layout(yaxis_title="달성률 (%)", xaxis_title="월")
    st.plotly_chart(fig_kpi, use_container_width=True)

# ===== 데이터 미리보기 & 다운로드 =====
st.divider()
st.subheader("데이터 미리보기")
st.dataframe(df.drop(columns=["_date"]), use_container_width=True)

csv_bytes = df.drop(columns=["_date"]).to_csv(index=False).encode("utf-8-sig")
st.download_button("가공 데이터 다운로드 (CSV)", data=csv_bytes, file_name="sales_enriched.csv", mime="text/csv")

st.caption("Tip: 좌측 사이드바에서 KPI 목표/강조색/이동평균을 조정해 보세요. 파일은 월(YYYY-MM), 매출액, 전년동월, (선택)증감률 컬럼을 포함해야 합니다.")
