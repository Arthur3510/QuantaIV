import pandas as pd

def calculate_rsi(data, period=14, price_col='close'):
    """Calculate the Relative Strength Index (RSI)"""
    delta = data[price_col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    data['rsi'] = rsi
    return data

def calculate_sma(data, period, col_name, price_col='close'):
    """Calculate Simple Moving Average (SMA)"""
    data[col_name] = data[price_col].rolling(window=period).mean()
    return data 