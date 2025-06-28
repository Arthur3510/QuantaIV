import os
import pandas as pd
import numpy as np
import json
from datetime import datetime
from utils.indicator_utils import calculate_rsi, calculate_sma
from utils.db_loader import load_price_data
from utils.version_manager import version_manager

def generate_signals(symbol, start_date, end_date, strategy_type, params):
    """
    根據策略類型和參數，為單一股票產生交易訊號。
    """
    df = load_price_data(symbol, start_date, end_date)
    
    param_source = params.get('params', params)

    if strategy_type.upper() == 'RSI':
        rsi_period = param_source.get('rsi_period', 14)
        overbought = param_source.get('rsi_upper', 70)
        oversold = param_source.get('rsi_lower', 30)
        df = calculate_rsi(df, period=rsi_period)
        df['signal'] = 0
        df.loc[df['rsi'] > overbought, 'signal'] = -1
        df.loc[df['rsi'] < oversold, 'signal'] = 1

    elif strategy_type.upper() == 'CROSS':
        short_window = param_source.get('fast_period', 5)
        long_window = param_source.get('slow_period', 20)
        df = calculate_sma(df, period=short_window, col_name='short_sma')
        df = calculate_sma(df, period=long_window, col_name='long_sma')
        df['signal'] = 0
        df.loc[df['short_sma'] > df['long_sma'], 'signal'] = 1
        df.loc[df['short_sma'] < df['long_sma'], 'signal'] = -1

    else:
        raise ValueError(f"未知的策略類型: {strategy_type}")
    
    # 產生 position
    df['position'] = df['signal'].replace(0, np.nan).ffill().fillna(0)
    return df

def generate_signals_df(params, strategy_type, start_date, end_date):
    symbol = params.get('symbol', 'AAPL')
    param_id = params.get('param_id', params.get('id', 'unknown'))
    try:
        # 直接呼叫新的 generate_signals 函數
        signals_df = generate_signals(symbol, start_date, end_date, strategy_type, params)
        signals_df['param_id'] = param_id
        return signals_df
    except Exception as e:
        print(f"[錯誤] 產生 param_id={param_id} 訊號失敗: {e}")
        return None

def main():
    print("【M2-1 訊號生成模組】")
    
    # 檢查並取得當前版本
    current_version = version_manager.get_current_version()
    if not current_version:
        print("⚠️ 沒有當前版本，請先執行 M1 建立版本")
        return
    
    print(f"使用版本: {current_version}")
    
    # 使用版本化的目錄路徑
    strategies_dir = version_manager.get_version_path(current_version, "in_sample_params")
    signals_dir = version_manager.get_version_path(current_version, "trading_signal")
    
    # 建立訊號目錄
    os.makedirs(signals_dir, exist_ok=True)
    
    # 檢查參數檔案
    if not os.path.exists(strategies_dir):
        print(f"版本目錄不存在: {strategies_dir}")
        return
    
    files = [f for f in os.listdir(strategies_dir) if f.startswith('param_log_') and f.endswith('.json')]
    if not files:
        print(f'{strategies_dir} 目錄下沒有 param_log_*.json 檔案！')
        return
    
    print('請選擇要批次產生 signals 的 param_log 檔案（可輸入多個編號，用逗號分隔）：')
    for idx, f in enumerate(files, 1):
        print(f'{idx}. {f}')
    
    choice_input = input('請輸入檔案編號：').strip()
    
    # 處理多個檔案編號
    try:
        choice_indices = [int(x.strip()) - 1 for x in choice_input.split(',')]
        selected_files = []
        for idx in choice_indices:
            if 0 <= idx < len(files):
                selected_files.append(files[idx])
            else:
                print(f'警告：檔案編號 {idx + 1} 超出範圍，已忽略')
        
        if not selected_files:
            print('沒有選擇任何有效檔案，結束。')
            return
            
    except Exception:
        print('輸入錯誤，結束。')
        return
    
    # 取得日期範圍（所有檔案使用相同的日期範圍）
    start_date = input('請輸入起始日期（YYYY-MM-DD）：').strip()
    end_date = input('請輸入結束日期（YYYY-MM-DD）：').strip()
    
    # 處理每個選中的檔案
    for param_file in selected_files:
        strategy_type = param_file.split('_')[2] # 從檔名解析策略類型
        symbol = param_file.split('_')[-1].replace('.json', '')
        
        print(f"\n處理策略: {strategy_type}, 股票: {symbol}")
        
        with open(os.path.join(strategies_dir, param_file), 'r', encoding='utf-8') as f:
            param_list = json.load(f)
        
        print(f"開始為 {len(param_list)} 組參數產生訊號...")
        
        all_signals = []
        for i, param in enumerate(param_list, 1):
            param['symbol'] = symbol
            # 將 start_date 和 end_date 傳遞給 generate_signals_df
            signals_df = generate_signals_df(param, strategy_type, start_date, end_date)
            if signals_df is not None:
                all_signals.append(signals_df)
            
            if i % 10 == 0:
                print(f"進度: {i}/{len(param_list)}")
        
        if not all_signals:
            print(f'沒有成功產生 {symbol} 的任何 signals！')
            continue
        
        df_all = pd.concat(all_signals, ignore_index=False)
        df_all.reset_index(inplace=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        out_file = os.path.join(signals_dir, f'{symbol}_{strategy_type}_signals_all_params_{timestamp}.csv')
        df_all.to_csv(out_file, index=False)
        
        print(f'✅ 已產生 {len(param_list)} 組 {symbol} signals')
        print(f'📁 存檔於: {out_file}')
    
    print(f'📂 版本目錄: {current_version}')

if __name__ == '__main__':
    main() 