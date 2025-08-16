import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog

# 한글 폰트 설정 (선택 사항)
try:
    import koreanize_matplotlib
except ImportError:
    print("koreanize_matplotlib가 설치되지 않았습니다. 설치 시 한글이 자연스럽게 표시됩니다.")

def select_file():
    """파일 업로드 창 열기"""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    return file_path

def plot_pareto_chart(file_path):
    """파레토 차트 시각화"""
    try:
        xls = pd.ExcelFile(file_path)
        if '파레토차트' not in xls.sheet_names:
            raise ValueError("'파레토차트' 시트를 찾을 수 없습니다.")

        df = xls.parse('파레토차트')
        if '부서' not in df.columns or '매출' not in df.columns:
            raise ValueError("'부서' 또는 '매출' 열이 존재하지 않습니다.")

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
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"[오류] {e}")

if __name__ == "__main__":
    print("📊 파레토 차트 시각화기 실행 중...")
    file_path = select_file()
    if file_path:
        plot_pareto_chart(file_path)
    else:
        print("파일이 선택되지 않았습니다.")
