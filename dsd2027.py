import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

try:
    import koreanize_matplotlib
except ImportError:
    pass

st.title("📊 부서별 매출 파레토 차트")

uploaded_file = st.file_uploader("엑셀 파일 업로드", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        xls = pd.ExcelFile(uploaded_file)
        if '파레토차트' not in xls.sheet_names:
            st.error("'파레토차트' 시트를 찾을 수 없습니다.")
        else:
            df = xls.parse('파레토차트')
            if '부서' not in df.columns or '매출' not in df.columns:
                st.error("'부서' 또는 '매출' 열이 존재하지 않습니다.")
            else:
                # 정렬 및 누적 계산
                df = df.sort_values(by='매출', ascending=False).reset_index(drop=True)
                df['누적 매출'] = df['매출'].cumsum()
                df['누적 비율(%)'] = 100 * df['누적 매출'] / df['매출'].sum()

                # 파레토 차트 그리기
                fig, ax1 = plt.subplots(figsize=(10, 6))
                ax1.bar(df['부서'], df['매출'], color='skyblue')
                ax1.set_xlabel('부서')
                ax1.set_ylabel('매출', color='blue')
                ax1.tick_params(axis='y', labelcolor='blue')

                # 누적 비율 라인
                ax2 = ax1.twinx()
                ax2.plot(df['부서'], df['누적 비율(%)'], color='red', marker='o')
                ax2.set_ylabel('누적 비율(%)', color='red')
                ax2.tick_params(axis='y', labelcolor='red')
                ax2.set_ylim(0, 110)

                # 80% 기준선
                ax2.axhline(80, color='gray', linestyle='--', linewidth=1)
                ax2.text(len(df)-1, 82, '80% 기준선', color='gray')

                plt.title('부서별 매출 파레토 차트')
                st.pyplot(fig)

    except Exception as e:
        st.error(f"[오류] {e}")
