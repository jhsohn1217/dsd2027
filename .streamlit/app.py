import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="팔레트 데모", page_icon="🎨")

# 1) 우리가 쓸 색연필(팔레트)
palette = ["#7EB900", "#80B70B", "#FDB803", "#F1F3F3", "#FFFFFF"]

# 2) 보여줄 데이터 (막대그래프 예시)
df = pd.DataFrame({
    "이름": ["A", "B", "C", "D", "E"],
    "점수": [3, 7, 4, 6, 5]
})

# 3) Plotly에게 “이 색들로 칠해!”라고 알려주기
fig = px.bar(
    df, x="이름", y="점수", color="이름",
    color_discrete_sequence=palette   # ← 여기 한 줄이 핵심!
)

# 4) 그래프 모양(배경/글자 등) 살짝 정리
fig.update_layout(
    title="우리 팔레트로 그린 막대그래프",
    plot_bgcolor="#F1F3F3",  # 그래프 안 배경
    paper_bgcolor="#FFFFFF", # 그래프 바깥 배경(종이)
    font_color="#1C1C1C"
)

# 5) 스트림릿에 보여주기
st.title("Plotly + 우리 팔레트 🎨")
st.plotly_chart(fig, use_container_width=True)
