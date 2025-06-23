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

    # 更新檔案列表邏輯以匹配新的需求
    all_files = [f for f in os.listdir(perf_dir) if f.startswith('performance_') and f.endswith('_batch.csv')]
    if not all_files:
        print(f'\'{perf_dir}\' 目錄下沒有績效報告！')
        return

    files_with_mtime = []
    for f in all_files:
        full_path = os.path.join(perf_dir, f)
        files_with_mtime.append((f, os.path.getmtime(full_path)))
    
    files_with_mtime.sort(key=lambda x: x[1], reverse=True)
    files = [f[0] for f in files_with_mtime]

    print('請選擇績效報告（已按時間倒序排列，最新的在最上方）：')
    for idx, f in enumerate(files, 1):
        print(f'{idx}. {f}')
    
    try:
        choice = input('請輸入檔案編號：').strip()
        idx = int(choice) - 1
        if not (0 <= idx < len(files)):
            raise ValueError("索引超出範圍")
    except (ValueError, IndexError):
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
    ascending = False
    if sort_col in ['total_return', 'sharpe']:
        ascending = False
    elif sort_col == 'max_drawdown':
        ascending = True
        
    user_desc = input(f'是否由大到小排序？(y/n, 預設{"n" if ascending else "y"})：').strip().lower()
    if user_desc == 'y':
        ascending = False
    elif user_desc == 'n':
        ascending = True
        
    top_n = input('請輸入要保留的前N名策略（預設10）：').strip()
    top_n = int(top_n) if top_n.isdigit() else 10
    
    df_sorted = df.sort_values(by=sort_col, ascending=ascending).head(top_n)
    
    out_file = os.path.join(strat_dir, f'best_strategies_{perf_file.replace("performance_", "")}')
    df_sorted.to_csv(out_file, index=False)
    print(f'已篩選出前{top_n}名最佳策略，存檔於 {out_file}')

    # === 新增：自動複製 param log ===
    # 從最佳策略的 param_id 中推斷出 strategy_type (最可靠)
    if not df_sorted.empty and 'param_id' in df_sorted.columns:
        strategy_type = df_sorted['param_id'].iloc[0].split('_')[0]
    else:
        print("無法從最佳策略中推斷出策略類型，請檢查績效報告欄位。")
        return
        
    # 從績效檔名中，穩健地解析出 symbol
    base_name = perf_file.replace('performance_', '').replace(f'_{strategy_type}_signals_all_params', '').replace('_batch.csv', '')
    # 找最後一個時間戳前的部分
    symbol = '_'.join(base_name.split('_')[:-2])


    all_params_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'strategies', 'in_sample', 'all_params')
    
    # 搜尋所有符合 param_log_{strategy_type}_{symbol}.json 的檔案
    # 注意：這裡的檔名解析是 M1 和 M2-1 的約定
    param_log_filename = f'param_log_{strategy_type}_{symbol}.json'
    paramlog_src = os.path.join(all_params_dir, param_log_filename)

    if os.path.exists(paramlog_src):
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
        print('這份檔案可直接用於 M4-1 驗證區間批次訊號產生！')
    else:
        print(f'找不到對應的 param log 檔案: {paramlog_src}')

if __name__ == '__main__':
    main() 