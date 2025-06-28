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


def test_polygon_api():
    """測試 Polygon API 的功能和限制"""
    print("=== Polygon API 測試 ===")
    client = RESTClient(api_key=POLYGON_API_KEY)
    
    # 測試最近的資料
    print("1. 測試最近的資料 (2024-01-01 到 2024-01-31):")
    try:
        aggs = client.get_aggs(
            ticker="AAPL",
            multiplier=1,
            timespan="day",
            from_=datetime(2024, 1, 1),
            to=datetime(2024, 1, 31)
        )
        print(f"   回傳 {len(aggs)} 筆資料")
        if aggs:
            first_date = datetime.fromtimestamp(aggs[0].timestamp / 1000).strftime('%Y-%m-%d')
            last_date = datetime.fromtimestamp(aggs[-1].timestamp / 1000).strftime('%Y-%m-%d')
            print(f"   日期範圍：{first_date} 到 {last_date}")
    except Exception as e:
        print(f"   錯誤：{e}")
    
    # 測試較舊的資料
    print("2. 測試較舊的資料 (2023-01-01 到 2023-01-31):")
    try:
        aggs = client.get_aggs(
            ticker="AAPL",
            multiplier=1,
            timespan="day",
            from_=datetime(2023, 1, 1),
            to=datetime(2023, 1, 31)
        )
        print(f"   回傳 {len(aggs)} 筆資料")
        if aggs:
            first_date = datetime.fromtimestamp(aggs[0].timestamp / 1000).strftime('%Y-%m-%d')
            last_date = datetime.fromtimestamp(aggs[-1].timestamp / 1000).strftime('%Y-%m-%d')
            print(f"   日期範圍：{first_date} 到 {last_date}")
    except Exception as e:
        print(f"   錯誤：{e}")
    
    print("=== 測試完成 ===")


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
        
        if not aggs:
            return pd.DataFrame()
            
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
    # 修正日期輸入檢查
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
    except ValueError:
        print(f"起始日期 {start_date} 無效，請重新輸入")
        return
    try:
        end = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        # 若日期無效，自動調整為該月最後一天
        year, month, _ = map(int, end_date.split('-'))
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        end_date = f"{year:04d}-{month:02d}-{last_day:02d}"
        end = datetime.strptime(end_date, '%Y-%m-%d')
        print(f"結束日期無效，已自動調整為 {end_date}")

    # 先讀取現有 CSV 資料
    csv_path = f'data_csv/{symbol}.csv'
    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path, parse_dates=['date'])
        existing_dates = set(existing_df['date'].dt.strftime('%Y-%m-%d'))
        print(f"現有資料日期範圍：{existing_df['date'].min()} 到 {existing_df['date'].max()}")
        print(f"現有資料筆數：{len(existing_df)}")
    else:
        existing_df = None
        existing_dates = set()
        print("無現有資料檔案")

    # 生成請求的日期範圍
    requested_dates = set()
    current_date = start
    while current_date <= end:
        requested_dates.add(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # 找出缺失的日期
    missing_dates = requested_dates - existing_dates
    if not missing_dates:
        print(f"{symbol} 在 {start_date} 到 {end_date} 期間的所有資料都已存在")
        return
    
    print(f"需要下載的日期數量：{len(missing_dates)}")
    print(f"缺失日期範圍：{min(missing_dates)} 到 {max(missing_dates)}")

    # 按時間區間下載缺失的資料
    current = start
    all_df = []
    
    # 使用更小的時間區間來避免 API 限制
    chunk_size = min(date_chunk_size, 30)  # 限制最大區間為 30 天
    
    while current <= end:
        chunk_end = min(current + timedelta(days=chunk_size-1), end)
        chunk_start_str = current.strftime('%Y-%m-%d')
        chunk_end_str = chunk_end.strftime('%Y-%m-%d')
        
        # 檢查這個區間是否有缺失的日期
        chunk_dates = set()
        temp_date = current
        while temp_date <= chunk_end:
            chunk_dates.add(temp_date.strftime('%Y-%m-%d'))
            temp_date += timedelta(days=1)
        
        missing_in_chunk = chunk_dates & missing_dates
        
        if missing_in_chunk:
            try:
                df = get_stock_data(symbol, chunk_start_str, chunk_end_str)
                if not df.empty:
                    # 只保留真正缺失的日期
                    df = df[df['date'].isin(missing_dates)]
                    if not df.empty:
                        all_df.append(df)
                        print(f"下載 {symbol}：{chunk_start_str} ~ {chunk_end_str} 補齊 {len(df)} 筆")
                    else:
                        print(f"{symbol}：{chunk_start_str} ~ {chunk_end_str} 無新資料")
                else:
                    print(f"下載 {symbol}：{chunk_start_str} ~ {chunk_end_str} 無資料")
            except Exception as e:
                print(f"下載 {symbol}：{chunk_start_str} ~ {chunk_end_str} 發生錯誤：{e}")
        else:
            print(f"{symbol}：{chunk_start_str} ~ {chunk_end_str} 已存在，略過")
        
        time.sleep(download_delay)
        current = chunk_end + timedelta(days=1)
    
    # 合併新舊資料
    if all_df:
        new_df = pd.concat(all_df) if len(all_df) > 1 else all_df[0]
        new_df['date'] = pd.to_datetime(new_df['date'])  # 確保新資料的日期格式正確
        if existing_df is not None:
            existing_df['date'] = pd.to_datetime(existing_df['date']) # 確保舊資料的日期格式正確
            result_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['date']).sort_values('date')
        else:
            result_df = new_df.sort_values('date')
        # 儲存至 CSV
        os.makedirs('data_csv', exist_ok=True)
        result_df.to_csv(csv_path, index=False)
        # 儲存至 SQLite
        os.makedirs('database', exist_ok=True)
        db_path = 'database/stock_price.db'
        conn = sqlite3.connect(db_path)
        result_df['date'] = result_df['date'].astype(str)  # 確保是純字串
        result_df.to_sql(symbol, conn, if_exists='replace', index=False)  # 不要設 index
        conn.close()
        print(f"{symbol} 補齊下載完成，資料已合併儲存至 {csv_path} 與 {db_path}")
        print(f"更新後總資料筆數：{len(result_df)}")
    else:
        print(f"{symbol} 指定區間皆已存在，無需下載")


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