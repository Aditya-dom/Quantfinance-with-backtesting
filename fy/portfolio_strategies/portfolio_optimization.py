# Import dependencies
import datetime
import numpy as np
import pandas as pd
import scipy.optimize as sco
import pandas_datareader as pdr
import matplotlib.pyplot as plt
from pypfopt import risk_models
from pypfopt import expected_returns
from pandas.plotting import register_matplotlib_converters
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices

# Registering converters for using matplotlib's plot_date() function.
register_matplotlib_converters()

# Setting display options for pandas
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

# Defining stocks to include in the portfolio
stocks = ["SCHB", "AAPL", "AMZN", "TSLA", "AMD", "MSFT", "NFLX"]

# Getting historical data from Yahoo Finance
start = datetime.date(2020, 8, 13)
end = datetime.datetime.now()
df = pdr.get_data_yahoo(stocks, start=start, end=end)["Close"]

# Printing the last few rows of the data
print(df.tail())

# Calculating daily returns of each stock
returns = df.pct_change()

# Plotting the daily returns of each stock
returns.plot(grid=True).axhline(y=0, color="black", lw=2)
plt.legend(loc="upper right", fontsize=12)
plt.ylabel("Daily Returns")

# Defining a function to calculate the annualized performance of a portfolio
def portfolio_annualised_performance(weights, mean_returns, cov_matrix):
    returns = np.sum(mean_returns * weights) * 252
    std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
    return std, returns

# Defining a function to generate random portfolios
def random_portfolios(num_portfolios, mean_returns, cov_matrix, risk_free_rate):
    results = np.zeros((3, num_portfolios))
    weights_record = []
    for i in range(num_portfolios):
        weights = np.random.random(n)
        weights /= np.sum(weights)
        weights_record.append(weights)
        portfolio_std_dev, portfolio_return = portfolio_annualised_performance(
            weights, mean_returns, cov_matrix
        )
        results[0, i] = portfolio_std_dev
        results[1, i] = portfolio_return
        results[2, i] = (portfolio_return - risk_free_rate) / portfolio_std_dev
    return results, weights_record

# Calculating mean returns and covariance matrix of returns
mean_returns = returns.mean()
cov_matrix = returns.cov()

# Setting the number of random portfolios to generate and the risk-free rate
num_portfolios = 50000
risk_free_rate = 0.021

# Defining a function to calculate the negative Sharpe ratio
def neg_sharpe_ratio(weights, mean_returns, cov_matrix, risk_free_rate):
    p_var, p_ret = portfolio_annualised_performance(weights, mean_returns, cov_matrix)
    return -(p_ret - risk_free_rate) / p_var

# Defining a function to find the portfolio with maximum Sharpe ratio
def max_sharpe_ratio(mean_returns, cov_matrix, risk_free_rate):
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix, risk_free_rate)
    constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}
    bound = (0.0, 1.0)
    bounds = tuple(bound for asset in range(num_assets))
    result = sco.minimize(
        neg_sharpe_ratio,
        num_assets
        * [
            1.0 / num_assets,
        ],
        args=args,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    return result

def portfolio_volatility(weights, mean_returns, cov_matrix):
    return portfolio_annualised_performance(weights, mean_returns, cov_matrix)[0]

def min_variance(mean_returns, cov_matrix):
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix)
    constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}
    bound = (0.0, 1.0)
    bounds = tuple(bound for asset in range(num_assets))

    result = sco.minimize(
        portfolio_volatility,
        num_assets
        * [
            1.0 / num_assets,
        ],
        args=args,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )

    return result

def efficient_return(mean_returns, cov_matrix, target):
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix)

    def portfolio_return(weights):
        return portfolio_annualised_performance(weights, mean_returns, cov_matrix)[1]

    constraints = (
        {"type": "eq", "fun": lambda x: portfolio_return(x) - target},
        {"type": "eq", "fun": lambda x: np.sum(x) - 1},
    )
    bounds = tuple((0, 1) for asset in range(num_assets))
    result = sco.minimize(
        portfolio_volatility,
        num_assets
        * [
            1.0 / num_assets,
        ],
        args=args,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    return result

def efficient_frontier(mean_returns, cov_matrix, returns_range):
    efficients = []
    for ret in returns_range:
        efficients.append(efficient_return(mean_returns, cov_matrix, ret))
    return efficients

def display_calculated_ef_with_random(
    mean_returns, cov_matrix, num_portfolios, risk_free_rate
):
    results, _ = random_portfolios(
        num_portfolios, mean_returns, cov_matrix, risk_free_rate
    )

    max_sharpe = max_sharpe_ratio(mean_returns, cov_matrix, risk_free_rate)
    sdp, rp = portfolio_annualised_performance(
        max_sharpe["x"], mean_returns, cov_matrix
    )
    max_sharpe_allocation = pd.DataFrame(
        max_sharpe.x, index=df.columns, columns=["allocation"]
    )
    max_sharpe_allocation.allocation = [
        round(i * 100, 2) for i in max_sharpe_allocation.allocation
    ]
    max_sharpe_allocation = max_sharpe_allocation.T
    max_sharpe_allocation

    min_vol = min_variance(mean_returns, cov_matrix)
    sdp_min, rp_min = portfolio_annualised_performance(
        min_vol["x"], mean_returns, cov_matrix
    )
    min_vol_allocation = pd.DataFrame(
        min_vol.x, index=df.columns, columns=["allocation"]
    )
    min_vol_allocation.allocation = [
        round(i * 100, 2) for i in min_vol_allocation.allocation
    ]
    min_vol_allocation = min_vol_allocation.T

    plt.figure(figsize=(10, 7))
    plt.scatter(
        results[0, :],
        results[1, :],
        c=results[2, :],
        cmap="YlGnBu",
        marker="o",
        s=10,
        alpha=0.3,
    )
    plt.colorbar()
    plt.scatter(sdp, rp, marker="*", color="r", s=500, label="Maximum Sharpe ratio")
    plt.scatter(
        sdp_min, rp_min, marker="*", color="g", s=500, label="Minimum volatility"
    )

    target = np.linspace(rp_min, 0.32, 50)
    efficient_portfolios = efficient_frontier(mean_returns, cov_matrix, target)
    plt.plot(
        [p["fun"] for p in efficient_portfolios],
        target,
        linestyle="-.",
        color="black",
        label="efficient frontier",
    )
    plt.title("Calculated Portfolio Optimization based on Efficient Frontier")
    plt.xlabel("annualised volatility")
    plt.ylabel("annualised returns")
    plt.legend(labelspacing=0.8)
    plt.show()

display_calculated_ef_with_random(
    mean_returns, cov_matrix, num_portfolios, risk_free_rate
)

def display_ef_with_selected(mean_returns, cov_matrix, risk_free_rate):
    max_sharpe = max_sharpe_ratio(mean_returns, cov_matrix, risk_free_rate)
    sdp, rp = portfolio_annualised_performance(
        max_sharpe["x"], mean_returns, cov_matrix
    )
    max_sharpe_allocation = pd.DataFrame(
        max_sharpe.x, index=df.columns, columns=["allocation"]
    )
    max_sharpe_allocation.allocation = [
        round(i * 100, 2) for i in max_sharpe_allocation.allocation
    ]
    max_sharpe_allocation = max_sharpe_allocation.T
    max_sharpe_allocation

    min_vol = min_variance(mean_returns, cov_matrix)
    sdp_min, rp_min = portfolio_annualised_performance(
        min_vol["x"], mean_returns, cov_matrix
    )
    min_vol_allocation = pd.DataFrame(
        min_vol.x, index=df.columns, columns=["allocation"]
    )
    min_vol_allocation.allocation = [
        round(i * 100, 2) for i in min_vol_allocation.allocation
    ]
    min_vol_allocation = min_vol_allocation.T

    an_vol = np.std(returns) * np.sqrt(252)
    an_rt = mean_returns * 252

    print("-" * 80)
    print("Maximum Sharpe Ratio Portfolio Allocation\n")
    print("Annualised Return:", round(rp, 2))
    print("Annualised Volatility:", round(sdp, 2))
    print("\n")
    print(max_sharpe_allocation)
    print("-" * 80)
    print("Minimum Volatility Portfolio Allocation\n")
    print("Annualised Return:", round(rp_min, 2))
    print("Annualised Volatility:", round(sdp_min, 2))
    print("\n")
    print(min_vol_allocation)
    print("-" * 80)
    print("Individual Stock Returns and Volatility\n")
    for i, txt in enumerate(df.columns):
        print(
            txt,
            ":",
            "annualised return",
            round(an_rt[i], 2),
            ", annualised volatility:",
            round(an_vol[i], 2),
        )
    print("-" * 80)
    plt.show()

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(an_vol, an_rt, marker="o", s=200)

    for i, txt in enumerate(df.columns):
        ax.annotate(
            txt, (an_vol[i], an_rt[i]), xytext=(10, 0), textcoords="offset points"
        )
    ax.scatter(sdp, rp, marker="*", color="r", s=500, label="Maximum Sharpe ratio")
    ax.scatter(
        sdp_min, rp_min, marker="*", color="g", s=500, label="Minimum volatility"
    )

    target = np.linspace(rp_min, 0.34, 50)
    efficient_portfolios = efficient_frontier(mean_returns, cov_matrix, target)
    ax.plot(
        [p["fun"] for p in efficient_portfolios],
        target,
        linestyle="-.",
        color="black",
        label="efficient frontier",
    )
    ax.set_title("Portfolio Optimization with Individual Stocks")
    ax.set_xlabel("annualised volatility")
    ax.set_ylabel("annualised returns")
    ax.legend(labelspacing=0.8)
    plt.show()

display_ef_with_selected(mean_returns, cov_matrix, risk_free_rate)

stocks = df
n = 1000  # total port. value

# Calculate expected returns and sample covariance
mu = expected_returns.mean_historical_return(df)
S = risk_models.sample_cov(df)

# Optimise for maximal Sharpe ratio
ef = EfficientFrontier(mu, S)
raw_weights = ef.max_sharpe()
cleaned_weights = ef.clean_weights()
ef.portfolio_performance(verbose=True)

latest_prices = get_latest_prices(df)

da = DiscreteAllocation(cleaned_weights, latest_prices, total_portfolio_value=n)
allocation, leftover = da.lp_portfolio()
print("Discrete allocation:", allocation)
print("Funds remaining: ${:.2f}".format(leftover))