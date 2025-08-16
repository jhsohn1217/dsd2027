import streamlit as st

# 우리가 고른 색깔들
colors = ["#FFFFFF", "#7EB900", "#80B70B", "#F1F3F3", "#FDB803"]

st.title("내 멋진 색깔 팔레트 🎨")

# 색깔 상자 보여주기
cols = st.columns(len(colors))
for i, c in enumerate(colors):
    with cols[i]:
        st.markdown(
            f"""
            <div style="background:{c};border-radius:10px;
                        height:70px;border:1px solid #ccc"></div>
            <p style="text-align:center">{c}</p>
            """,
            unsafe_allow_html=True,
        )
