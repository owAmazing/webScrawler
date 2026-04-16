# NIKKEIscraper.py
import requests
import pandas as pd
import time
import yfinance as yf
from datetime import datetime, timedelta

class NIKKEIScraper:
    def __init__(self):
        self.ticker = '^N225'
        self.etf_ticker = '1321.T'
        self.market_name = 'NIKKEI225'
        self.price_data = None
        self.valuation_data = None
        self.valuation_history = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
        print("NIKKEI 225 Scraper 初始化完成")

    def fetch_price_data(self, interval="1mo", years=15):
        """抓取 NIKKEI 225 最近 years 年的歷史價格資料"""
        end_ts = int(time.time())
        start_ts = int((datetime.now() - timedelta(days=365.25 * years)).timestamp())
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self.ticker}?period1={start_ts}&period2={end_ts}&interval={interval}"
        
        try:
            resp = requests.get(url, headers=self.headers, timeout=20)
            if resp.status_code == 200:
                json_data = resp.json()['chart']['result'][0]
                
                df = pd.DataFrame({
                    'Date': pd.to_datetime(json_data['timestamp'], unit='s'),
                    'Open': json_data['indicators']['quote'][0]['open'],
                    'High': json_data['indicators']['quote'][0]['high'],
                    'Low': json_data['indicators']['quote'][0]['low'],
                    'Close': json_data['indicators']['quote'][0]['close'],
                    'Volume': json_data['indicators']['quote'][0]['volume'],
                    'Adj Close': json_data['indicators']['adjclose'][0]['adjclose']
                }).set_index('Date')
                
                df = df.dropna(how='all')
                self.price_data = df
                
                print(f"✅ 近 {years} 年價格資料抓取成功 | 總筆數: {len(df)} | 最早: {df.index[0].date()} | 最新: {df.index[-1].date()}")
                return df
            else:
                print(f"❌ 價格請求失敗: {resp.status_code}")
        except Exception as e:
            print(f"❌ 價格抓取錯誤: {e}")
        return None

    def fetch_valuation_data(self):
        """抓取估值指標：使用 NEXT FUNDS Nikkei 225 ETF 1321.T 的 Yahoo Finance 資料"""
        val_data = {
            'Market': 'Next Funds Nikkei 225 ETF',
            'Ticker': self.etf_ticker,
            'As_Of_Date': datetime.now().strftime('%Y-%m-%d'),
            'Trailing_PE_Ratio': 'N/A',
            'Dividend_Yield': 'N/A',
        }

        try:
            etf_val = self._fetch_etf_valuation()
            if etf_val:
                for key, value in etf_val.items():
                    if value is not None:
                        val_data[key] = value
        except Exception as e:
            print(f"ETF 估值抓取失敗: {e}")

        self.valuation_data = val_data
        print("✅ 估值資料抓取完成")
        print(f"   Trailing PE Ratio: {val_data['Trailing_PE_Ratio']} | Dividend Yield: {val_data['Dividend_Yield']}")
        return val_data

    def _fetch_etf_valuation(self):
        ticker = yf.Ticker(self.etf_ticker)
        info = ticker.info or {}

        pe = info.get('trailingPE') or info.get('forwardPE')
        div = info.get('trailingAnnualDividendYield') or info.get('dividendYield')

        return {
            'Trailing_PE_Ratio': self._format_numeric(pe),
            'Dividend_Yield': self._format_percent(div),
        }

    def _format_numeric(self, value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return f"{value:.2f}"
        return str(value)

    def _format_percent(self, value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return f"{value * 100:.2f}%"
        return str(value)

    def fetch_valuation_history(self, years=15):
        """計算 ETF 的歷史 trailing dividend yield（15 年月度）。

        注意：歷史 P/E 比率無法從僅有的高/低/調整後收盤價資料推算，
        因此此歷史檔案只包含 trailing dividend yield。
        """
        ticker = yf.Ticker(self.etf_ticker)
        hist = ticker.history(period=f"{years}y", interval="1mo", auto_adjust=False, actions=True)
        if hist is None or hist.empty:
            print("❌ 歷史估值資料抓取失敗：無法取得歷史價格/股利資料")
            return None

        hist = hist.copy()
        hist.index = hist.index.tz_localize(None)
        if 'Dividends' not in hist.columns:
            hist['Dividends'] = 0.0

        hist['Dividends'] = hist['Dividends'].fillna(0.0)
        hist['Trailing_Dividend_Yield'] = pd.NA

        for current_date in hist.index:
            start_date = current_date - pd.DateOffset(years=1)
            trailing_div = hist.loc[start_date:current_date, 'Dividends'].sum()
            close_price = hist.at[current_date, 'Close'] if 'Close' in hist.columns else hist.at[current_date, 'Adj Close']
            hist.at[current_date, 'Trailing_Dividend_Yield'] = trailing_div / close_price if close_price else None

        valuation_history = hist[['Trailing_Dividend_Yield']]
        self.valuation_history = valuation_history
        print(f"✅ 近 {years} 年歷史估值資料計算完成 | 總筆數: {len(valuation_history)}")
        return valuation_history


    def save_data(self):
        """儲存所有資料到 CSV。價格資料與估值資料分開儲存。"""
        if self.price_data is not None:
            self.price_data.to_csv(f"{self.market_name}_price_max.csv")
            print(f"💾 價格資料已儲存 → {self.market_name}_price_max.csv")

        if self.valuation_data is not None:
            valuation_df = pd.DataFrame([self.valuation_data])
            valuation_df.to_csv('NIKKEIvaluation.csv', index=False)
            print(f"💾 基本估值資料已儲存 → NIKKEIvaluation.csv")

        if self.valuation_history is not None:
            self.valuation_history[['Trailing_Dividend_Yield']].to_csv('NIKKEIvaluation_history.csv', index=True, date_format='%Y-%m-%d')
            print(f"💾 歷史估值資料已儲存 → NIKKEIvaluation_history.csv")

    def build_dataset(self, years=15):
        """建立 NIKKEI 225 月度價格資料集，並同時更新最新估值快照及歷史估值資料。"""
        price_data = self.fetch_price_data(interval="1mo", years=years)
        if price_data is None:
            raise RuntimeError("價格資料抓取失敗，無法建立資料集")

        self.fetch_valuation_data()
        self.fetch_valuation_history(years=years)

        if self.valuation_history is not None:
            dataset = price_data.join(self.valuation_history[['Trailing_Dividend_Yield']], how='left')
        else:
            dataset = price_data

        return dataset

    def save_dataset(self, dataset):
        output_path = f"{self.market_name}_dataset.csv"
        dataset.to_csv(output_path)
        print(f"💾 合併資料集已儲存 → {output_path}")

    def run(self):
        print("🚀 開始抓取 NIKKEI 225 資料...")
        dataset = self.build_dataset(years=15)
        self.save_dataset(dataset)
        self.save_data()
        print("🎉 抓取完成！")


if __name__ == "__main__":
    scraper = NIKKEIScraper()
    scraper.run()