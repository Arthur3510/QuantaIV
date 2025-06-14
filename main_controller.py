import os
import sys
from modules.m0_data_loader import download_stock_data, load_stock_data

def main():
    while True:
        print("\n【QuantaIII 主選單】")
        print("1. M0 資料載入模組")
        print("2. M1 參數生成模組")
        print("3. M2 回測模組")
        print("4. M3 策略挑選模組")
        print("5. M4 訊號檢查模組")
        print("0. 離開")
        
        choice = input("請選擇模組（0-5）：")
        
        if choice == "0":
            print("離開程式")
            sys.exit()
        elif choice == "1":
            print("\n【M0 資料載入模組】")
            symbol = input("請輸入股票代碼（例如 AAPL）：")
            start_date = input("請輸入起始日期（格式：YYYY-MM-DD）：")
            end_date = input("請輸入結束日期（格式：YYYY-MM-DD）：")
            download_delay = int(input("請輸入下載延遲秒數（預設：2）：") or "2")
            date_chunk_size = int(input("請輸入時間切段大小（天數，預設：180）：") or "180")
            
            download_stock_data(symbol, start_date, end_date, download_delay, date_chunk_size)
            df = load_stock_data(symbol, start_date, end_date, source='csv')
            print(df.head())
        elif choice == "2":
            print("M1 參數生成模組尚未開發")
        elif choice == "3":
            print("M2 回測模組尚未開發")
        elif choice == "4":
            print("M3 策略挑選模組尚未開發")
        elif choice == "5":
            print("M4 訊號檢查模組尚未開發")
        else:
            print("無效的選擇，請重新輸入")

if __name__ == "__main__":
    main() 