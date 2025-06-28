import os
import pandas as pd
from utils.performance_utils import calculate_performance_metrics
from utils.version_manager import version_manager
from datetime import datetime

def main():
    print("【M2-2 績效計算模組】")
    
    # 檢查並取得當前版本
    current_version = version_manager.get_current_version()
    if not current_version:
        print("⚠️ 沒有當前版本，請先執行 M1 建立版本")
        return
    
    print(f"使用版本: {current_version}")
    
    # 使用版本化的目錄路徑
    signals_dir = version_manager.get_version_path(current_version, "trading_signal")
    perf_dir = version_manager.get_version_path(current_version, "trading_performance")
    
    # 建立績效目錄
    os.makedirs(perf_dir, exist_ok=True)
    
    # 檢查訊號檔案
    if not os.path.exists(signals_dir):
        print(f"版本目錄不存在: {signals_dir}")
        return
    
    # 取得檔案列表並按修改時間排序
    all_files = [f for f in os.listdir(signals_dir) if 'all_params' in f and f.endswith('.csv')]
    if not all_files:
        print(f'{signals_dir} 目錄下沒有 all_params signals 檔案！')
        return

    files_with_mtime = []
    for f in all_files:
        full_path = os.path.join(signals_dir, f)
        files_with_mtime.append((f, os.path.getmtime(full_path)))
    
    files_with_mtime.sort(key=lambda x: x[1], reverse=True)
    files = [f[0] for f in files_with_mtime]
        
    print('請選擇要批次計算績效的 signals 檔案（已按時間倒序排列，最新的在最上方）：')
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
    signal_file_path = os.path.join(signals_dir, signal_file)
    print(f"\n正在讀取檔案: {signal_file_path}")
    df = pd.read_csv(signal_file_path)

    # 檢查必要欄位
    required_cols = ['date', 'param_id', 'signal', 'close']
    if not all(col in df.columns for col in required_cols):
        print(f"檔案缺少必要欄位! 需要的欄位: {required_cols}")
        return

    # 資料預處理
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date')

    print("\n=== 開始計算所有策略的績效 ===")
    
    unique_params = df['param_id'].unique()
    print(f"找到 {len(unique_params)} 個不同的參數組合")
    
    results = []
    
    for i, param_id in enumerate(unique_params, 1):
        group = df[df['param_id'] == param_id].copy()
        perf_series = calculate_performance_metrics(group)
        perf_series['param_id'] = param_id
        results.append(perf_series)
        
        if i % 10 == 0:
            print(f"進度: {i}/{len(unique_params)}")
    
    results_df = pd.DataFrame(results)

    # 重新排列欄位，將 param_id 放到第一位
    if not results_df.empty:
        cols = ['param_id'] + [col for col in results_df.columns if col != 'param_id']
        results_df = results_df[cols]

    print("=== 績效計算完成 ===")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_file = os.path.join(perf_dir, f'performance_{signal_file.replace(".csv", "")}_batch.csv')
    
    print("\n=== 最終結果統計 ===")
    print(results_df.describe())

    results_df.to_csv(out_file, index=False)
    print(f'\n✅ 已完成 {len(results_df)} 組績效計算')
    print(f'📁 存檔於: {out_file}')
    print(f'📂 版本目錄: {current_version}')

if __name__ == '__main__':
    main() 