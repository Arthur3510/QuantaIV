import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from polygon import RESTClient
import pandas as pd
import sqlite3
import time

# 載入環境變數
load_dotenv()

# 從 docs/Polygon.io/polygon API Key.txt 讀取 API Key
api_key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'Polygon.io', 'polygon API Key.txt')
if os.path.exists(api_key_path):
    with open(api_key_path, 'r') as f:
        POLYGON_API_KEY = f.read().strip()
else:
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY") or "YOUR_POLYGON_API_KEY"  # 請替換為你的 API Key


def get_stock_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    client = RESTClient(api_key=POLYGON_API_KEY)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    try:
        aggs = client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=start,
            to=end
        )
        df = pd.DataFrame([{
            'date': datetime.fromtimestamp(agg.timestamp / 1000).strftime('%Y-%m-%d'),
            'open': agg.open,
            'high': agg.high,
            'low': agg.low,
            'close': agg.close,
            'volume': agg.volume
        } for agg in aggs])
        return df
    except Exception as e:
        print(f"下載 {ticker}：{start_date} ~ {end_date} 發生錯誤：{e}")
        return pd.DataFrame()


def download_stock_data(symbol, start_date, end_date, download_delay=2, date_chunk_size=180):
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    current = start
    all_df = []
    while current < end:
        chunk_end = min(current + timedelta(days=date_chunk_size), end)
        chunk_start_str = current.strftime('%Y-%m-%d')
        chunk_end_str = chunk_end.strftime('%Y-%m-%d')
        try:
            df = get_stock_data(symbol, chunk_start_str, chunk_end_str)
            if not df.empty:
                all_df.append(df)
                print(f"下載 {symbol}：{chunk_start_str} ~ {chunk_end_str} 完成，共 {len(df)} 筆")
            else:
                print(f"下載 {symbol}：{chunk_start_str} ~ {chunk_end_str} 無資料")
        except Exception as e:
            print(f"下載 {symbol}：{chunk_start_str} ~ {chunk_end_str} 發生錯誤：{e}")
        time.sleep(download_delay)
        current = chunk_end
    if all_df:
        result_df = pd.concat(all_df).drop_duplicates(subset=['date']).sort_values('date')
        # 儲存至 CSV
        os.makedirs('data_csv', exist_ok=True)
        csv_path = f'data_csv/{symbol}.csv'
        result_df.to_csv(csv_path, index=False)
        # 儲存至 SQLite
        os.makedirs('database', exist_ok=True)
        db_path = 'database/stock_price.db'
        conn = sqlite3.connect(db_path)
        result_df.set_index('date', inplace=True)
        result_df.to_sql(symbol, conn, if_exists='replace', index=True)
        conn.close()
        print(f"{symbol} 全部下載完成，資料已儲存至 {csv_path} 與 {db_path}")
    else:
        print(f"{symbol} 無任何資料下載")


def load_stock_data(symbol, start_date, end_date, source='csv'):
    if source == 'csv':
        csv_path = f'data_csv/{symbol}.csv'
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV 檔案 {csv_path} 不存在")
        df = pd.read_csv(csv_path, parse_dates=['date'])
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    elif source == 'sqlite':
        db_path = 'database/stock_price.db'
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"SQLite 資料庫 {db_path} 不存在")
        conn = sqlite3.connect(db_path)
        df = pd.read_sql(f"SELECT * FROM {symbol}", conn, parse_dates=['date'])
        conn.close()
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    else:
        raise ValueError("資料來源必須為 'csv' 或 'sqlite'")
    return df


if __name__ == "__main__":
    print("【M0 資料載入模組】")
    symbol = input("請輸入股票代碼（例如 AAPL）：")
    start_date = input("請輸入起始日期（格式：YYYY-MM-DD）：")
    end_date = input("請輸入結束日期（格式：YYYY-MM-DD）：")
    download_delay = int(input("請輸入下載延遲秒數（預設：2）：") or "2")
    date_chunk_size = int(input("請輸入時間切段大小（天數，預設：180）：") or "180")
    download_stock_data(symbol, start_date, end_date, download_delay, date_chunk_size)
    df = load_stock_data(symbol, start_date, end_date, source='csv')
    print(df.head()) 