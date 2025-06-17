import os
import pandas as pd
from .m2_signal_generator_batch import generate_signals_df
from datetime import datetime

def main():
    mode = input('請選擇模式（in_sample/out_sample）：').strip()
    if mode not in ['in_sample', 'out_sample']:
        print('模式輸入錯誤，預設為 out_sample')
        mode = 'out_sample'
    strategies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'strategies', 'in_sample')
    signals_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'signals', mode)
    os.makedirs(signals_dir, exist_ok=True)
    files = [f for f in os.listdir(strategies_dir) if f.endswith('.csv') or f.endswith('.json')]
    files = [f for f in files if f.startswith('best_strategies_') or f.startswith('param_log_')]
    if not files:
        print(f'{strategies_dir} 下沒有最佳策略清單或 param_log 檔案！')
        return
    print('請選擇最佳策略清單或 param_log 檔案：')
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
    strategy_file = files[idx]
    if strategy_file.endswith('.csv'):
        df = pd.read_csv(os.path.join(strategies_dir, strategy_file))
        param_list = df.to_dict(orient='records')
        symbol = strategy_file.split('_')[-2]
    else:
        import json
        with open(os.path.join(strategies_dir, strategy_file), 'r', encoding='utf-8') as f:
            param_list = json.load(f)
        symbol = strategy_file.split('_')[-1].replace('.json', '')
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