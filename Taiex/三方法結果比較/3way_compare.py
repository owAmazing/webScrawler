import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 1. 設定路徑
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
file_path = os.path.join(desktop_path, "cat2.csv")

# 設定中文字體與負號顯示
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False

try:
    # 2. 讀取 csv
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except:
        df = pd.read_csv(file_path, encoding='cp950')

    # 3. 準備繪圖數據
    labels = df['Strategy'].tolist()
    final_value = df['Final_Value'].tolist()
    total_invested = df['Total_Invested'].tolist()

    x = np.arange(len(labels))  
    width = 0.35  

    # 4. 開始畫圖
    fig, ax = plt.subplots(figsize=(12, 7), dpi=100)
    
    # 繪製長條圖
    rects1 = ax.bar(x - width/2, final_value, width, label='最終組合價值 (TWD)', color='#1f77b4')
    rects2 = ax.bar(x + width/2, total_invested, width, label='總投入金額 (TWD)', color='#ff7f0e')

    # 5. 圖表裝飾 (這裡修改了 TAIEX 與 台幣單位)
    ax.set_title('TAIEX 指數策略最終績效比較', fontsize=16, pad=20) # 修改標題
    ax.set_ylabel('金額 (TWD / 台幣)', fontsize=12)               # 修改 Y 軸單位
    ax.set_xlabel('投資策略', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    # 加入水平網格線
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)
    
    # 數值標籤函式
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:,.0f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), 
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

    autolabel(rects1)
    autolabel(rects2)

    plt.tight_layout()
    plt.show()
    print("✅ TAIEX 策略對比圖表已生成！")

except Exception as e:
    print(f"❌ 繪圖失敗：{e}")