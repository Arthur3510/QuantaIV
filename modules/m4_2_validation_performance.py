import os
import pandas as pd
from .m2_performance_from_signals_batch import calculate_performance

def main():
    signals_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'signals', 'out_sample')
    perf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'performance', 'out_sample')
    os.makedirs(perf_dir, exist_ok=True)
    files = [f for f in os.listdir(signals_dir) if f.endswith('.csv')]
    if not files:
        print(f'{signals_dir} 下沒有訊號檔案！')
        return
    print('請選擇訊號檔案：')
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
    results = []
    for _, row in df.iterrows():
        params = row.to_dict()
        perf = calculate_performance(params, signals_dir)
        results.append(perf)
    out_file = os.path.join(perf_dir, f'performance_{signal_file.replace(".csv", "")}_validation.csv')
    pd.DataFrame(results).to_csv(out_file, index=False)
    print(f'已完成 {len(results)} 組績效計算，存檔於 {out_file}')

if __name__ == '__main__':
    main() 