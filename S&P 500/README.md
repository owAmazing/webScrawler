# S&P 500 Historical and Valuation Data

This project collects monthly S&P 500 price history and fundamental valuation proxies for the last 15+ years.

## Data collected

- `Date`: month-end date
- `Open`: monthly first trading day open price
- `High`: monthly maximum high price
- `Low`: monthly minimum low price
- `Close`: monthly last trading day close price
- `Adj Close`: monthly last trading day adjusted close price
- `Volume`: monthly total traded volume
- `CAPE`: cyclically adjusted price-to-earnings ratio scraped from multpl.com
- `Dividend_Yield`: trailing 12-month dividend yield scraped from multpl.com
- `PE_Ratio`: standard trailing price-to-earnings ratio scraped from multpl.com

## Data sources

- S&P 500 price history: Yahoo Finance (`^GSPC`)
- Valuation proxies: multpl.com monthly valuation tables
  - `https://www.multpl.com/s-p-500-pe-ratio/table/by-month`
  - `https://www.multpl.com/shiller-pe/table/by-month`
  - `https://www.multpl.com/s-p-500-dividend-yield/table/by-month`

## Files

- `collect_sp500_data.py`: Python script that fetches data and saves `sp500_data.csv`
- `sp500_data.csv`: output CSV file containing monthly data
- `analyze_sp500_strategies.py`: Python script that simulates three investment strategies and creates charts

## How to run

1. Install dependencies: `pip install pandas requests yfinance lxml`
2. Run the script: `python collect_sp500_data.py`
3. `sp500_data.csv` will be created in the same folder

## How to analyze strategies

1. Run `python analyze_sp500_strategies.py`
2. This generates the following outputs:
   - `price_trend.png`
   - `investment_vs_value.png`
   - `final_performance.png`
   - `strategy_summary.csv`
