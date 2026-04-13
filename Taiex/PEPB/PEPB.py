import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import re

def draw_pepb_chart_special_format():
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    file_path = os.path.join(desktop_path, "PEPB.xlsx")
    
    try:
        # 1. 讀取 Excel
        df = pd.read_excel(file_path)
        
        # 2. 處理特殊日期格式
        current_year = None
        ad_dates = []
        
        for index, row in df.iterrows():
            time_val = str(row['time']).strip()
            
            # 提取數字 (例如從 "100年 1月" 提取出 [100, 1])
            nums = re.findall(r'\d+', time_val)
            
            if len(nums) == 2: # 格式如 "100年 1月"
                current_year = int(nums[0]) + 1911
                current_month = int(nums[1])
            elif len(nums) == 1: # 格式如 "2月"
                current_month = int(nums[0])
            else:
                ad_dates.append(None)
                continue
            
            # 組合為西元日期 (預設每月1號)
            if current_year:
                ad_dates.append(pd.to_datetime(f"{current_year}-{current_month:02d}-01"))
            else:
                ad_dates.append(None)
        
        df['ad_time'] = ad_dates
        
        # 3. 數據轉型與清理
        df['PE'] = pd.to_numeric(df['PE'], errors='coerce')
        df['PB'] = pd.to_numeric(df['PB'], errors='coerce')
        df = df.dropna(subset=['ad_time']).sort_values('ad_time')

        # 4. 繪圖
        fig, ax1 = plt.subplots(figsize=(15, 7))

        # PE 折線 (左軸)
        color_pe = '#e31a1c'
        ax1.set_xlabel('Year', fontsize=10)
        ax1.set_ylabel('P/E Ratio', color=color_pe, fontsize=12, fontweight='bold')
        ax1.plot(df['ad_time'], df['PE'], color=color_pe, label='PE', linewidth=1.5, marker='o', markersize=3, alpha=0.8)
        ax1.tick_params(axis='y', labelcolor=color_pe)
        ax1.grid(True, linestyle=':', alpha=0.6)

        # PB 折線 (右軸)
        ax2 = ax1.twinx()
        color_pb = '#1f78b4'
        ax2.set_ylabel('P/B Ratio', color=color_pb, fontsize=12, fontweight='bold')
        ax2.plot(df['ad_time'], df['PB'], color=color_pb, label='PB', linestyle='--', linewidth=1.5, marker='x', markersize=3, alpha=0.8)
        ax2.tick_params(axis='y', labelcolor=color_pb)

        # 標題與格式
        plt.title('TAIEX Historical PE/PB Trend (2011-2026)', fontsize=14, pad=20)
        ax1.xaxis.set_major_locator(mdates.YearLocator()) # 每年顯示一個標籤
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        
        # 圖例
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper left')

        plt.tight_layout()
        
        # 儲存
        output_image = os.path.join(desktop_path, "TAIEX_Analysis_Result.png")
        plt.savefig(output_image, dpi=300)
        print(f"✅ 圖片已成功儲存至桌面！")
        plt.show()

    except Exception as e:
        print(f"💥 錯誤：{e}")

if __name__ == "__main__":
    draw_pepb_chart_special_format()