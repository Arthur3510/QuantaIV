import os
import pandas as pd
import json
import glob

def select_best_strategies(mode, copy_param_log=False):
    """
    通用策略篩選器。
    :param mode: 'in_sample' 或 'out_sample'
    :param copy_param_log: 是否複製 param_log (僅 M3 需要)
    """
    # 根據模式設定路徑
    perf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'performance', mode)
    strat_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'strategies', mode, 'best')
    os.makedirs(strat_dir, exist_ok=True)

    # 根據模式設定檔案過濾條件
    file_suffix = '_batch.csv' if mode == 'in_sample' else '_validation.csv'
    files = [f for f in os.listdir(perf_dir) if f.endswith(file_suffix)]
    if not files:
        print(f'{perf_dir} 下沒有績效報告！')
        return

    print('請選擇績效報告：')
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
    
    perf_file = files[idx]
    df = pd.read_csv(os.path.join(perf_dir, perf_file))

    # --- 篩選邏輯 ---
    print(f'可用排序欄位： {", ".join(df.columns)}')
    sort_col = input('請輸入排序欄位（如 total_return、sharpe）：').strip()
    if sort_col not in df.columns:
        print('欄位錯誤，預設用 sharpe')
        sort_col = 'sharpe'

    default_ascending = 'drawdown' in sort_col
    asc_choice = input(f'是否由大到小排序？(y/n, 預設{"n" if default_ascending else "y"})：').strip().lower()
    if asc_choice == 'y':
        ascending = False
    elif asc_choice == 'n':
        ascending = True
    else:
        ascending = default_ascending

    top_n = input('請輸入要保留的前N名策略（預設10）：').strip()
    top_n = int(top_n) if top_n.isdigit() else 10
    
    df_sorted = df.sort_values(by=sort_col, ascending=ascending).head(top_n)
    
    # 根據模式調整輸出檔名
    out_file_name = f'best_strategies_{perf_file.replace("performance_", "")}'
    if mode == 'in_sample':
        out_file_name = out_file_name.replace("_batch", "") # M3的特殊規則
        
    out_file = os.path.join(strat_dir, out_file_name)
    df_sorted.to_csv(out_file, index=False)
    print(f'已篩選出前{top_n}名最佳策略，存檔於 {out_file}')

    # --- M3 的額外邏輯：複製 param log ---
    if copy_param_log:
        print('這份檔案可直接用於 M4-1 驗證區間批次訊號產生！')
        copy_param_logs_for_best_strategies(df_sorted, perf_file)

def copy_param_logs_for_best_strategies(best_strategies_df, perf_file):
    """
    根據最佳策略清單，複製對應的 param log。
    """
    # 從績效檔名中解析出 symbol
    base_name = perf_file.replace('performance_', '').replace('_batch.csv', '')
    symbol = base_name.split('_signals_all_params_')[0]

    if best_strategies_df.empty or 'param_id' not in best_strategies_df.columns:
        print("無法從最佳策略中推斷出策略類型，請檢查績效報告欄位。")
        return
    strategy_type = best_strategies_df['param_id'].iloc[0].split('_')[0]

    all_params_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'strategies', 'in_sample', 'all_params')
    param_log_pattern = os.path.join(all_params_dir, f'param_log_{strategy_type}_{symbol}.json')
    param_log_files = glob.glob(param_log_pattern)
    
    if param_log_files:
        paramlog_src = param_log_files[0]
        paramlog_dst_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'strategies', 'out_sample', 'param_logs')
        os.makedirs(paramlog_dst_dir, exist_ok=True)
        paramlog_dst = os.path.join(paramlog_dst_dir, os.path.basename(paramlog_src))
        
        with open(paramlog_src, 'r', encoding='utf-8') as f:
            all_params = json.load(f)
            
        best_ids = set(best_strategies_df['param_id'])
        filtered_params = [p for p in all_params if p.get('id') in best_ids]
        
        with open(paramlog_dst, 'w', encoding='utf-8') as f:
            json.dump(filtered_params, f, ensure_ascii=False, indent=2)
            
        print(f'已自動複製並過濾 param log，存檔於 {paramlog_dst}')
    else:
        print(f'找不到 {symbol} 的 param log 檔案，請確認 {all_params_dir} 目錄下是否有對應的檔案！') 