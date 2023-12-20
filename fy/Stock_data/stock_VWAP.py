# Import dependencies
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
import datetime as dt

from pandas_datareader import data as pdr
import statsmodels.api as sm

# Set stock symbol
stock = 'AAPL'

# Define function to get stock data for a specified time range
def get_symbol(symbol):
    num_of_years = 1
    start_date = dt.date.today() - dt.timedelta(days=365*num_of_years)
    end_date = dt.date.today()
    df = pdr.get_data_yahoo(symbol, start_date, end_date)
    return df

# Calculate VWAP for a stock symbol
def VWAP():
    df = get_symbol(stock)
    df['Typical_Price'] = (df['High'] + df['Low'] + df['Adj Close']) / 3
    df['TP_Volume'] = df['Typical_Price'] * df['Volume']
    cumulative_TP_V = df['TP_Volume'].sum() 
    cumulative_V = df['Volume'].sum()
    vwap = cumulative_TP_V / cumulative_V
    return vwap

# Print VWAP for the stock symbol
print(VWAP())

# Update VWAP for the stock symbol
def update_VWAP():
    df = get_symbol(stock)
    df['OpenxVolume'] = df['Open'] * df['Volume']
    df['HighxVolume'] = df['High'] * df['Volume']
    df['LowxVolume'] = df['Low'] * df['Volume']
    df['ClosexVolume'] = df['Adj Close'] * df['Volume']
    sum_volume = df['Volume'].sum()
    sum_x_OV = df['OpenxVolume'].sum() / sum_volume
    sum_x_HV = df['HighxVolume'].sum() / sum_volume
    sum_x_LV = df['LowxVolume'].sum() / sum_volume
    sum_x_CV = df['ClosexVolume'].sum() / sum_volume
    average_volume_each = (sum_x_OV + sum_x_HV + sum_x_LV + sum_x_OV) / 4
    new_vwap = ((df['Adj Close'][-1] - average_volume_each) + (df['Adj Close'][-1] + average_volume_each)) / 2
    return new_vwap

# Print updated VWAP for the stock symbol
print(update_VWAP())

# Add VWAP column to the stock data
def add_VWAP_column():
    df = get_symbol(stock)
    df['OpenxVolume'] = df['Open'] * df['Volume']
    df['HighxVolume'] = df['High'] * df['Volume']
    df['LowxVolume'] = df['Low'] * df['Volume']
    df['ClosexVolume'] = df['Adj Close'] * df['Volume']
    vwap_column = (df[['OpenxVolume','HighxVolume','LowxVolume','ClosexVolume']].mean(axis=1))/df['Volume']
    df['VWAP'] = vwap_column
    return df

# Print stock data with VWAP column
print(add_VWAP_column())