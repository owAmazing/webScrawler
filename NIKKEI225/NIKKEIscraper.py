# NIKKEIscraper.py
import requests
import pandas as pd
import time
import yfinance as yf
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class NIKKEIScraper:
    def __init__(self):
        self.ticker = '^N225'
        self.market_name = 'NIKKEI225'
        self.price_data = None
        self.valuation_data = None
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
        """抓取估值指標（Yahoo API + Yahoo HTML + 日經官方）"""
        val_data = {
            'Market': self.market_name,
            'Ticker': self.ticker,
            'As_Of_Date': datetime.now().strftime('%Y-%m-%d'),
            'Trailing_PE': 'N/A',
            'Price_Book': 'N/A',
            'Dividend_Yield': 'N/A',
            'CAPE': 'N/A'
        }

        # 1. 嘗試使用 yfinance 取得基本估值
        try:
            yfinance_val = self._fetch_yfinance_valuation()
            if yfinance_val:
                for key, value in yfinance_val.items():
                    if value is not None:
                        val_data[key] = value
        except Exception as e:
            print(f"yfinance 估值抓取失敗: {e}")

        # 2. 嘗試從日經官方 archive 抓取估值資料
        try:
            nikkei_val = self._fetch_nikkei_archive_valuation()
            if nikkei_val:
                for key, value in nikkei_val.items():
                    if value is not None and val_data.get(key) in ('N/A', None):
                        val_data[key] = value
        except Exception as e:
            print(f"日經官方 archive 估值抓取失敗: {e}")

        # 3. 如果 yfinance/API 沒抓到，再以 HTML 解析 Yahoo key statistics
        try:
            if val_data['Trailing_PE'] == 'N/A' or val_data['Price_Book'] == 'N/A' or val_data['Dividend_Yield'] == 'N/A' or val_data['CAPE'] == 'N/A':
                url = f"https://finance.yahoo.com/quote/{self.ticker}/key-statistics"
                resp = requests.get(url, headers=self.headers, timeout=15)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    if val_data['Trailing_PE'] == 'N/A':
                        val_data['Trailing_PE'] = self._parse_value(soup, ['Trailing P/E', 'Trailing PE'])
                    if val_data['Price_Book'] == 'N/A':
                        val_data['Price_Book'] = self._parse_value(soup, ['Price/Book', 'Price to Book'])
                    if val_data['Dividend_Yield'] == 'N/A':
                        val_data['Dividend_Yield'] = self._parse_value(soup, ['Forward Annual Dividend Yield', 'Trailing Annual Dividend Yield', 'Dividend Yield'])
                    if val_data['CAPE'] == 'N/A':
                        val_data['CAPE'] = self._parse_value(soup, ['CAPE', 'Cyclically Adjusted P/E', 'Cyclically Adjusted P/E (CAPE)'])
        except Exception as e:
            print(f"Yahoo HTML 估值抓取失敗: {e}")

        self.valuation_data = val_data
        print("✅ 估值資料抓取完成")
        print(f"   PE: {val_data['Trailing_PE']} | PB: {val_data['Price_Book']} | Dividend Yield: {val_data['Dividend_Yield']} | CAPE: {val_data['CAPE']}")
        return val_data

    def _fetch_yahoo_valuation(self):
        url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{self.ticker}?modules=summaryDetail,defaultKeyStatistics,financialData"
        resp = requests.get(url, headers=self.headers, timeout=20)
        if resp.status_code != 200:
            return {}

        data = resp.json().get('quoteSummary', {}).get('result')
        if not data:
            return {}

        result = data[0]
        def g(path):
            node = result
            for key in path:
                node = node.get(key) if isinstance(node, dict) else None
                if node is None:
                    return None
            return node

        pe = g(['summaryDetail', 'trailingPE']) or g(['defaultKeyStatistics', 'trailingPE'])
        pb = g(['summaryDetail', 'priceToBook'])
        div = g(['summaryDetail', 'trailingAnnualDividendYield']) or g(['summaryDetail', 'dividendYield'])

        return {
            'Trailing_PE': self._format_numeric(pe),
            'Price_Book': self._format_numeric(pb),
            'Dividend_Yield': self._format_percent(div),
            'CAPE': None
        }

    def _fetch_yfinance_valuation(self):
        ticker = yf.Ticker(self.ticker)
        info = ticker.info or {}
        pe = info.get('trailingPE') or info.get('forwardPE')
        pb = info.get('priceToBook')
        div = info.get('trailingAnnualDividendYield') or info.get('dividendYield')

        return {
            'Trailing_PE': self._format_numeric(pe),
            'Price_Book': self._format_numeric(pb),
            'Dividend_Yield': self._format_percent(div),
            'CAPE': None
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

    def _parse_value(self, soup, labels):
        for label in labels:
            elements = soup.find_all(string=lambda t: t and label in t)
            for elem in elements:
                parent = elem.find_parent('tr') or elem.find_parent('td')
                if parent:
                    tds = parent.find_all('td')
                    if len(tds) > 1 and tds[-1].text.strip():
                        return tds[-1].text.strip()
        return "N/A"

    def _fetch_nikkei_archive_valuation(self):
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://indexes.nikkei.co.jp/en/nkave/archives',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        result = {
            'Trailing_PE': None,
            'Price_Book': None,
            'Dividend_Yield': None,
            'CAPE': None,
        }

        def parse_last_row(url, expected_cols):
            resp = session.get(url, timeout=20)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.text, 'html.parser')
            table = soup.find('table')
            if not table:
                return None
            rows = table.find_all('tr')
            for row in reversed(rows):
                cols = [td.get_text(strip=True) for td in row.find_all('td')]
                if len(cols) >= expected_cols and cols[0]:
                    return cols
            return None

        try:
            pbr_cols = parse_last_row('https://indexes.nikkei.co.jp/en/nkave/archives/data?list=pbr', 3)
            if pbr_cols:
                result['Trailing_PE'] = pbr_cols[1]
                result['Price_Book'] = pbr_cols[2]
        except Exception:
            pass

        try:
            div_cols = parse_last_row('https://indexes.nikkei.co.jp/en/nkave/archives/data?list=dividend-yield', 2)
            if div_cols:
                result['Dividend_Yield'] = div_cols[1]
        except Exception:
            pass

        try:
            cape_cols = parse_last_row('https://indexes.nikkei.co.jp/en/nkave/archives/data?list=cape', 2)
            if cape_cols:
                result['CAPE'] = cape_cols[1]
        except Exception:
            pass

        return result

    def save_data(self):
        """儲存所有資料到 CSV"""
        if self.price_data is not None:
            price_output = self.price_data.copy()
            if self.valuation_data is not None:
                for key in ['Trailing_PE', 'Price_Book', 'Dividend_Yield', 'CAPE']:
                    price_output[key] = self.valuation_data.get(key)
            price_output.to_csv(f"{self.market_name}_price_max.csv")
            print(f"💾 價格資料已儲存 → {self.market_name}_price_max.csv")

        if self.valuation_data is not None:
            pd.DataFrame([self.valuation_data]).to_csv(f"{self.market_name}_basic_info.csv", index=False)
            print(f"💾 基本估值資料已儲存 → {self.market_name}_basic_info.csv")

    def build_dataset(self, years=15):
        """建立 NIKKEI 225 月度資料集，包含價格與最新估值欄位。"""
        price_data = self.fetch_price_data(interval="1mo", years=years)
        if price_data is None:
            raise RuntimeError("價格資料抓取失敗，無法建立資料集")

        valuation = self.fetch_valuation_data()
        metrics = {
            'Trailing_PE': valuation.get('Trailing_PE'),
            'Price_Book': valuation.get('Price_Book'),
            'Dividend_Yield': valuation.get('Dividend_Yield'),
            'CAPE': valuation.get('CAPE'),
        }

        proxies = pd.DataFrame(
            {key: [value] * len(price_data) for key, value in metrics.items()},
            index=price_data.index,
        )

        dataset = price_data.join(proxies, how='left')
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