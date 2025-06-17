import os
import pandas as pd

def main():
    mode = input('請選擇模式（in_sample/out_sample）：').strip()
    if mode not in ['in_sample', 'out_sample']:
        print('模式輸入錯誤，預設為 in_sample')
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
    user_asc = input(f'是否由小到大排序？(y/n, 預設{"y" if ascending else "n"})：').strip().lower()
    if user_asc == 'y':
        ascending = True
    elif user_asc == 'n':
        ascending = False
    top_n = input('請輸入要保留的前N名策略（預設10）：').strip()
    top_n = int(top_n) if top_n.isdigit() else 10
    df_sorted = df.sort_values(by=sort_col, ascending=ascending).head(top_n)
    out_file = os.path.join(strat_dir, f'best_strategies_{perf_file.replace("performance_", "")}')
    df_sorted.to_csv(out_file, index=False)
    print(f'已篩選出前{top_n}名最佳策略，存檔於 {out_file}')
    print('這份檔案可直接用於 M4-1 驗證區間批次訊號產生！')

if __name__ == '__main__':
    main() 