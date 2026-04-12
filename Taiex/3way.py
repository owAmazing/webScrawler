import pandas as pd
import os

# --- 基礎類別：處理資料讀取與路徑 ---
class BaseSimulator:
    def __init__(self, file_name="cat123.csv"):
        self.desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.file_path = os.path.join(self.desktop_path, file_name)
        self.df = None
        self.history = []  # 儲存每月明細
        self.results = {}

    def _load_data(self):
        try:
            try:
                self.df = pd.read_csv(self.file_path, encoding='utf-8-sig')
            except:
                self.df = pd.read_csv(self.file_path, encoding='cp950')
            
            col_map = {col.strip(): col for col in self.df.columns}
            self.date_col = col_map.get('Date') or col_map.get('日期')
            self.close_col = col_map.get('Close') or col_map.get('收盤指數')
            
            if not self.date_col or not self.close_col:
                raise ValueError("找不到必要的 'Date' 或 'Close' 欄位")

            self.df[self.date_col] = pd.to_datetime(self.df[self.date_col])
            return True
        except Exception as e:
            print(f"❌ 讀取失敗: {e}")
            return False

    def export_history(self, strategy_name):
        if not self.history:
            return
        output_file = os.path.join(self.desktop_path, f"{strategy_name}_History.csv")
        pd.DataFrame(self.history).to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✅ 明細已匯出至桌面: {strategy_name}_History.csv")

# 1. Traditional DCA (定期定額現金)
class DCASimulator(BaseSimulator):
    def run(self, investment=10000):
        if not self._load_data(): return
        df_sim = self.df[(self.df[self.date_col] >= '2011-04-01') & (self.df[self.date_col] <= '2026-04-01')].sort_values(self.date_col).reset_index()
        
        total_shares = 0
        self.history = []
        for i, row in df_sim.iterrows():
            price = row[self.close_col]
            bought = round(investment / price, 2)
            total_shares += bought
            # 價值計算：買入後的總股數 * 當前股價
            current_value = round(total_shares * price, 2)
            
            self.history.append({
                "月份": i+1, "日期": row[self.date_col].strftime('%Y-%m-%d'),
                "當月股價": price, "投入金額": investment, "買入股數": bought, 
                "累積股數": round(total_shares, 2), "目前持有價值": current_value
            })
        
        self.results = {
            "name": "Traditional DCA",
            "total_invested": len(df_sim) * investment,
            "total_shares": round(total_shares, 2),
            "current_value": self.history[-1]["目前持有價值"]
        }

# 2. Fixed-Share DCA (定期定股)
class FixedShareSimulator(BaseSimulator):
    def run(self, shares=1):
        if not self._load_data(): return
        df_sim = self.df[(self.df[self.date_col] >= '2011-04-01') & (self.df[self.date_col] <= '2026-04-01')].sort_values(self.date_col).reset_index()
        
        total_shares = 0
        total_invested = 0
        self.history = []
        for i, row in df_sim.iterrows():
            price = row[self.close_col]
            cost = round(price * shares, 2)
            total_shares += shares
            total_invested += cost
            current_value = round(total_shares * price, 2)
            
            self.history.append({
                "月份": i+1, "日期": row[self.date_col].strftime('%Y-%m-%d'),
                "當月股價": price, "投入金額": cost, "買入股數": shares, 
                "累積股數": total_shares, "目前持有價值": current_value
            })
        
        self.results = {
            "name": "Fixed-Share DCA",
            "total_invested": round(total_invested, 2),
            "total_shares": total_shares,
            "current_value": self.history[-1]["目前持有價值"]
        }

# 3. Value Averaging (價值平均法)
class ValueAveragingSimulator(BaseSimulator):
    def run(self, value_increase=10000):
        if not self._load_data(): return
        df_sim = self.df[(self.df[self.date_col] >= '2011-04-01') & (self.df[self.date_col] <= '2026-04-01')].sort_values(self.date_col).reset_index()
        
        total_shares = 0
        total_invested = 0
        self.history = []
        for i, row in df_sim.iterrows():
            month_idx = i + 1
            price = row[self.close_col]
            target_v = month_idx * value_increase
            
            # 買入前的持有價值
            pre_buy_value = total_shares * price
            needed = target_v - pre_buy_value
            
            invest = max(0, needed)
            bought = round(invest / price, 2)
            total_shares += bought
            total_invested += invest
            # 買入後的實際持有價值
            actual_current_value = round(total_shares * price, 2)
            
            self.history.append({
                "月份": month_idx, "日期": row[self.date_col].strftime('%Y-%m-%d'), "當月股價": price,
                "預期達到價值": target_v, "投入金額": round(invest, 2), "買入股數": bought, 
                "累積股數": round(total_shares, 2), "目前持有價值": actual_current_value
            })
        
        self.results = {
            "name": "Value Averaging",
            "total_invested": round(total_invested, 2),
            "total_shares": round(total_shares, 2),
            "current_value": self.history[-1]["目前持有價值"]
        }

# --- 執行整合測試 ---
if __name__ == "__main__":
    simulators = [
        DCASimulator("cat123.csv"),
        FixedShareSimulator("cat123.csv"),
        ValueAveragingSimulator("cat123.csv")
    ]
    
    for sim in simulators:
        if isinstance(sim, DCASimulator): sim.run(10000)
        elif isinstance(sim, FixedShareSimulator): sim.run(1)
        elif isinstance(sim, ValueAveragingSimulator): sim.run(10000)
        
        res = sim.results
        print("\n" + "="*50)
        print(f"📊 策略名稱: {res['name']}")
        print("-" * 50)
        print(f"🔹 15年總投資金額: {res['total_invested']:,.2f} 元")
        print(f"🔹 15年總累積股數: {res['total_shares']:,.2f} 股")
        print(f"🔹 目前累積總市值: {res['current_value']:,.0f} 元")
        
        sim.export_history(res['name'].replace(" ", "_"))

    print("\n" + "="*50)
    print("✨ 所有模擬完成，請到桌面查看對帳單檔案！")