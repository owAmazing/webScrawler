import pandas as pd
import matplotlib.pyplot as plt
import os

# 1. 設定桌面路徑與檔案名稱
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
file_name = "cat123.csv" 
file_path = os.path.join(desktop_path, file_name)

# 設定中文字體（解決 Matplotlib 中文亂碼問題）
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] # 微軟正黑體
plt.rcParams['axes.unicode_minus'] = False # 修復負號顯示問題

print(f"📂 正在從桌面讀取 CSV 檔案: {file_path}")

try:
    # 2. 讀取 CSV
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except:
        df = pd.read_csv(file_path, encoding='cp950')
    
    # 3. 自動偵測欄位名稱 (支援 Date/日期 與 Close/收盤指數)
    col_map = {col.strip(): col for col in df.columns}
    date_col = col_map.get('Date') or col_map.get('日期')
    close_col = col_map.get('Close') or col_map.get('收盤指數')
    
    if not date_col or not close_col:
        raise ValueError(f"找不到必要欄位！檔案內現有欄位為: {list(df.columns)}")

    # 4. 資料預處理
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col)

    # 5. 繪圖設定
    plt.figure(figsize=(12, 6), dpi=100)
    
    # 繪製純折線圖 (無圓點)
    plt.plot(df[date_col], df[close_col], 
             color='#1f77b4',      
             linewidth=2.5,        
             label='收盤價')  

    # 6. 圖表裝飾
    plt.title('TAIEX 價格走勢', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('指數點數', fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend()

    # 自動調整日期標籤方向
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout()
    plt.show()
    print("✅ 圖表已成功顯示！")

except Exception as e:
    print(f"❌ 發生錯誤：{e}")