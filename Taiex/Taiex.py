import requests
import pandas as pd
import time
from datetime import datetime

class TAIEXLongTermSpider:
    def __init__(self):
        self.url = "https://www.twse.com.tw/indicesReport/MI_5MINS_HIST"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            # 偽裝成真人瀏覽器
        } 

    def fetch_month_data(self, date_str):
        """抓取該月整月資料"""
        params = {'response': 'json', 'date': date_str} # 請求回傳 json 格式
        try:
            resp = requests.get(self.url, params=params, headers=self.headers, timeout=10)
            data = resp.json()
            if data.get('stat') == 'OK':
                df = pd.DataFrame(data['data'], columns=data['fields']) # 將回傳格式整理成表格
                return df
        except Exception as e:
            print(f"Error fetching {date_str}: {e}")
        return None

    def clean_and_get_first_day(self, df):
        """清理數據並僅保留該月第一個交易日"""
        if df is None or df.empty:
            return None
            
        # 民國轉西元
        def convert_date(d):
            y, m, d = d.split('/')
            return f"{int(y)+1911}-{m}-{d}"
        
        df['Date'] = df['日期'].apply(convert_date)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # 重新命名與格式化
        df = df.rename(columns={'開盤指數': 'Open', '最高指數': 'High', '最低指數': 'Low', '收盤指數': 'Close'})
        cols = ['Open', 'High', 'Low', 'Close']
        for col in cols:
            df[col] = df[col].str.replace(',', '').astype(float)
            
        # 重點：取該月第一筆資料 (即每月第一個交易日)
        return df.iloc[[0]][['Date', 'Open', 'High', 'Low', 'Close']]

# --- 執行自動化 Pipeline ---
spider = TAIEXLongTermSpider()
all_monthly_first_days = []

# --- 關鍵修改處：調整時間範圍 ---
start_year = 2011
end_year = 2015

print(f"🚀 開始抓取 TAIEX 歷史數據 ({start_year} - {end_year})...")

for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        # 因為 end_year 設定為 2015，迴圈會跑到 2015/12，不需要額外的 break 條件
        
        date_query = f"{year}{month:02d}01"
        print(f"📡 正在處理: {year}-{month:02d} ...", end="\r")
        
        raw_df = spider.fetch_month_data(date_query)
        first_day_df = spider.clean_and_get_first_day(raw_df)
        
        if first_day_df is not None:
            all_monthly_first_days.append(first_day_df)
            
        # 建議將 sleep 稍微調高到 2 秒左右，避免被證交所暫時鎖 IP
        time.sleep(2.0) 

# 合併數據
if all_monthly_first_days:
    final_df = pd.concat(all_monthly_first_days, ignore_index=True)
    # 儲存 CSV
    file_name = f"TAIEX_{start_year}_{end_year}_Monthly.csv"
    final_df.to_csv(file_name, index=False, encoding='utf-8-sig')
    print(f"\n✅ 抓取完成！共取得 {len(final_df)} 個月的數據。")
    print(f"💾 檔案已儲存為: {file_name}")
    print(final_df.head())
else:
    print("\n❌ 未抓取到任何數據，請檢查網路或 API 狀態。")