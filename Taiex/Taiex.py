import requests
import pandas as pd
import time
from datetime import datetime

class TAIEXLongTermSpider:
    def __init__(self):
        self.url = "https://www.twse.com.tw/indicesReport/MI_5MINS_HIST"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        } 

    def fetch_month_data(self, date_str):
        """抓取該月整月資料"""
        params = {'response': 'json', 'date': date_str}
        try:
            resp = requests.get(self.url, params=params, headers=self.headers, timeout=10)
            data = resp.json()
            if data.get('stat') == 'OK':
                df = pd.DataFrame(data['data'], columns=data['fields'])
                return df
        except Exception as e:
            print(f"Error fetching {date_str}: {e}")
        return None

    def clean_and_get_first_day(self, df):
        """清理數據並僅保留該月第一個交易日"""
        if df is None or df.empty:
            return None
            
        # 民國轉西元邏輯
        def convert_date(d):
            y, m, d = d.split('/')
            return f"{int(y)+1911}-{m}-{d}"
        
        # 建立 Date 欄位並轉換為日期格式
        df['Date'] = df['日期'].apply(convert_date)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # 欄位重新命名 (配合作業格式)
        df = df.rename(columns={'開盤指數': 'Open', '最高指數': 'High', '最低指數': 'Low', '收盤指數': 'Close'})
        
        # 清除數字中的千分位逗號並轉為浮點數
        cols = ['Open', 'High', 'Low', 'Close']
        for col in cols:
            df[col] = df[col].astype(str).str.replace(',', '').astype(float)
            
        # 重點：只取該月第一筆交易資料
        return df.iloc[[0]][['Date', 'Open', 'High', 'Low', 'Close']]

# --- 執行自動化 Pipeline ---
spider = TAIEXLongTermSpider()
all_monthly_first_days = []

# --- 設定目標區間：2011 到 2025 ---
start_year = 2011
end_year = 2025

print(f"🚀 開始抓取 TAIEX 歷史數據 ({start_year} - {end_year})...")

for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        # 構造查詢日期 (每個月的1號作為 API 觸發點)
        date_query = f"{year}{month:02d}01"
        print(f"📡 處理中: {year}-{month:02d} ...", end="\r")
        
        raw_df = spider.fetch_month_data(date_query)
        first_day_df = spider.clean_and_get_first_day(raw_df)
        
        if first_day_df is not None:
            all_monthly_first_days.append(first_day_df)
            
        # 🛡️ 禮貌延遲：防止 IP 被封鎖 (建議至少 2 秒)
        time.sleep(0.05) 

# 合併與儲存
if all_monthly_first_days:
    final_df = pd.concat(all_monthly_first_days, ignore_index=True)
    file_name = f"TAIEX_{start_year}_{end_year}.csv"
    final_df.to_csv(file_name, index=False, encoding='utf-8-sig')
    print(f"\n✅ 完成！共取得 {len(final_df)} 個月的開盤數據。")
    print(f"💾 儲存成功：{file_name}")
else:
    print("\n❌ 未能抓取數據，請確認網路連線。")