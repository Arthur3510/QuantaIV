import yfinance as yf
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor

def download_stock_data(symbol, start_date, end_date, download_delay=2, date_chunk_size=180):
    """
    從 Yahoo Finance 下載股票資料並儲存至 CSV 與 SQLite 資料庫。
    
    Args:
        symbol (str): 股票代碼
        start_date (str): 起始日期，格式為 'YYYY-MM-DD'
        end_date (str): 結束日期，格式為 'YYYY-MM-DD'
        download_delay (int): 下載延遲秒數，預設為 2 秒
        date_chunk_size (int): 時間切段大小（天數），預設為 180 天
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 時間切段設計
    current = start
    while current < end:
        chunk_end = min(current + timedelta(days=date_chunk_size), end)
        chunk_start_str = current.strftime('%Y-%m-%d')
        chunk_end_str = chunk_end.strftime('%Y-%m-%d')
        
        # 下載資料
        stock = yf.Ticker(symbol)
        df = stock.history(start=chunk_start_str, end=chunk_end_str)
        
        # 儲存至 CSV
        csv_path = f'data_csv/{symbol}.csv'
        os.makedirs('data_csv', exist_ok=True)
        if os.path.exists(csv_path):
            existing_df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            df = pd.concat([existing_df, df]).drop_duplicates()
        df.to_csv(csv_path)
        
        # 儲存至 SQLite
        db_path = 'database/stock_price.db'
        os.makedirs('database', exist_ok=True)
        conn = sqlite3.connect(db_path)
        df.to_sql(symbol, conn, if_exists='replace', index=True)
        conn.close()
        
        print(f"資料已下載並儲存至 {csv_path} 與 {db_path}（{chunk_start_str} 至 {chunk_end_str}）")
        
        # 下載延遲
        time.sleep(download_delay)
        current = chunk_end

def load_stock_data(symbol, start_date, end_date, source='csv'):
    """
    從 CSV 或 SQLite 資料庫讀取股票資料。
    
    Args:
        symbol (str): 股票代碼
        start_date (str): 起始日期，格式為 'YYYY-MM-DD'
        end_date (str): 結束日期，格式為 'YYYY-MM-DD'
        source (str): 資料來源，'csv' 或 'sqlite'，預設為 'csv'
    
    Returns:
        pandas.DataFrame: 股票資料
    """
    if source == 'csv':
        csv_path = f'data_csv/{symbol}.csv'
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV 檔案 {csv_path} 不存在")
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    elif source == 'sqlite':
        db_path = 'database/stock_price.db'
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"SQLite 資料庫 {db_path} 不存在")
        conn = sqlite3.connect(db_path)
        df = pd.read_sql(f"SELECT * FROM {symbol}", conn, index_col='Date', parse_dates=True)
        conn.close()
    else:
        raise ValueError("資料來源必須為 'csv' 或 'sqlite'")
    
    # 篩選日期範圍
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    return df

if __name__ == "__main__":
    # 範例使用
    download_stock_data('AAPL', '2023-01-01', '2023-12-31')
    df = load_stock_data('AAPL', '2023-01-01', '2023-12-31', source='csv')
    print(df.head()) 