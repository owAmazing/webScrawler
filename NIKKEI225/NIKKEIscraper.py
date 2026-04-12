import pandas as pd
import os

class DCASimulator:
    def __init__(self, file_name="cat123.csv", monthly_investment=10000):
        """
        初始化模擬器
        :param file_name: 放在桌面的檔案名稱
        :param monthly_investment: 每月投入金額
        """
        self.desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.file_path = os.path.join(self.desktop_path, file_name)
        self.monthly_investment = monthly_investment
        self.df = None
        self.results = {}

    def load_data(self):
        """讀取並預處理資料"""
        try:
            # 嘗試不同編碼讀取
            try:
                self.df = pd.read_csv(self.file_path, encoding='utf-8-sig')
            except:
                self.df = pd.read_csv(self.file_path, encoding='cp950')

            # 自動偵測欄位
            col_map = {col.strip(): col for col in self.df.columns}
            self.date_col = col_map.get('Date') or col_map.get('日期')
            self.close_col = col_map.get('Close') or col_map.get('收盤指數')

            if not self.date_col or not self.close_col:
                raise ValueError("找不到 'Date' 或 'Close' 欄位")

            # 轉換日期格式
            self.df[self.date_col] = pd.to_datetime(self.df[self.date_col])
            return True
        except Exception as e:
            print(f"❌ 讀取資料失敗: {e}")
            return False

    def run_simulation(self, start_date='2011-04-01', end_date='2026-04-01'):
        """執行定期定額模擬"""
        if self.df is None:
            if not self.load_data(): return

        # 篩選時間區間並排序
        mask = (self.df[self.date_col] >= start_date) & (self.df[self.date_col] <= end_date)
        df_sim = self.df.loc[mask].sort_values(self.date_col).copy()

        if df_sim.empty:
            print("⚠️ 該時間區間內無資料")
            return

        # 計算每月買入股數 (保留兩位小數)
        df_sim['Bought_Shares'] = (self.monthly_investment / df_sim[self.close_col]).round(2)

        # 計算統計數據
        total_months = len(df_sim)
        total_invested = total_months * self.monthly_investment
        total_shares = df_sim['Bought_Shares'].sum()
        last_close = df_sim[self.close_col].iloc[-1]
        current_value = total_shares * last_close

        # 儲存結果
        self.results = {
            "total_months": total_months,
            "total_invested": total_invested,
            "total_shares": total_shares,
            "current_value": current_value,
            "last_date": df_sim[self.date_col].iloc[-1].strftime('%Y/%m/%d')
        }

    def display_results(self):
        """格式化輸出結果"""
        if not self.results:
            print("❌ 尚未執行模擬或無結果")
            return

        print("-" * 50)
        print(f"📊 Traditional DCA 模擬報告 (2011/04 - 2026/04)")
        print("-" * 50)
        print(f"🔹 15 年間總投資金額: {self.results['total_invested']:,.0f} 元")
        print(f"🔹 15 年間總累積股票: {self.results['total_shares']:,.2f} 股")
        print(f"🔹 目前累積總額 (以 {self.results['last_date']} 收盤價計算): {self.results['current_value']:,.0f} 元")
        print("-" * 50)

# --- 使用範例 ---
if __name__ == "__main__":
    # 建立實例
    dca = DCASimulator(file_name="cat123.csv", monthly_investment=10000)
    
    # 執行模擬
    dca.run_simulation()
    
    # 顯示結果
    dca.display_results()