import os
import pandas as pd

def main():
    """
    M5 策略挑選模組 (樣本外)
    - 從 performance/out_sample 中挑選績效報告
    - 篩選出最終的最佳策略
    - 將結果存到 strategies/out_sample/best
    """
    mode = 'out_sample'
    
    # 根據模式設定路徑
    perf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'performance', mode)
    strat_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'strategies', mode, 'best')
    os.makedirs(strat_dir, exist_ok=True)

    # 根據模式設定檔案過濾條件
    file_suffix = '_validation.csv'
    all_files = [f for f in os.listdir(perf_dir) if f.endswith(file_suffix)]
    if not all_files:
        print(f'{perf_dir} 下沒有績效報告！')
        return

    # 按時間排序
    files_with_mtime = []
    for f in all_files:
        full_path = os.path.join(perf_dir, f)
        files_with_mtime.append((f, os.path.getmtime(full_path)))
    files_with_mtime.sort(key=lambda x: x[1], reverse=True)
    files = [f[0] for f in files_with_mtime]

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
    
    # 輸出檔名邏輯
    out_file_name = f'best_strategies_{perf_file.replace("performance_", "")}'
    out_file = os.path.join(strat_dir, out_file_name)
    df_sorted.to_csv(out_file, index=False)
    print(f'已篩選出前{top_n}名最佳策略，存檔於 {out_file}')

if __name__ == '__main__':
    main() 