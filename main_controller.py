import os
import sys
import importlib
from modules.m0_data_loader import download_stock_data, load_stock_data
from modules.m1_param_generator import main as m1_main
from modules.m2_signal_generator_batch import main as m2_signal_batch_main
from modules.m2_performance_from_signals_batch import main as m2_perf_batch_main
from modules.m3_strategy_selector import main as m3_main
from modules.m4_1_validation_signal_generator import main as m4_1_main
# We will dynamically import and reload m4_2
# from modules.m4_2_validation_performance import main as m4_2_main 
from modules.m5_validation_strategy_selector import main as m5_main
from modules.m6_multi_strategy_signal_generator import generate_trade_signals
from modules.m7_multi_account_simulator import simulate_accounts

def main():
    while True:
        print("\n=== QuantaIV 主控選單 ===")
        print("\n--- 1. 策略回測與驗證 (M0-M5) ---")
        print("1. M0 - 資料載入模組")
        print("2. M1 - 參數生成模組")
        print("3. M2 - 樣本內(in-sample)回測 (訊號+績效)")
        print("4. M3 - 樣本內(in-sample)策略挑選")
        print("5. M4/M5 - 樣本外(out-sample)驗證 (訊號+績效+挑選)")
        print("\n--- 2. 模擬交易 (M6-M7) ---")
        print("6. M6 - 產生模擬交易訊號")
        print("7. M7 - 模擬每日績效")
        print("\n--- 0. 系統 ---")
        print("0. 離開")
        
        choice = input("請選擇模組：")
        
        if choice == "0":
            print("感謝使用，再見！")
            break
        elif choice == "1":
            print("\n【M0 資料載入模組】")
            symbol = input("請輸入股票代碼（例如 AAPL）：")
            start_date = input("請輸入起始日期（格式：YYYY-MM-DD）：")
            end_date = input("請輸入結束日期（格式：YYYY-MM-DD）：")
            download_delay = int(input("請輸入下載延遲秒數（預設：2）：") or "2")
            date_chunk_size = int(input("請輸入時間切段大小（天數，預設：180）：") or "180")
            
            download_stock_data(symbol, start_date, end_date, download_delay, date_chunk_size)
            df = load_stock_data(symbol, start_date, end_date, source='csv')
            
            # 處理多個股票的返回結果
            if isinstance(df, dict):
                # 多個股票的情況
                print(f"\n=== 載入完成，共 {len(df)} 個股票 ===")
                for stock_symbol, stock_df in df.items():
                    if not stock_df.empty:
                        print(f"\n{stock_symbol} 資料摘要：")
                        print(f"  資料筆數：{len(stock_df)}")
                        print(f"  日期範圍：{stock_df['date'].min()} 到 {stock_df['date'].max()}")
                        print(f"  價格範圍：${stock_df['close'].min():.2f} - ${stock_df['close'].max():.2f}")
                        print(f"  最新收盤價：${stock_df['close'].iloc[-1]:.2f}")
                    else:
                        print(f"\n{stock_symbol}：無資料")
            else:
                # 單一股票的情況
                if not df.empty:
                    print(f"\n=== 載入完成 ===")
                    print(f"資料筆數：{len(df)}")
                    print(f"日期範圍：{df['date'].min()} 到 {df['date'].max()}")
                    print(f"價格範圍：${df['close'].min():.2f} - ${df['close'].max():.2f}")
                    print(f"最新收盤價：${df['close'].iloc[-1]:.2f}")
                    print("\n前5筆資料：")
                    print(df.head())
                else:
                    print("無資料載入")
        elif choice == "2":
            print("\n【M1 參數生成模組】")
            m1_main()
        elif choice == "3":
            print("\n【M2-1 樣本內批次訊號產生】")
            m2_signal_batch_main()
            print("\n【M2-2 樣本內批次回測】")
            m2_perf_batch_main()
        elif choice == "4":
            print("\n【M3 策略挑選模組】")
            m3_main()
        elif choice == "5":
            print("\n【M4-1 驗證區間批次訊號產生】")
            m4_1_main()
            print("\n【M4-2 驗證區間回測】")
            # Force reload the module to bypass cache issues
            import modules.m4_2_validation_performance
            importlib.reload(modules.m4_2_validation_performance)
            modules.m4_2_validation_performance.main()
            print("\n【M5 驗證區間策略再挑選】")
            m5_main()
        elif choice == "6":
            print("\n【M6 - 產生模擬交易訊號】")
            symbols_input = input("請輸入要產生訊號的股票代碼，用逗號分隔 (例如: AAPL,NVDA): ")
            symbols = [s.strip().upper() for s in symbols_input.split(',')]
            if symbols:
                generate_trade_signals(symbols)
            else:
                print("未輸入任何股票代碼。")
        elif choice == "7":
            print("\n【M7 - 模擬每日績效】")
            simulate_accounts()
        else:
            print("無效的選擇，請重新輸入")

if __name__ == "__main__":
    main() 