import requests
import pandas as pd
import time
import os
from datetime import datetime

class TAIEXLongTermSpider:
    def __init__(self):
        self.url = "https://www.twse.com.tw/indicesReport/MI_5MINS_HIST"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        } 

    def fetch_month_data(self, date_str):
        params = {'response': 'json', 'date': date_str}
        try:
            resp = requests.get(self.url, params=params, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('stat') == 'OK':
                    return pd.DataFrame(data['data'], columns=data['fields'])
                else:
                    print(f"\n⚠️ 證交所回應: {data.get('stat')}")
        except Exception as e:
            print(f"\n❌ 網路請求錯誤: {e}")
        return None

    def clean_and_get_first_day(self, df, target_year, target_month):
        if df is None or df.empty:
            return None
            
        try:
            df = df.copy()
            def convert_date(d):
                y, m, d = d.split('/')
                return f"{int(y)+1911}-{m}-{d}"
            
            df['Date_Obj'] = pd.to_datetime(df['日期'].apply(convert_date))
            first_row_date = df['Date_Obj'].iloc[0]
            
            # --- 嚴格年月檢核 ---
            if first_row_date.year != target_year or first_row_date.month != target_month:
                print(f"\n🚨 資料可能有誤！預期 {target_year}/{target_month:02d}，但抓到 {first_row_date.year}/{first_row_date.month:02d}")
                return "CHECK_ERROR" 
            
            df['Date'] = df['Date_Obj'].dt.strftime('%Y-%m-%d')
            df = df.rename(columns={'開盤指數': 'Open', '最高指數': 'High', '最低指數': 'Low', '收盤指數': 'Close'})
            
            for col in ['Open', 'High', 'Low', 'Close']:
                df[col] = df[col].astype(str).str.replace(',', '').astype(float)
            
            return df.iloc[[0]][['Date', 'Open', 'High', 'Low', 'Close']]
        except Exception as e:
            print(f"\n🧹 資料清理異常: {e}")
            return None

# --- 修改後的設定起始值 ---
i = 2011  # 起始年份改為 2011
j = 4     # 起始月份改為 4
end_year = 2026 # 結束年份改為 2026
file_name = f"TAIEX_History_2011_2026.csv"
spider = TAIEXLongTermSpider()

# 取得今天日期，避免抓過頭
today = datetime.now()

print(f"🚀 開始抓取 TAIEX 數據 (從 {i}年{j}月 開始 到 2026年4月)...")

if os.path.exists(file_name):
    os.remove(file_name)

# --- While 迴圈主體 ---
while i <= end_year:
    # 檢查是否超過目前日期 (2026年4月)
    if i == 2026 and j > 4:
        print("\n已抓取至 2026-04，任務結束。")
        break
    
    # 同時也要防止超過「今天」的日期（萬一你提早執行）
    if i == today.year and j > today.month:
        print("\n已超過今日日期，停止抓取。")
        break

    date_query = f"{i}{j:02d}01"
    print(f"📡 嘗試抓取: {i}-{j:02d} ...", end="\r")

    raw_df = spider.fetch_month_data(date_query)
    result_df = spider.clean_and_get_first_day(raw_df, i, j)

    if isinstance(result_df, pd.DataFrame):
        print(f"✅ {i}-{j:02d} 成功 | 第一交易日: {result_df['Date'].values[0]} | 開盤: {result_df['Open'].values[0]}")
        
        header_needed = not os.path.exists(file_name)
        result_df.to_csv(file_name, mode='a', index=False, header=header_needed, encoding='utf-8-sig')
        
        # 推進指標
        if j == 12:
            j = 1
            i += 1
        else:
            j += 1
            
        # 建議：證交所爬蟲延遲設為 3-5 秒比較安全，避免被封鎖 IP
        time.sleep(0.5)
        
    elif result_df == "CHECK_ERROR":
        print(f"🔄 {i}-{j:02d} 年月檢核失敗，10秒後重試...")
        time.sleep(10.0)
    else:
        print(f"🔄 {i}-{j:02d} 抓取失敗 (None)，15秒後重試...")
        time.sleep(15.0)

print(f"\n🏁 任務完成！資料儲存至 {file_name}")