import yfinance as yf
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta

def download_stock_data(symbol, start_date, end_date, download_delay=2):
    """
    從 Yahoo Finance 下載股票資料並儲存至 CSV 與 SQLite 資料庫。
    
    Args:
        symbol (str): 股票代碼
        start_date (str): 起始日期，格式為 'YYYY-MM-DD'
        end_date (str): 結束日期，格式為 'YYYY-MM-DD'
        download_delay (int): 下載延遲秒數，預設為 2 秒
    """
    # 下載資料
    stock = yf.Ticker(symbol)
    df = stock.history(start=start_date, end=end_date)
    
    # 儲存至 CSV
    csv_path = f'data_csv/{symbol}.csv'
    os.makedirs('data_csv', exist_ok=True)
    df.to_csv(csv_path)
    
    # 儲存至 SQLite
    db_path = 'database/stock_price.db'
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect(db_path)
    df.to_sql(symbol, conn, if_exists='replace', index=True)
    conn.close()
    
    print(f"資料已下載並儲存至 {csv_path} 與 {db_path}")

if __name__ == "__main__":
    # 範例使用
    download_stock_data('AAPL', '2023-01-01', '2023-12-31') 