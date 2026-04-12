import io
import requests
import pandas as pd


# 這個腳本用來收集 S&P 500 的月度價格資料，並從 multpl.com 抓取估值變數。
# 最終輸出 CSV 檔案 `sp500_data.csv`。


def fetch_sp500_monthly_prices(start_date="2011-01-01") -> pd.DataFrame:
    """從 Yahoo Finance HTTP JSON API 下載 S&P 500 的日資料，並轉換成月度資料。"""
    start_ts = int(pd.Timestamp(start_date, tz="UTC").timestamp())
    end_ts = int(pd.Timestamp.now(tz="UTC").timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
        f"?period1={start_ts}&period2={end_ts}&interval=1d&includePrePost=false&events=div|split"
    )

    response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    payload = response.json()

    result = payload.get("chart", {}).get("result")
    if not result:
        raise RuntimeError("No chart result returned from Yahoo Finance API")
    result = result[0]

    timestamps = result.get("timestamp")
    quote = result.get("indicators", {}).get("quote", [{}])[0]
    adjclose = result.get("indicators", {}).get("adjclose", [{}])[0].get("adjclose")
    if not timestamps or not quote:
        raise RuntimeError("Missing quote data from Yahoo Finance JSON response")

    price_data = pd.DataFrame(
        {
            "Date": pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(None),
            "Open": quote.get("open"),
            "High": quote.get("high"),
            "Low": quote.get("low"),
            "Close": quote.get("close"),
            "Adj Close": adjclose,
            "Volume": quote.get("volume"),
        }
    )
    price_data = price_data.dropna(subset=["Date", "Close"]).set_index("Date")

    monthly = price_data.resample("ME").agg(
        {
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Adj Close": "last",
            "Volume": "sum",
        }
    )
    monthly = monthly.loc[monthly.index >= pd.to_datetime(start_date)]

    # 移除當前尚未完成的月度資料，避免出現未來月末標籤
    current_period = pd.Timestamp.now().to_period("M")
    monthly = monthly.loc[monthly.index.to_period("M") < current_period]

    monthly.index.name = "Date"
    return monthly


def fetch_multpl_monthly_series(url: str, value_name: str) -> pd.DataFrame:
    """從 multpl.com 抓取單一月度序列，並整理成標準時間索引。"""
    response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    # 使用 pandas 解析 HTML 表格，進行基本的爬蟲處理
    tables = pd.read_html(io.StringIO(response.text))
    if not tables:
        raise RuntimeError(f"No tables found at {url}")

    df = tables[0].copy()
    df.columns = [str(c).strip() for c in df.columns]
    if len(df.columns) < 2:
        raise RuntimeError(f"Unexpected table structure for {url}")

    # 只取前兩欄：日期與目標指標值
    df = df.iloc[:, :2]
    df.columns = ["Date", value_name]

    # 解析日期並轉成月末時間點
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce") + pd.offsets.MonthEnd(0)

    # 將數值欄位轉成數字，移除百分比符號後再轉換
    df[value_name] = pd.to_numeric(df[value_name].astype(str).str.replace("%", ""), errors="coerce")

    # 清理日期錯誤並依日期排序
    df = df.dropna(subset=["Date"]).set_index("Date").sort_index()
    return df


def fetch_multpl_proxies() -> pd.DataFrame:
    """從 multpl.com 撈取三個估值代理變數，並合併成一個表格。"""
    pe = fetch_multpl_monthly_series(
        "https://www.multpl.com/s-p-500-pe-ratio/table/by-month",
        "PE_Ratio",
    )
    cape = fetch_multpl_monthly_series(
        "https://www.multpl.com/shiller-pe/table/by-month",
        "CAPE",
    )
    dividend = fetch_multpl_monthly_series(
        "https://www.multpl.com/s-p-500-dividend-yield/table/by-month",
        "Dividend_Yield",
    )

    # 將三個月度序列按照日期合併為一個 dataframe
    proxies = pe.join([cape, dividend], how="outer")
    proxies = proxies.loc[proxies.index >= pd.to_datetime("2011-01-01")]
    return proxies


def build_dataset() -> pd.DataFrame:
    """組合價格資料與估值代理變數，並回傳完整資料集。"""
    prices = fetch_sp500_monthly_prices(start_date="2011-01-01")
    proxies = fetch_multpl_proxies()

    merged = prices.join(proxies, how="left")
    merged = merged.sort_index()

    return merged


def main():
    """主程式入口：建立資料集並寫出 CSV 檔案。"""
    dataset = build_dataset()
    output_path = "sp500_data.csv"
    dataset.to_csv(output_path, float_format="%.6f")
    print(f"Saved S&P 500 dataset with {len(dataset)} monthly rows to {output_path}")


if __name__ == "__main__":
    main()
