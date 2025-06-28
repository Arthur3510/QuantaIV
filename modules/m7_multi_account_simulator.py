"""
M7: Multi-Account Performance Simulator

This module simulates daily performance for multiple trading strategies,
each with its own virtual account.
"""
import os
import pandas as pd
from datetime import datetime, timedelta
from utils import config
from utils.version_manager import version_manager

def new_account(param_id):
    """Initializes a new trading account."""
    return {
        "param_id": param_id,
        "cash": config.INITIAL_CAPITAL,
        "position_size": 0,
        "position_value": 0.0,
        "total_value": config.INITIAL_CAPITAL,
        "last_updated": "N/A"
    }

def load_accounts_from_snapshot(snapshot_path: str) -> dict:
    """Loads all accounts from the previous day's snapshot CSV."""
    print(f"INFO: Loading accounts from snapshot: {snapshot_path}")
    df = pd.read_csv(snapshot_path)
    # Convert the DataFrame rows into a dictionary of account dicts, keyed by param_id
    accounts = {row['param_id']: row.to_dict() for _, row in df.iterrows()}
    return accounts

def update_account(account: dict, trade_signal: dict) -> dict:
    """
    Updates an account based on a trade signal.
    This is the core trading logic for the simulation.
    """
    signal = trade_signal['signal']
    price = trade_signal['price']
    
    # Update position value based on the new price
    account['position_value'] = account['position_size'] * price
    account['total_value'] = account['cash'] + account['position_value']

    # --- MVP Trading Logic ---
    # Signal 1: Buy (if not already holding a position)
    if signal == 1 and account['position_size'] == 0:
        shares_to_buy = account['cash'] / price
        account['position_size'] += shares_to_buy
        account['cash'] = 0
        print(f"  - EXECUTE BUY: param_id={account['param_id']}, shares={shares_to_buy:.2f}, price={price}")

    # Signal -1: Sell (if currently holding a position)
    elif signal == -1 and account['position_size'] > 0:
        cash_from_sale = account['position_size'] * price
        account['cash'] += cash_from_sale
        account['position_size'] = 0
        print(f"  - EXECUTE SELL: param_id={account['param_id']}, shares={account['position_size']:.2f}, price={price}")
    
    # Update total value one last time after trade execution
    account['position_value'] = account['position_size'] * price
    account['total_value'] = account['cash'] + account['position_value']
    
    return account

def simulate_accounts():
    """
    Main function for M7. Loads today's signals, loads yesterday's account
    states, simulates trades, and saves today's account states.
    """
    print("\nM7 - Simulating Daily Multi-Strategy Performance...")
    today_str_ymd = datetime.now().strftime('%Y-%m-%d')
    today_str = datetime.now().strftime('%Y%m%d')
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')

    # 使用版本管理器取得當前版本
    current_version = version_manager.get_current_version()
    
    # Define paths with version support
    if current_version:
        signal_dir = version_manager.get_version_path(current_version, "trading_signal")
        performance_dir = version_manager.get_version_path(current_version, "trading_performance")
    else:
        signal_dir = "trading_simulation/signal"
        performance_dir = "trading_simulation/performance"
    
    signal_path = os.path.join(signal_dir, f'M6_trade_decisions_{today_str}.csv')
    snapshot_path_yesterday = os.path.join(performance_dir, f'M7_simulation_result_{yesterday_str}.csv')
    snapshot_path_today = os.path.join(performance_dir, f'M7_simulation_result_{today_str}.csv')

    # --- Step 1: Load today's trade signals ---
    if not os.path.exists(signal_path):
        print(f"ERROR: M6 signal file not found for today: {signal_path}")
        return
    df_signal = pd.read_csv(signal_path)
    print(f"INFO: Loaded {len(df_signal)} trade signals for {today_str_ymd}.")

    # --- Step 2: Load yesterday's accounts ---
    if os.path.exists(snapshot_path_yesterday):
        accounts = load_accounts_from_snapshot(snapshot_path_yesterday)
    else:
        print("INFO: No snapshot from yesterday found. Starting with fresh accounts.")
        accounts = {}

    # --- Step 3: Update accounts based on signals ---
    all_param_ids_today = set(df_signal['param_id'].unique())
    
    for _, row in df_signal.iterrows():
        param_id = row['param_id']
        # Get existing account or create a new one
        account = accounts.get(param_id, new_account(param_id))
        # Update account with the trade signal
        updated_account = update_account(account, row)
        updated_account['last_updated'] = today_str_ymd
        accounts[param_id] = updated_account

    # --- Step 4: Carry over accounts that had no signal today ---
    # This ensures we don't lose track of strategies that were simply holding.
    existing_param_ids = set(accounts.keys())
    unseen_ids = existing_param_ids - all_param_ids_today
    if unseen_ids:
        print(f"INFO: {len(unseen_ids)} accounts had no signal today. Carrying them over.")
        # We just need to update their total value with the latest price,
        # but for MVP, we will just carry them as is. A future version
        # would need to fetch the price for their symbol to update their value.

    # --- Step 5: Save today's snapshot ---
    if not accounts:
        print("M7 - No accounts were simulated today.")
        return
    
    # 確保目錄存在
    os.makedirs(performance_dir, exist_ok=True)
        
    today_results_df = pd.DataFrame(list(accounts.values()))
    today_results_df.to_csv(snapshot_path_today, index=False)
    print(f"\nSUCCESS: M7 process complete. {len(accounts)} accounts simulated.")
    print(f"Today's performance snapshot saved to:\n{snapshot_path_today}")
    if current_version:
        print(f"📂 版本目錄: {current_version}")
    
    # Display summary
    total_asset_value = today_results_df['total_value'].sum()
    print(f"\n--- Simulation Summary ---")
    print(f"Total simulated strategies: {len(today_results_df)}")
    print(f"Total simulated asset value: ${total_asset_value:,.2f}")
    print("--------------------------")


if __name__ == '__main__':
    # Example usage for standalone testing
    simulate_accounts() 