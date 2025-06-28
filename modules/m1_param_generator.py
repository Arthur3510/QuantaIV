import sys
import os
import time
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.param_generator import generate_param_combinations
from utils.file_saver import save_json
from utils.version_manager import version_manager
from datetime import datetime

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

def generate_param_id_with_timestamp(strategy_type: str, param: dict) -> str:
    """生成帶時間戳的param_id"""
    import hashlib
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    param_hash = hashlib.md5(str(param).encode()).hexdigest()[:8]
    return f"{strategy_type}_{param_hash}_{timestamp}"

def worker(symbol, strategy_type, param_ranges, n_params, delay):
    print(f"[INFO] 為 {symbol} 產生 {strategy_type} 參數組合...")
    param_list, param_map = generate_param_combinations(strategy_type, param_ranges)
    if n_params > 0 and n_params < len(param_list):
        param_list = param_list[:n_params]
        param_map = {p['param_id']: p for p in param_list}
    os.makedirs('strategies', exist_ok=True)
    save_json(param_list, f'strategies/param_log_{strategy_type}_{symbol}.json')
    save_json(param_map, f'strategies/signal_param_map_{strategy_type}_{symbol}.json')
    print(f"⮑ 產出 {len(param_list)} 組 param_id + param_dict")
    if delay > 0:
        print(f"⏳ 暫停 {delay} 秒...")
        time.sleep(delay)
    return symbol

def generate_rsi_params(n=100):
    """產生 RSI 策略參數"""
    params = []
    for i in range(n):
        param = {
            'rsi_period': random.randint(5, 30),
            'rsi_upper': random.uniform(60, 90),
            'rsi_lower': random.uniform(10, 40),
            'stop_loss': random.uniform(0.01, 0.1),
            'take_profit': random.uniform(0.02, 0.2)
        }
        # 生成帶時間戳的param_id
        param['id'] = generate_param_id_with_timestamp('RSI', param)
        params.append(param)
    return params

def generate_cross_params(n=100):
    """產生均線交叉策略參數"""
    params = []
    for i in range(n):
        param = {
            'fast_period': random.randint(5, 20),
            'slow_period': random.randint(21, 60),
            'stop_loss': random.uniform(0.01, 0.1),
            'take_profit': random.uniform(0.02, 0.2)
        }
        # 生成帶時間戳的param_id
        param['id'] = generate_param_id_with_timestamp('CROSS', param)
        params.append(param)
    return params

def save_params(symbol, strategy_type, params, mode='in_sample'):
    """儲存參數到指定模式資料夾"""
    # 取得當前版本目錄
    current_version = version_manager.get_current_version()
    if not current_version:
        print("⚠️ 沒有當前版本，建立新版本...")
        current_version = version_manager.create_new_version()
    
    # 使用版本化的目錄路徑
    if mode == 'in_sample':
        strategies_dir = version_manager.get_version_path(current_version, "in_sample_params")
    else:
        strategies_dir = version_manager.get_version_path(current_version, "out_sample_params")
    
    os.makedirs(strategies_dir, exist_ok=True)
    
    # 儲存參數列表
    param_log_file = os.path.join(strategies_dir, f'param_log_{strategy_type}_{symbol}.json')
    with open(param_log_file, 'w', encoding='utf-8') as f:
        json.dump(params, f, indent=2, ensure_ascii=False)
    
    # 儲存參數映射
    signal_param_map = {param['id']: param for param in params}
    map_file = os.path.join(strategies_dir, f'signal_param_map_{strategy_type}_{symbol}.json')
    with open(map_file, 'w', encoding='utf-8') as f:
        json.dump(signal_param_map, f, indent=2, ensure_ascii=False)
    
    print(f"📁 參數已儲存到版本目錄: {current_version}")
    return param_log_file, map_file

def main():
    print("【策略參數產生 M1】")
    
    # 檢查並建立新版本
    current_version = version_manager.get_current_version()
    if not current_version:
        print("建立新版本...")
        current_version = version_manager.create_new_version()
    else:
        print(f"使用當前版本: {current_version}")
    
    symbol_input = input("請輸入股票代碼（例如 AAPL,TSLA）：\n> ").strip().upper()
    if not symbol_input:
        print("股票代碼不能為空！")
        return
    
    # 處理多個股票代碼
    symbols = [s.strip() for s in symbol_input.split(',')]
    
    mode = 'in_sample' # M1 固定為 in_sample 模式
    
    print("請選擇策略類型：")
    print("1. RSI")
    print("2. CROSS")
    strategy_choice = input("> ").strip()
    
    if strategy_choice == "1":
        strategy_type = "RSI"
        generate_func = generate_rsi_params
    elif strategy_choice == "2":
        strategy_type = "CROSS"
        generate_func = generate_cross_params
    else:
        print("輸入錯誤，將自動切換為 RSI")
        strategy_type = "RSI"
        generate_func = generate_rsi_params
    
    n_params = input("請輸入欲產生幾組策略參數（預設=100）：\n> ").strip()
    n_params = int(n_params) if n_params.isdigit() else 100
    
    max_workers = input("請輸入同時產生上限 max_workers（預設=3）：\n> ").strip()
    max_workers = int(max_workers) if max_workers.isdigit() else 3
    
    delay = input("請輸入每支股票產生後延遲秒數（預設=1）：\n> ").strip()
    delay = int(delay) if delay.isdigit() else 1
    
    print("\n3️⃣ 使用者執行過程與結束畫面")
    print("⏳ 執行中\n")
    
    # 為每個股票生成參數
    for symbol in symbols:
        print(f"[INFO] 為 {symbol} 產生 {strategy_type} 參數組合...")
        params = generate_func(n_params)
        print(f"⮑ 產出 {len(params)} 組 param_id + param_dict")
        
        print(f"⏳ 暫停 {delay} 秒...")
        time.sleep(delay)
        
        param_log_file, map_file = save_params(symbol, strategy_type, params, mode)
        print(f"✅ {symbol} 產生完成\n")
    
    print("📁 產出完成：")
    for symbol in symbols:
        print(f"✔️ param_log_{strategy_type}_{symbol}.json")
        print(f"✔️ signal_param_map_{strategy_type}_{symbol}.json")
    print(f"📂 版本目錄: {current_version}")

if __name__ == "__main__":
    main() 