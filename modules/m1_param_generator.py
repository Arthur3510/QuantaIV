import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.param_generator import generate_param_combinations
from utils.file_saver import save_json

def get_strategy_type():
    strategies = ["RSI", "CROSS"]  # 可擴充
    print("請選擇策略類型：")
    for idx, s in enumerate(strategies, 1):
        print(f"{idx}. {s}")
    choice = input("> ").strip()
    try:
        idx = int(choice)
        if 1 <= idx <= len(strategies):
            return strategies[idx-1]
    except Exception:
        pass
    print(f"輸入錯誤，將自動切換為 {strategies[0]}")
    return strategies[0]

def worker(symbol, strategy_type, param_ranges, n_params, delay):
    print(f"[INFO] 為 {symbol} 產生 {strategy_type} 參數組合...")
    param_list, param_map = generate_param_combinations(strategy_type, param_ranges)
    if n_params > 0 and n_params < len(param_list):
        param_list = param_list[:n_params]
        param_map = {p['param_id']: p for p in param_list}
    os.makedirs('signals', exist_ok=True)
    save_json(param_list, f'signals/param_log_{strategy_type}_{symbol}.json')
    save_json(param_map, f'signals/signal_param_map_{strategy_type}_{symbol}.json')
    print(f"⮑ 產出 {len(param_list)} 組 param_id + param_dict")
    if delay > 0:
        print(f"⏳ 暫停 {delay} 秒...")
        time.sleep(delay)
    return symbol

def main():
    print("【策略參數產生 M1】")
    symbols = input("請輸入股票代碼（例如 AAPL,TSLA）：\n> ")
    symbol_list = list({s.strip().upper() for s in symbols.split(',') if s.strip()})
    if not symbol_list:
        print("未輸入有效股票代碼，結束。")
        return
    strategy_type = get_strategy_type()
    n_params = input("請輸入欲產生幾組策略參數（預設=100）：\n> ").strip()
    n_params = int(n_params) if n_params.isdigit() else 100
    max_workers = input("請輸入同時產生上限 max_workers（預設=3）：\n> ").strip()
    max_workers = int(max_workers) if max_workers.isdigit() else 3
    delay = input("請輸入每支股票產生後延遲秒數（預設=1）：\n> ").strip()
    delay = int(delay) if delay.isdigit() else 1
    # 參數範圍可根據策略擴充
    param_ranges_dict = {
        "RSI": {
            "period": list(range(5, 31)),
            "overbought": [70, 80],
            "oversold": [20, 30]
        },
        "CROSS": {
            "fast": list(range(5, 21)),
            "slow": list(range(20, 61)),
            "signal": [0, 1]  # 0: golden cross, 1: death cross
        }
    }
    param_ranges = param_ranges_dict[strategy_type]
    print("\n3️⃣ 使用者執行過程與結束畫面\n⏳ 執行中\n")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, symbol, strategy_type, param_ranges, n_params, delay) for symbol in symbol_list]
        for future in as_completed(futures):
            symbol = future.result()
            print(f"✅ {symbol} 產生完成\n")
    print("📁 產出完成：")
    for symbol in symbol_list:
        print(f"✔️ param_log_{strategy_type}_{symbol}.json")
        print(f"✔️ signal_param_map_{strategy_type}_{symbol}.json")
    print("\n全部結束！")

if __name__ == "__main__":
    main() 