import os
import pandas as pd
import numpy as np

def calc_total_return(nav):
    return nav[-1] / nav[0] - 1 if len(nav) > 1 else np.nan

def calc_max_drawdown(nav):
    peak = np.maximum.accumulate(nav)
    drawdown = (nav - peak) / peak
    return drawdown.min() if len(drawdown) > 0 else np.nan

def calc_sharpe_ratio(nav, risk_free_rate=0.0, freq=252):
    returns = np.diff(nav) / nav[:-1]
    excess_ret = returns - risk_free_rate / freq
    ann_ret = np.mean(excess_ret) * freq if len(excess_ret) > 0 else np.nan
    ann_vol = np.std(excess_ret) * np.sqrt(freq) if len(excess_ret) > 0 else np.nan
    return ann_ret / ann_vol if ann_vol > 0 else np.nan

def calculate_performance(params, signals_dir):
    """根據單一參數組計算績效"""
    param_id = params.get('param_id', params.get('id', 'unknown'))
    if 'signal' not in params or 'close' not in params:
        print(f'param_id={param_id} 的參數組缺少必要欄位（signal, close）！')
        return {
            'param_id': param_id,
            'total_return': np.nan,
            'max_drawdown': np.nan,
            'sharpe': np.nan
        }
    
    position = pd.Series(params['signal']).replace(0, np.nan).ffill().fillna(0)
    first_trade_idx = position.ne(0).idxmax()
    position = position.loc[first_trade_idx:]
    close = pd.Series(params['close']).loc[first_trade_idx:]
    nav = (1 + position.shift().fillna(0) * close.pct_change()).cumprod().dropna()
    total_return = calc_total_return(nav.values)
    max_drawdown = calc_max_drawdown(nav.values)
    sharpe = calc_sharpe_ratio(nav.values)
    return {
        'param_id': param_id,
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'sharpe': sharpe
    }

def main():
    mode = 'in_sample'
    signals_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'signals', mode)
    perf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'performance', mode)
    os.makedirs(perf_dir, exist_ok=True)
    files = [f for f in os.listdir(signals_dir) if 'all_params' in f and f.endswith('.csv')]
    if not files:
        print('signals 目錄下沒有 all_params signals 檔案！')
        return
    print('請選擇要批次計算績效的 signals 檔案：')
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
    signal_file = files[idx]
    df = pd.read_csv(os.path.join(signals_dir, signal_file))
    if 'param_id' not in df.columns or 'signal' not in df.columns or 'close' not in df.columns:
        print('signals 檔案缺少必要欄位（param_id, signal, close）！')
        return
    results = []
    for param_id, group in df.groupby('param_id'):
        position = group['signal'].replace(0, np.nan).ffill().fillna(0)
        first_trade_idx = position.ne(0).idxmax()
        position = position.loc[first_trade_idx:]
        close = group['close'].loc[first_trade_idx:]
        nav = (1 + position.shift().fillna(0) * close.pct_change()).cumprod().dropna()
        total_return = calc_total_return(nav.values)
        max_drawdown = calc_max_drawdown(nav.values)
        sharpe = calc_sharpe_ratio(nav.values)
        results.append({
            'param_id': param_id,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'sharpe': sharpe
        })
    out_file = os.path.join(perf_dir, f'performance_{signal_file.replace(".csv", "")}_batch.csv')
    pd.DataFrame(results).to_csv(out_file, index=False)
    print(f'已完成 {len(results)} 組績效計算，存檔於 {out_file}')

if __name__ == '__main__':
    main() 