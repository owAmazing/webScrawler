# NIKKEIstrategy.py
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

class NIKKEIStrategy:
    def __init__(self, price_df, monthly_investment=10000):
        self.df = price_df.copy().sort_index()
        self.monthly_investment = monthly_investment  # 每月投資金額（日元）
        self.results = {}

    def run_all_strategies(self):
        self.standard_dca()
        self.fixed_shares()
        self.value_averaging()
        self.compare_results()
        self.save_summary_csv()
        self.plot_price_trend()
        self.plot_cumulative_investment_vs_portfolio()
        self.plot_final_performance_comparison()

    def standard_dca(self):
        """標準 DCA：每月固定金額"""
        df = self.df.copy()
        df['Investment'] = self.monthly_investment
        df['Shares'] = df['Investment'] / df['Adj Close']
        df['Total_Shares'] = df['Shares'].cumsum()
        df['Total_Invested'] = df['Investment'].cumsum()
        df['Portfolio_Value'] = df['Total_Shares'] * df['Adj Close']
        
        self.results['Standard_DCA'] = self._make_result(df)

    def fixed_shares(self):
        """Fixed Shares：每月固定股數（以平均價格計算）"""
        df = self.df.copy()
        avg_price = df['Adj Close'].mean()
        shares_per_month = self.monthly_investment / avg_price
        
        df['Investment'] = shares_per_month * df['Adj Close']
        df['Shares'] = shares_per_month
        df['Total_Shares'] = df['Shares'].cumsum()
        df['Total_Invested'] = df['Investment'].cumsum()
        df['Portfolio_Value'] = df['Total_Shares'] * df['Adj Close']
        
        self.results['Fixed_Shares'] = self._make_result(df)

    def value_averaging(self):
        """Value Averaging：目標市值線性成長（不賣出）"""
        df = self.df.copy()
        months = np.arange(1, len(df) + 1)
        target_value = months * self.monthly_investment

        df['Target_Value'] = target_value
        df['Investment'] = 0.0
        df['Portfolio_Value'] = 0.0
        total_shares = 0.0
        total_shares_list = []

        for idx in df.index:
            current_price = df.at[idx, 'Adj Close']
            target = df.at[idx, 'Target_Value']
            current_portfolio = total_shares * current_price
            invest = max(target - current_portfolio, 0.0)

            shares_bought = invest / current_price if current_price else 0.0
            total_shares += shares_bought
            total_shares_list.append(total_shares)

            df.at[idx, 'Investment'] = invest
            df.at[idx, 'Portfolio_Value'] = total_shares * current_price

        df['Total_Invested'] = df['Investment'].cumsum()
        df['Total_Shares'] = total_shares_list

        self.results['Value_Averaging'] = self._make_result(df)

    def _make_result(self, df):
        years = (df.index[-1] - df.index[0]).days / 365.25
        final_value = df['Portfolio_Value'].iloc[-1]
        total_invested = df['Total_Invested'].iloc[-1]
        start_value = df['Portfolio_Value'].replace(0, np.nan).ffill().iloc[0]
        if years > 0 and start_value > 0:
            cagr = ((final_value / start_value) ** (1 / years) - 1) * 100
        else:
            cagr = 0.0

        return {
            'final_value': final_value,
            'total_invested': total_invested,
            'cagr': cagr,
            'df': df
        }

    def compare_results(self):
        print("\n" + "="*70)
        print("NIKKEI 225 三種投資策略長期比較")
        print("="*70)
        for name, res in self.results.items():
            print(f"\n{name.replace('_', ' ')}:")
            print(f"  最終組合價值     : {res['final_value']:,.0f} JPY")
            print(f"  總投入金額       : {res['total_invested']:,.0f} JPY")
            print(f"  年化報酬率 (CAGR): {res['cagr']:.2f}%")

    def save_summary_csv(self):
        """彙整基本資料 + 策略結果到 CSV"""
        summary = []
        for name, res in self.results.items():
            summary.append({
                'Strategy': name.replace('_', ' '),
                'Final_Value_JPY': round(res['final_value']),
                'Total_Invested_JPY': round(res['total_invested']),
                'CAGR_%': round(res['cagr'], 2),
                'Data_Start': self.df.index[0].date(),
                'Data_End': self.df.index[-1].date(),
                'Months': len(self.df)
            })
        
        pd.DataFrame(summary).to_csv('NIKKEI225_strategy_summary.csv', index=False)
        print("\n💾 策略比較結果已儲存 → NIKKEI225_strategy_summary.csv")

    def plot_price_trend(self):
        """畫出 NIKKEI 225 價格走勢圖"""
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        plt.figure(figsize=(12, 7))
        plt.plot(self.df.index, self.df['Adj Close'], color='tab:blue')
        plt.title('NIKKEI 225 價格走勢')
        plt.xlabel('日期')
        plt.ylabel('調整後收盤價 (JPY)')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('NIKKEI225_price_trend.png', dpi=300)
        plt.show()
        print('📈 價格走勢圖已儲存 → NIKKEI225_price_trend.png')

    def plot_cumulative_investment_vs_portfolio(self):
        """畫出累積投資金額與投資組合價值對比圖"""
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        plt.figure(figsize=(14, 8))
        for name, res in self.results.items():
            df = res['df']
            plt.plot(df.index, df['Total_Invested'], label=f'{name.replace("_", " ")} - 總投入', linestyle='-')
            plt.plot(df.index, df['Portfolio_Value'], label=f'{name.replace("_", " ")} - 組合價值', linestyle='--')

        plt.title('NIKKEI 225 - 累積投資 vs 投資組合價值')
        plt.xlabel('日期')
        plt.ylabel('金額 (JPY)')
        plt.legend(loc='upper left', fontsize='small')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('NIKKEI225_investment_vs_portfolio.png', dpi=300)
        plt.show()
        print('📊 累積投資 vs 投資組合價值圖已儲存 → NIKKEI225_investment_vs_portfolio.png')

    def plot_final_performance_comparison(self):
        """畫出最終績效比較長條圖"""
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        names = []
        final_values = []
        total_invested = []
        for name, res in self.results.items():
            names.append(name.replace('_', ' '))
            final_values.append(res['final_value'])
            total_invested.append(res['total_invested'])

        x = np.arange(len(names))
        width = 0.35

        fig, ax = plt.subplots(figsize=(12, 7))
        ax.bar(x - width/2, final_values, width, label='最終組合價值')
        ax.bar(x + width/2, total_invested, width, label='總投入金額')

        ax.set_title('NIKKEI 225 策略最終績效比較')
        ax.set_xlabel('策略')
        ax.set_ylabel('JPY')
        ax.set_xticks(x)
        ax.set_xticklabels(names)
        ax.legend()
        ax.grid(True, axis='y', linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.savefig('NIKKEI225_final_performance_comparison.png', dpi=300)
        plt.show()
        print('📊 最終績效比較圖已儲存 → NIKKEI225_final_performance_comparison.png')

    def plot_comparison(self):
        """畫出三種策略走勢圖並儲存"""
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        plt.figure(figsize=(12, 7))
        for name, res in self.results.items():
            df = res['df']
            plt.plot(df.index, df['Portfolio_Value'], label=name.replace('_', ' '))
        
        plt.title('NIKKEI 225 - Standard DCA vs Fixed Shares vs Value Averaging')
        plt.xlabel('日期')
        plt.ylabel('投資組合價值 (JPY)')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('NIKKEI225_strategy_comparison.png', dpi=300)
        plt.show()
        print("📊 比較圖表已儲存 → NIKKEI225_strategy_comparison.png")


# ==================== 主程式 ====================
if __name__ == "__main__":
    csv_file = 'NIKKEI225_price_max.csv'

    if not os.path.exists(csv_file):
        print(f"{csv_file} 不存在，將自動啟動 NIKKEIscraper 抓取最新資料。")
        try:
            from NIKKEIscraper import NIKKEIScraper
            scraper = NIKKEIScraper()
            price_df = scraper.fetch_price_data(interval="1mo")
            if price_df is None:
                raise FileNotFoundError('無法取得價格資料')
            scraper.save_data()
        except Exception as e:
            raise SystemExit(f"無法取得價格資料：{e}")
    else:
        price_df = pd.read_csv(csv_file, index_col='Date', parse_dates=True)

    strategy = NIKKEIStrategy(price_df, monthly_investment=10000)  # 每月投資 10,000 日元，可自行修改
    strategy.run_all_strategies()
    strategy.plot_comparison()