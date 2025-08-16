import plotly.express as px

BRAND = ["#7EB900", "#80B70B", "#FDB803", "#F1F3F3", "#111827"]  # 필요 수만큼
fig = px.bar(
    df, x="category", y="value", color="category",
    color_discrete_sequence=BRAND
)
fig.update_layout(
    plot_bgcolor="#F1F3F3",
    paper_bgcolor="#FFFFFF",
    font_color="#1C1C1C",
)
st.plotly_chart(fig, use_container_width=True)
