import pandas as pd
import matplotlib.pyplot as plt
import os

# --- 設定路徑與字體 ---
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False

def plot_investment_trends_final():
    # 檔案名稱清單
    files = {
        "Standard DCA": "Traditional_DCA_History.csv",
        "Fixed Shares": "Fixed-Share_DCA_History.csv",
        "Value Averaging": "Value_Averaging_History.csv"
    }
    
    # 顏色配置：深色用於實線(投入)，淺色用於虛線(價值)
    # 紅色系、藍色系、綠色系
    color_map = {
        "Standard DCA": {"dark": "#8B0000", "light": "#FF6B6B"},    # 深紅 vs 亮紅
        "Fixed Shares": {"dark": "#00008B", "light": "#4D94FF"},    # 深藍 vs 天藍
        "Value Averaging": {"dark": "#006400", "light": "#90EE90"}  # 深綠 vs 嫩綠
    }

    plt.figure(figsize=(15, 9), dpi=100)

    for label, file_name in files.items():
        file_path = os.path.join(desktop_path, file_name)
        
        if not os.path.exists(file_path):
            print(f"⚠️ 找不到檔案: {file_name}")
            continue
        
        # 讀取數據
        df = pd.read_csv(file_path)
        df['日期'] = pd.to_datetime(df['日期'])
        df['累計投入'] = df['投入金額'].cumsum()
        
        # 取得對應顏色
        c = color_map[label]
        
        # 繪製總投入 (深色實線)
        plt.plot(df['日期'], df['累計投入'], 
                 label=f"{label} - 總投入 (深)", 
                 color=c['dark'], linestyle='-', linewidth=2.0)
        
        # 繪製組合價值 (淺色虛線)
        plt.plot(df['日期'], df['目前持有價值'], 
                 label=f"{label} - 組合價值 (淺)", 
                 color=c['light'], linestyle='--', linewidth=1.5)

    # 圖表裝飾
    plt.title('NIKKEI 225 投資績效趨勢：累積投入 vs 組合價值', fontsize=18, pad=20)
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('金額 (JPY)', fontsize=12)
    
    # 格線與圖例
    plt.grid(True, which='both', linestyle=':', alpha=0.4)
    # 將圖例放在外面避免擋到線條
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=10, frameon=True)
    
    plt.tight_layout()
    
    # 儲存與顯示
    save_path = os.path.join(desktop_path, "Investment_Trend_RGB_Contrast.png")
    plt.savefig(save_path, bbox_inches='tight')
    plt.show()
    print(f"✅ 最終配色圖表已儲存至桌面: Investment_Trend_RGB_Contrast.png")

if __name__ == "__main__":
    plot_investment_trends_final()