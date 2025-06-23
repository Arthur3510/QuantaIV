import os
import pandas as pd
import numpy as np
import json
from datetime import datetime
from utils.indicator_utils import calculate_rsi, calculate_sma
from utils.db_loader import load_price_data

def generate_signals(symbol, start_date, end_date, strategy_type, params):
    """
    根據策略類型和參數，為單一股票產生交易訊號。
    """
    df = load_price_data(symbol, start_date, end_date)
    
    param_source = params.get('params', params)

    if strategy_type.upper() == 'RSI':
        rsi_period = param_source.get('rsi_period', 14)
        overbought = param_source.get('rsi_upper', 70)
        oversold = param_source.get('rsi_lower', 30)
        df = calculate_rsi(df, period=rsi_period)
        df['signal'] = 0
        df.loc[df['rsi'] > overbought, 'signal'] = -1
        df.loc[df['rsi'] < oversold, 'signal'] = 1

    elif strategy_type.upper() == 'CROSS':
        short_window = param_source.get('fast_period', 5)
        long_window = param_source.get('slow_period', 20)
        df = calculate_sma(df, period=short_window, col_name='short_sma')
        df = calculate_sma(df, period=long_window, col_name='long_sma')
        df['signal'] = 0
        df.loc[df['short_sma'] > df['long_sma'], 'signal'] = 1
        df.loc[df['short_sma'] < df['long_sma'], 'signal'] = -1

    else:
        raise ValueError(f"未知的策略類型: {strategy_type}")
    
    # 產生 position
    df['position'] = df['signal'].replace(0, np.nan).ffill().fillna(0)
    return df

def generate_signals_df(params, strategy_type, start_date, end_date):
    symbol = params.get('symbol', 'AAPL')
    param_id = params.get('param_id', params.get('id', 'unknown'))
    try:
        # 直接呼叫新的 generate_signals 函數
        signals_df = generate_signals(symbol, start_date, end_date, strategy_type, params)
        signals_df['param_id'] = param_id
        return signals_df
    except Exception as e:
        print(f"[錯誤] 產生 param_id={param_id} 訊號失敗: {e}")
        return None

def main():
    mode = 'in_sample'  # M2-1 固定為 in_sample 模式
    signals_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'signals', mode)
    os.makedirs(signals_dir, exist_ok=True)
    strategies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'strategies', mode, 'all_params')
    files = [f for f in os.listdir(strategies_dir) if f.startswith('param_log_') and f.endswith('.json')]
    if not files:
        print(f'{strategies_dir} 目錄下沒有 param_log_*.json 檔案！')
        return
    print('請選擇要批次產生 signals 的 param_log 檔案：')
    for idx, f in enumerate(files, 1):
        print(f'{idx}. {f}')
    choice = input('請輸入檔案編號：').strip()
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(files):
            raise ValueError
    except Exception:
        print('輸入錯誤，結束。')
        return
    param_file = files[idx]
    strategy_type = param_file.split('_')[2] # 從檔名解析策略類型
    symbol = param_file.split('_')[-1].replace('.json', '')
    with open(os.path.join(strategies_dir, param_file), 'r', encoding='utf-8') as f:
        param_list = json.load(f)
    start_date = input('請輸入起始日期（YYYY-MM-DD）：').strip()
    end_date = input('請輸入結束日期（YYYY-MM-DD）：').strip()
    all_signals = []
    for param in param_list:
        param['symbol'] = symbol
        # 將 start_date 和 end_date 傳遞給 generate_signals_df
        signals_df = generate_signals_df(param, strategy_type, start_date, end_date)
        if signals_df is not None:
            all_signals.append(signals_df)
    if not all_signals:
        print('沒有成功產生任何 signals！')
        return
    df_all = pd.concat(all_signals, ignore_index=False)
    df_all.reset_index(inplace=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_file = os.path.join(signals_dir, f'{symbol}_{strategy_type}_signals_all_params_{timestamp}.csv')
    df_all.to_csv(out_file, index=False)
    print(f'已產生 {len(param_list)} 組 signals，存檔於 {out_file}')

if __name__ == '__main__':
    main() 