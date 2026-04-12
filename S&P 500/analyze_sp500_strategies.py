import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def load_data(path="sp500_data.csv") -> pd.DataFrame:
    """讀取 CSV 價格資料並轉成時間排序的 DataFrame。"""
    df = pd.read_csv(path, parse_dates=["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df


def dca_strategy(prices: pd.Series, monthly_amount: float) -> pd.DataFrame:
    """Standard DCA：每月投入固定金額，買入當月收盤價股票。"""
    # 每月用固定金額買入多少股
    shares = monthly_amount / prices
    # 每月累積持股後的組合市值
    value = shares.cumsum() * prices
    # 總投入金額每月固定遞增
    cumulative_invested = np.arange(1, len(prices) + 1) * monthly_amount

    return pd.DataFrame(
        {
            "Date": prices.index,
            "Strategy": "DCA",
            "Monthly_Contribution": monthly_amount,
            "Cumulative_Investment": cumulative_invested,
            "Shares_Held": shares.cumsum(),
            "Portfolio_Value": value,
            "Cash_Flow": monthly_amount,
        }
    )


def fixed_shares_strategy(prices: pd.Series, monthly_shares: float) -> pd.DataFrame:
    """Fixed Shares：每月固定買入相同股數，而投資金額會隨價格波動。"""
    # 每月買入固定股數
    shares = np.full(len(prices), monthly_shares)
    # 累積持股數
    cumulative_shares = np.cumsum(shares)
    # 每月投入的金額取決於當月股價
    monthly_investment = shares * prices
    # 總投入金額是每月投入金額的累積
    cumulative_invested = monthly_investment.cumsum()
    # 以累積持股數乘上當月價格計算組合市值
    value = cumulative_shares * prices

    return pd.DataFrame(
        {
            "Date": prices.index,
            "Strategy": "Fixed Shares",
            "Monthly_Contribution": monthly_investment,
            "Cumulative_Investment": cumulative_invested,
            "Shares_Held": cumulative_shares,
            "Portfolio_Value": value,
            "Cash_Flow": monthly_investment,
        }
    )


def value_averaging_strategy(prices: pd.Series, target_growth: float) -> pd.DataFrame:
    """Value Averaging：目標市值線性成長，若組合價值低於目標則補足買進。"""
    # 每月期望的組合市值目標
    target_values = np.arange(1, len(prices) + 1) * target_growth
    shares = []
    cumulative_shares = 0.0
    monthly_cash_flows = []
    portfolio_values = []

    for target_value, price in zip(target_values, prices):
        current_value = cumulative_shares * price
        # 如果組合價值低於目標，則補足差額買進；如果高於目標，當月不再買進
        invest = max(target_value - current_value, 0.0)
        shares_bought = invest / price if price else 0.0

        cumulative_shares += shares_bought
        monthly_cash_flows.append(invest)
        portfolio_values.append(cumulative_shares * price)
        shares.append(cumulative_shares)

    cumulative_investment = np.cumsum(monthly_cash_flows)

    return pd.DataFrame(
        {
            "Date": prices.index,
            "Strategy": "Value Averaging",
            "Monthly_Contribution": monthly_cash_flows,
            "Cumulative_Investment": cumulative_investment,
            "Shares_Held": shares,
            "Portfolio_Value": portfolio_values,
            "Cash_Flow": monthly_cash_flows,
        }
    )


def aggregate_strategies(df: pd.DataFrame, monthly_amount: float = 1000.0, monthly_shares: float = 1.0, target_growth: float = 1000.0) -> pd.DataFrame:
    prices = df["Close"]
    prices.index = df["Date"]

    dca = dca_strategy(prices, monthly_amount)
    fixed_shares = fixed_shares_strategy(prices, monthly_shares)
    value_avg = value_averaging_strategy(prices, target_growth)

    return pd.concat([dca, fixed_shares, value_avg], ignore_index=True)


def plot_price_trend(df: pd.DataFrame, output_path="price_trend.png"):
    plt.figure(figsize=(12, 6))
    plt.plot(df["Date"], df["Close"], label="S&P 500 Close", color="tab:blue")
    plt.title("S&P 500 Price Trend")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_cumulative_investment_vs_value(results: pd.DataFrame, output_path="investment_vs_value.png"):
    plt.figure(figsize=(12, 6))
    for name, group in results.groupby("Strategy"):
        plt.plot(group["Date"], group["Cumulative_Investment"], label=f"{name} Invested", linestyle="--")
        plt.plot(group["Date"], group["Portfolio_Value"], label=f"{name} Portfolio Value")
    plt.title("Cumulative Investment vs Portfolio Value")
    plt.xlabel("Date")
    plt.ylabel("USD")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_final_performance(results: pd.DataFrame, output_path="final_performance.png"):
    summary = results.groupby("Strategy").agg(
        Final_Value=("Portfolio_Value", "last"),
        Total_Investment=("Cumulative_Investment", "last")
    )
    summary = summary.reset_index()
    summary["Return"] = summary["Final_Value"] - summary["Total_Investment"]

    strategies = summary["Strategy"]
    x = np.arange(len(strategies))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - width / 2, summary["Total_Investment"], width, label="Total Investment", color="tab:blue")
    ax.bar(x + width / 2, summary["Final_Value"], width, label="Final Portfolio Value", color="tab:orange")

    ax.set_xticks(x)
    ax.set_xticklabels(strategies)
    ax.set_title("Final Performance Comparison")
    ax.set_ylabel("USD")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.4, axis="y")

    for i, (investment, final_val) in enumerate(zip(summary["Total_Investment"], summary["Final_Value"])):
        ax.text(i - width / 2, investment, f"{investment:,.0f}", ha="center", va="bottom", fontsize=8)
        ax.text(i + width / 2, final_val, f"{final_val:,.0f}", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def save_summary(results: pd.DataFrame, output_path="strategy_summary.csv"):
    summary = results.groupby("Strategy").agg(
        Final_Value=("Portfolio_Value", "last"),
        Total_Investment=("Cumulative_Investment", "last")
    )
    summary = summary.reset_index()
    summary["Return"] = summary["Final_Value"] - summary["Total_Investment"]
    summary["ROI"] = summary["Return"] / summary["Total_Investment"]
    summary.to_csv(output_path, index=False)


def main():
    df = load_data("sp500_data.csv")
    results = aggregate_strategies(df, monthly_amount=1000.0, monthly_shares=1.0, target_growth=1000.0)
    plot_price_trend(df)
    plot_cumulative_investment_vs_value(results)
    plot_final_performance(results)
    save_summary(results)
    print("Generated strategy analysis charts and summary CSV.")


if __name__ == "__main__":
    main()
