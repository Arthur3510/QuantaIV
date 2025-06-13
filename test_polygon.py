import os
from datetime import datetime, timedelta
from polygon import RESTClient
import pandas as pd

def read_api_key():
    """
    從指定檔案讀取 Polygon.io API Key
    
    Returns:
        str: API Key
    """
    api_key_path = os.path.join(os.path.dirname(__file__), "docs", "Polygon.io", "polygon API Key.txt")
    try:
        with open(api_key_path, "r") as f:
            api_key = f.read().strip()
            print(f"讀取到的 API Key 長度: {len(api_key)}")
            print(f"API Key 格式檢查:")
            print(f"- 是否包含空格: {'是' if ' ' in api_key else '否'}")
            print(f"- 是否包含換行: {'是' if '\n' in api_key else '否'}")
            print(f"- 是否包含其他特殊字符: {'是' if not api_key.isalnum() else '否'}")
            return api_key
    except Exception as e:
        print(f"讀取 API Key 時發生錯誤：{str(e)}")
        return None

def get_stock_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    從 Polygon.io 下載股票資料
    
    Args:
        ticker (str): 股票代碼
        start_date (str): 開始日期 (YYYY-MM-DD)
        end_date (str): 結束日期 (YYYY-MM-DD)
    
    Returns:
        pd.DataFrame: 包含股票資料的 DataFrame
    """
    # 讀取 API Key
    api_key = read_api_key()
    if not api_key:
        raise ValueError("無法讀取 API Key")
    
    # 檢查 API Key 格式
    if len(api_key) < 20:  # Polygon.io API Key 通常很長
        raise ValueError(f"API Key 長度不正確: {len(api_key)}")
    
    # 初始化 Polygon.io 客戶端
    client = RESTClient(api_key=api_key)
    
    # 轉換日期格式
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # 獲取股票資料
    aggs = client.get_aggs(
        ticker=ticker,
        multiplier=1,
        timespan="day",
        from_=start,
        to=end
    )
    
    # 轉換為 DataFrame
    df = pd.DataFrame([{
        "date": datetime.fromtimestamp(agg.timestamp / 1000),
        "open": agg.open,
        "high": agg.high,
        "low": agg.low,
        "close": agg.close,
        "volume": agg.volume
    } for agg in aggs])
    
    return df

def main():
    # 測試下載 AAPL 的資料
    ticker = "AAPL"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    try:
        df = get_stock_data(ticker, start_date, end_date)
        print(f"\n成功下載 {ticker} 的資料：")
        print(f"資料期間：{start_date} 到 {end_date}")
        print("\n前5筆資料：")
        print(df.head())
        
        # 保存到 CSV 文件
        output_file = f"{ticker}_data.csv"
        df.to_csv(output_file, index=False)
        print(f"\n資料已保存到 {output_file}")
        
    except Exception as e:
        print(f"發生錯誤：{str(e)}")

if __name__ == "__main__":
    main()
