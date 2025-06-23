import os
import pandas as pd
import numpy as np

def calculate_performance_metrics(group):
    """計算單一策略的績效指標"""
    result = {
        'param_id': group['param_id'].iloc[0],
        'total_return': 0.0,
        'max_drawdown': 0.0,
        'sharpe': 0.0
    }
    
    print(f"\n=== 開始計算 {result['param_id']} 的績效 ===")
    print(f"資料筆數: {len(group)}")
    
    # 計算持倉部位
    position = group['signal'].replace(0, np.nan).ffill().fillna(0)
    
    # 輸出訊號統計
    print(f"Signal 分布:\n{group['signal'].value_counts()}")
    print(f"Position 分布:\n{position.value_counts()}")
    
    # 找到第一個交易訊號的位置
    first_trade_idx = position[position != 0].index[0] if (position != 0).any() else position.index[-1]
    print(f"第一個交易訊號位置: {first_trade_idx}")
    
    # 從第一個交易訊號開始計算
    position = position.loc[first_trade_idx:]
    close = group['close'].loc[first_trade_idx:]
    
    # 計算每日報酬率和淨值
    daily_returns = position.shift().fillna(0) * close.pct_change().fillna(0)
    nav = (1 + daily_returns).cumprod()
    
    # 輸出報酬率統計
    print(f"每日報酬率統計:\n{daily_returns.describe()}")
    print(f"起始淨值: {nav.iloc[0]}")
    print(f"結束淨值: {nav.iloc[-1]}")
    
    # 計算總報酬率
    result['total_return'] = nav.iloc[-1] - 1 if len(nav) > 1 else 0.0
    print(f"總報酬率: {result['total_return']:.4f}")
    
    # 計算最大回撤
    peak = nav.expanding().max()
    drawdown = (nav - peak) / peak
    result['max_drawdown'] = drawdown.min() if len(drawdown) > 0 else 0.0
    print(f"最大回撤: {result['max_drawdown']:.4f}")
    
    # 計算夏普比率
    if len(daily_returns) > 1:
        excess_ret = daily_returns - 0.0/252  # 假設無風險利率為 0
        ann_ret = np.mean(excess_ret) * 252
        ann_vol = np.std(excess_ret) * np.sqrt(252)
        result['sharpe'] = ann_ret / ann_vol if ann_vol > 0 else 0.0
        print(f"年化報酬率: {ann_ret:.4f}")
        print(f"年化波動率: {ann_vol:.4f}")
        print(f"夏普比率: {result['sharpe']:.4f}")
    
    print("=== 績效計算完成 ===\n")
    return result

def main():
    signals_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'signals', 'out_sample')
    perf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'performance', 'out_sample')
    os.makedirs(perf_dir, exist_ok=True)
    
    # 自動尋找最新的 signals 檔案
    files = [os.path.join(signals_dir, f) for f in os.listdir(signals_dir) if f.endswith('.csv')]
    if not files:
        print('signals/out_sample 目錄下沒有 signals 檔案！')
        return
        
    signal_file_path = max(files, key=os.path.getctime)
    signal_file_name = os.path.basename(signal_file_path)
    print(f"自動選擇最新的訊號檔案: {signal_file_name}")

    df = pd.read_csv(signal_file_path)
    
    if 'param_id' not in df.columns or 'signal' not in df.columns or 'close' not in df.columns:
        print('signals 檔案缺少必要欄位（param_id, signal, close）！')
        return
    
    # 輸出載入的數據基本資訊
    print(f"\n=== 數據基本資訊 ===")
    print(f"總資料筆數: {len(df)}")
    print(f"欄位: {df.columns.tolist()}")
    print(f"param_id 分布:\n{df['param_id'].value_counts()}")
    print(f"signal 值域: [{df['signal'].min()}, {df['signal'].max()}]")
    print(f"close 價格範圍: [{df['close'].min():.2f}, {df['close'].max():.2f}]")
    
    # 取得所有唯一的 param_id
    unique_params = df['param_id'].unique()
    print(f"\n找到 {len(unique_params)} 個不同的參數組合")
    
    results = []
    
    # 對每個參數計算績效
    for param_id in unique_params:
        print(f"\n處理參數 {param_id}")
        group = df[df['param_id'] == param_id].copy()
        result = calculate_performance_metrics(group)
        results.append(result)
    
    # 儲存結果
    out_file = os.path.join(perf_dir, f'performance_{signal_file_name}')
    results_df = pd.DataFrame(results)
    
    # 輸出最終結果統計
    print("\n=== 最終結果統計 ===")
    print(results_df.describe())
    
    results_df.to_csv(out_file, index=False)
    print(f'\n已完成 {len(results)} 組績效計算，存檔於 {out_file}')

if __name__ == '__main__':
    main() 