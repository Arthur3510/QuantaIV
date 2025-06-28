import os
import pandas as pd
from .m2_signal_generator_batch import generate_signals_df
from datetime import datetime
import json
from utils.version_manager import version_manager

def main():
    print("【M4-1 樣本外訊號生成模組】")
    
    # 檢查並取得當前版本
    current_version = version_manager.get_current_version()
    if not current_version:
        print("⚠️ 沒有當前版本，請先執行 M1 建立版本")
        return
    
    print(f"使用版本: {current_version}")
    
    # 使用版本化的目錄路徑
    strategies_dir = version_manager.get_version_path(current_version, "in_sample_best")
    param_logs_dir = version_manager.get_version_path(current_version, "out_sample_params")
    signals_dir = version_manager.get_version_path(current_version, "trading_signal")
    
    # 建立訊號目錄
    os.makedirs(signals_dir, exist_ok=True)
    
    # 檢查最佳策略檔案
    if not os.path.exists(strategies_dir):
        print(f"版本目錄不存在: {strategies_dir}")
        return
    
    # 先找最佳策略清單
    strategy_files = [f for f in os.listdir(strategies_dir) if f.startswith('best_strategies_') and f.endswith('.csv')]
    if not strategy_files:
        print(f'{strategies_dir} 下沒有最佳策略清單！')
        return
    
    print('請選擇最佳策略清單：')
    for idx, f in enumerate(strategy_files, 1):
        print(f'{idx}. {f}')
    
    choice = input('請輸入檔案編號：').strip()
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(strategy_files):
            raise ValueError
    except Exception:
        print('輸入錯誤，結束。')
        return
        
    strategy_file = strategy_files[idx]
    
    # 讀取最佳策略清單以推斷策略類型
    df_strategies = pd.read_csv(os.path.join(strategies_dir, strategy_file))
    
    if df_strategies.empty or 'param_id' not in df_strategies.columns:
        print("無法從最佳策略中推斷出策略類型，請檢查檔案內容。")
        return
    strategy_type = df_strategies['param_id'].iloc[0].split('_')[0]

    # 從檔名穩健地解析出 symbol
    base_name = strategy_file.replace('best_strategies_', '').replace('_batch.csv', '')
    temp_name = base_name.split(f'_{strategy_type}_signals_all_params_')[0]
    symbol = temp_name
    
    print(f"處理策略: {strategy_type}, 股票: {symbol}")
    
    # 精準定位唯一的 param_log 檔案
    param_log_file = f'param_log_{strategy_type}_{symbol}.json'
    param_log_path = os.path.join(param_logs_dir, param_log_file)
    
    if not os.path.exists(param_log_path):
        print(f'❌ 找不到對應的參數檔案：{param_log_path}')
        return
        
    # 讀取已經被 M3 過濾好的參數檔案
    with open(param_log_path, 'r', encoding='utf-8') as f:
            param_list = json.load(f)
    
    start_date = input('請輸入起始日期（YYYY-MM-DD）：').strip()
    end_date = input('請輸入結束日期（YYYY-MM-DD）：').strip()
    
    all_signals = []
    print(f'開始產生 {len(param_list)} 組參數的訊號...')
    
    for i, param in enumerate(param_list, 1):
        print(f'處理參數 {param["id"]}... ({i}/{len(param_list)})')
        
        # 將 symbol, date, 和 param_id 加入到要傳遞的參數字典中
        pass_params = param.copy()
        pass_params['symbol'] = symbol
        pass_params['start_date'] = start_date
        pass_params['end_date'] = end_date
        pass_params['param_id'] = param['id']

        signals_df = generate_signals_df(pass_params, strategy_type, start_date, end_date)

        if signals_df is not None:
            all_signals.append(signals_df)
            print(f'✅ 完成參數 {param["id"]} 的訊號產生')
    
    if not all_signals:
        print('❌ 沒有成功產生任何 signals！')
        return
        
    df_all = pd.concat(all_signals, ignore_index=False)
    df_all.reset_index(inplace=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_file = os.path.join(signals_dir, f'{symbol}_{strategy_type}_signals_all_params_{timestamp}_validation.csv')
    df_all.to_csv(out_file, index=False)
    
    print(f'✅ 已產生 {len(all_signals)} 組 signals')
    print(f'📁 存檔於: {out_file}')
    print(f'📂 版本目錄: {current_version}')

if __name__ == '__main__':
    main() 