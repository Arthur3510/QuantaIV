import requests
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor

# 設定 polygon.io API Key
POLYGON_API_KEY = "YOUR_POLYGON_API_KEY"  # 請替換為你的 API Key

def download_stock_data(symbol, start_date, end_date, download_delay=2, date_chunk_size=180):
    """
    從 polygon.io 下載股票資料並儲存至 CSV 與 SQLite 資料庫。
    
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
        
        # 從 polygon.io 下載資料
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{chunk_start_str}/{chunk_end_str}?apiKey={POLYGON_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'OK':
            df = pd.DataFrame(data['results'])
            df['date'] = pd.to_datetime(df['t'], unit='ms')
            df.set_index('date', inplace=True)
            df.drop('t', axis=1, inplace=True)
            
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
            df.index = df.index.strftime('%Y-%m-%d')
            df.to_sql(symbol, conn, if_exists='replace', index=True)
            conn.close()
            
            print(f"資料已下載並儲存至 {csv_path} 與 {db_path}（{chunk_start_str} 至 {chunk_end_str}）")
        else:
            print(f"下載失敗：{data['status']}")
        
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
    # 選單讓使用者填寫下載參數
    print("【M0 資料載入模組】")
    symbol = input("請輸入股票代碼（例如 AAPL）：")
    start_date = input("請輸入起始日期（格式：YYYY-MM-DD）：")
    end_date = input("請輸入結束日期（格式：YYYY-MM-DD）：")
    download_delay = int(input("請輸入下載延遲秒數（預設：2）：") or "2")
    date_chunk_size = int(input("請輸入時間切段大小（天數，預設：180）：") or "180")
    
    download_stock_data(symbol, start_date, end_date, download_delay, date_chunk_size)
    df = load_stock_data(symbol, start_date, end_date, source='csv')
    print(df.head()) 