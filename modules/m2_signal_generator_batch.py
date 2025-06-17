import os
import pandas as pd
import numpy as np
import json
from datetime import datetime
from modules.m2_signal_generator import SignalGenerator

def generate_signals_df(params):
    symbol = params.get('symbol', 'AAPL')
    start_date = params.get('start_date', '2020-01-01')
    end_date = params.get('end_date', '2023-12-31')
    param_id = params.get('param_id', params.get('id', 'unknown'))
    sg = SignalGenerator()
    try:
        signals_df = sg.generate_signals(symbol, start_date, end_date, 'RSI', params, save_file=False)
        signals_df['param_id'] = param_id
        return signals_df
    except Exception as e:
        print(f"[錯誤] 產生 param_id={param_id} 訊號失敗: {e}")
        return None

def main():
    mode = 'in_sample'
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
    symbol = param_file.split('_')[-1].replace('.json', '')
    with open(os.path.join(strategies_dir, param_file), 'r', encoding='utf-8') as f:
        param_list = json.load(f)
    start_date = input('請輸入起始日期（YYYY-MM-DD）：').strip()
    end_date = input('請輸入結束日期（YYYY-MM-DD）：').strip()
    all_signals = []
    for param in param_list:
        param['symbol'] = symbol
        param['start_date'] = start_date
        param['end_date'] = end_date
        signals_df = generate_signals_df(param)
        if signals_df is not None:
            all_signals.append(signals_df)
    if not all_signals:
        print('沒有成功產生任何 signals！')
        return
    df_all = pd.concat(all_signals, ignore_index=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_file = os.path.join(signals_dir, f'{symbol}_signals_all_params_{timestamp}.csv')
    df_all.to_csv(out_file, index=False)
    print(f'已產生 {len(all_signals)} 組 signals，存檔於 {out_file}')

if __name__ == '__main__':
    main() 