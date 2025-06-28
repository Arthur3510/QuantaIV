"""
Strategy Runner

This utility module contains the core logic for applying a given trading
strategy to a price series and generating a trading signal.
"""
import pandas as pd
from .indicator_utils import calculate_rsi, calculate_sma

def apply_strategy(strategy_type: str, price_df: pd.DataFrame, params: dict) -> int:
    """
    Applies the specified strategy logic to the price data.

    Args:
        strategy_type (str): The type of strategy (e.g., 'RSI', 'CROSS').
        price_df (pd.DataFrame): DataFrame with historical price data, must contain 'close'.
        params (dict): A dictionary of parameters for the strategy.

    Returns:
        int: The trading signal: 1 for buy, -1 for sell, 0 for hold.
    """
    if strategy_type.upper() == 'RSI':
        return _apply_rsi_strategy(price_df, params)
    elif strategy_type.upper() == 'CROSS':
        return _apply_cross_strategy(price_df, params)
    else:
        print(f"WARNING: Strategy type '{strategy_type}' is not supported.")
        return 0

def _apply_rsi_strategy(price_df: pd.DataFrame, params: dict) -> int:
    """
    Calculates the RSI signal based on the latest price data.
    """
    rsi_period = params.get('rsi_period')
    rsi_upper = params.get('rsi_upper')
    rsi_lower = params.get('rsi_lower')

    if not all([rsi_period, rsi_upper, rsi_lower]):
        print("WARNING: RSI strategy is missing one or more parameters.")
        return 0

    price_df = calculate_rsi(price_df, rsi_period, 'close')
    latest_rsi = price_df['rsi'].iloc[-1]

    if latest_rsi > rsi_upper:
        return -1  # Sell signal
    elif latest_rsi < rsi_lower:
        return 1   # Buy signal
    else:
        return 0   # Hold signal

def _apply_cross_strategy(price_df: pd.DataFrame, params: dict) -> int:
    """
    Calculates the Moving Average Crossover signal.
    """
    fast_period = params.get('fast_period')
    slow_period = params.get('slow_period')

    if not all([fast_period, slow_period]):
        print("WARNING: Crossover strategy is missing one or more parameters.")
        return 0

    price_df = calculate_sma(price_df, fast_period, 'short_mavg', 'close')
    price_df = calculate_sma(price_df, slow_period, 'long_mavg', 'close')
    
    # We need to look at the previous day and today to see if a cross occurred
    prev_short = price_df['short_mavg'].iloc[-2]
    prev_long = price_df['long_mavg'].iloc[-2]
    curr_short = price_df['short_mavg'].iloc[-1]
    curr_long = price_df['long_mavg'].iloc[-1]

    # Golden cross: short-term MA crosses above long-term MA
    if prev_short <= prev_long and curr_short > curr_long:
        return 1 # Buy signal
    # Death cross: short-term MA crosses below long-term MA
    elif prev_short >= prev_long and curr_short < curr_long:
        return -1 # Sell signal
    else:
        return 0 # Hold signal 