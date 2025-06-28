"""
M6: Multi-Strategy Signal Generator

This module generates daily trading signals for various strategies and symbols.
It identifies the best-performing parameters from out-of-sample backtests,
loads the necessary data, applies the strategy logic, and outputs a daily
trade decision file.
"""
import os
import pandas as pd
from datetime import datetime
from utils.param_loader import load_param
from utils.db_loader import get_recent_price_series
from utils.strategy_runner import apply_strategy
from utils.version_manager import version_manager

def find_best_strategies_for_symbol(symbol: str) -> list:
    """
    Finds all best strategies for a given symbol by scanning the 'best' strategies directory.

    It looks for files matching the pattern 'best_strategies_*_{symbol}_*' inside
    the versioned 'strategies/out_sample/best/' directory.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').

    Returns:
        list: A list of dictionaries, where each dictionary represents a
              best strategy with keys like 'strategy_type', 'param_id', etc.
              Returns an empty list if no strategy files are found.
    """
    print(f"INFO: Finding best strategies for {symbol}...")
    
    # 使用版本管理器取得當前版本的最佳策略目錄
    current_version = version_manager.get_current_version()
    if not current_version:
        print("WARNING: No current version found. Please run M1-M5 workflow first.")
        return []
    
    best_strategies_dir = version_manager.get_version_path(current_version, "out_sample_best")
    all_strategies = []

    if not os.path.exists(best_strategies_dir):
        print(f"WARNING: Directory not found: {best_strategies_dir}")
        return []

    for filename in os.listdir(best_strategies_dir):
        # Check if filename contains the symbol and starts with 'best_strategies_'
        if f'_{symbol}_' in filename and filename.startswith('best_strategies_') and filename.endswith('.csv'):
            try:
                # Extract strategy type from filename, e.g., 'RSI' from 'best_strategies_NVDA_RSI_signals_all_params_...'
                parts = filename.replace('.csv', '').split('_')
                # Find the strategy type (RSI or CROSS) in the filename
                strategy_type = None
                for part in parts:
                    if part in ['RSI', 'CROSS']:
                        strategy_type = part
                        break
                
                if not strategy_type:
                    print(f"WARNING: Could not identify strategy type from filename: {filename}")
                    continue

                strategy_df = pd.read_csv(os.path.join(best_strategies_dir, filename))
                
                # As per our discussion, we take ALL strategies from the best list, not just top 1
                for _, row in strategy_df.iterrows():
                    strategy_info = row.to_dict()
                    strategy_info['strategy_type'] = strategy_type # Add strategy type for context
                    all_strategies.append(strategy_info)
                
                print(f"  - Loaded {len(strategy_df)} strategies from {filename}")

            except Exception as e:
                print(f"ERROR: Failed to read or process {filename}. Reason: {e}")

    return all_strategies

def generate_trade_signals(symbols: list):
    """
    Generates trading signals for a list of stock symbols and saves them to a file.

    For each symbol, it finds the best strategies identified in the out-of-sample
    validation phase (M5), fetches the latest price data, applies the strategy
    logic, and generates a buy (1), sell (-1), or hold (0) signal.

    The final output is a CSV file containing all trade decisions for the day.

    Args:
        symbols (list): A list of stock symbols to process (e.g., ['AAPL', 'TSLA']).
    """
    today_str = datetime.now().strftime('%Y%m%d')
    all_decisions = []

    print("M6 - Generating Simulated Trading Signals...")

    for symbol in symbols:
        print(f"Processing symbol: {symbol}")
        best_strategies = find_best_strategies_for_symbol(symbol)

        if not best_strategies:
            print(f"WARNING: No best strategies found for {symbol}. Skipping.")
            continue

        # Get recent price data once per symbol
        price_df = get_recent_price_series(symbol, window=30)
        if price_df.empty or len(price_df) < 2: # Need at least 2 points for some indicators
            print(f"WARNING: Insufficient price data for {symbol}. Skipping.")
            continue
        
        latest_price = price_df['close'].iloc[-1]

        for strategy_info in best_strategies:
            strategy_type = strategy_info.get('strategy_type')
            param_id = strategy_info.get('param_id')

            if not all([strategy_type, param_id]):
                print(f"WARNING: Incomplete strategy info found. Skipping: {strategy_info}")
                continue

            # Load the detailed parameters for the strategy
            params = load_param(strategy_type, param_id, symbol, 'out_sample')

            # Apply the strategy to get a signal
            signal = apply_strategy(strategy_type, price_df, params)

            decision = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'symbol': symbol,
                'strategy_type': strategy_type,
                'param_id': param_id,
                'signal': signal,
                'price': latest_price,
                'comment': strategy_info.get('comment', '')
            }
            all_decisions.append(decision)
            print(f"  -> Strategy: {strategy_type}, Param_ID: {param_id}, Signal: {signal}, Price: {latest_price}")

    if not all_decisions:
        print("M6 - No trade decisions were generated today.")
        return

    # Save the decisions to a daily file
    output_df = pd.DataFrame(all_decisions)
    
    # 使用版本管理器取得當前版本的訊號目錄
    current_version = version_manager.get_current_version()
    if current_version:
        output_dir = version_manager.get_version_path(current_version, "trading_signal")
    else:
        output_dir = 'trading_simulation/signal'
    
    output_path = os.path.join(output_dir, f'M6_trade_decisions_{today_str}.csv')
    
    # 確保目錄存在
    os.makedirs(output_dir, exist_ok=True)
    
    output_df.to_csv(output_path, index=False)
    print(f"\nSUCCESS: M6 process complete. Trade decisions saved to:\n{output_path}")
    if current_version:
        print(f"📂 版本目錄: {current_version}")

if __name__ == '__main__':
    # Example usage:
    # This allows the module to be run standalone for testing.
    # In the final system, this will be called from main_controller.py
    test_symbols = ['AAPL', 'NVDA'] # Example symbols
    generate_trade_signals(test_symbols) 