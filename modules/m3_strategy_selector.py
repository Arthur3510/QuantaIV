import os
import pandas as pd
import json
import glob

def main():
    # 移除模式選擇，直接使用 in_sample
    mode = 'in_sample'
    perf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'performance', mode)
    strat_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'strategies', mode, 'best')
    os.makedirs(strat_dir, exist_ok=True)
    files = [f for f in os.listdir(perf_dir) if f.endswith('_batch.csv')]
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
    print('可用排序欄位：', ', '.join(df.columns))
    sort_col = input('請輸入排序欄位（如 total_return、sharpe）：').strip()
    if sort_col not in df.columns:
        print('欄位錯誤，預設用 sharpe')
        sort_col = 'sharpe'
    # 預設排序方向
    if sort_col in ['total_return', 'sharpe']:
        ascending = False
    elif sort_col == 'max_drawdown':
        ascending = True
    else:
        ascending = False
    user_desc = input(f'是否由大到小排序？(y/n, 預設{"y" if not ascending else "n"})：').strip().lower()
    if user_desc == 'y' or user_desc == '':
        ascending = False
    elif user_desc == 'n':
        ascending = True
    top_n = input('請輸入要保留的前N名策略（預設10）：').strip()
    top_n = int(top_n) if top_n.isdigit() else 10
    df_sorted = df.sort_values(by=sort_col, ascending=ascending).head(top_n)
    out_file = os.path.join(strat_dir, f'best_strategies_{perf_file.replace("performance_", "")}')
    df_sorted.to_csv(out_file, index=False)
    print(f'已篩選出前{top_n}名最佳策略，存檔於 {out_file}')
    print('這份檔案可直接用於 M4-1 驗證區間批次訊號產生！')

    # === 新增：自動複製 param log ===
    # 取得 symbol
    symbol = perf_file.split('_')[1]  # e.g. performance_MSFT_signals_all_params_xxx.csv
    all_params_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'strategies', 'in_sample', 'all_params')
    # 搜尋所有符合 param_log_*_{symbol}.json 的檔案
    param_log_pattern = os.path.join(all_params_dir, f'param_log_*_{symbol}.json')
    param_log_files = glob.glob(param_log_pattern)
    
    if param_log_files:
        paramlog_src = param_log_files[0]  # 使用找到的第一個檔案
        paramlog_dst_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'strategies', 'out_sample', 'param_logs')
        os.makedirs(paramlog_dst_dir, exist_ok=True)
        # 保持原始檔名
        paramlog_dst = os.path.join(paramlog_dst_dir, os.path.basename(paramlog_src))
        
        # 讀取原始 param log
        with open(paramlog_src, 'r', encoding='utf-8') as f:
            all_params = json.load(f)
        # 只保留 best_strategies 裡的 param_id
        best_ids = set(df_sorted['param_id'])
        filtered_params = [p for p in all_params if p.get('id') in best_ids]
        with open(paramlog_dst, 'w', encoding='utf-8') as f:
            json.dump(filtered_params, f, ensure_ascii=False, indent=2)
        print(f'已自動複製並過濾 param log，存檔於 {paramlog_dst}')
    else:
        print(f'找不到 {symbol} 的 param log 檔案，請確認 {all_params_dir} 目錄下是否有對應的檔案！')

if __name__ == '__main__':
    main() 