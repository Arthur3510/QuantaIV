import sqlite3
import pandas as pd

def load_price_data(symbol, start_date, end_date):
    conn = sqlite3.connect('database/stock_price.db')
    df = pd.read_sql(f"SELECT * FROM {symbol} WHERE date >= ? AND date <= ? ORDER BY date", conn, params=(start_date, end_date), parse_dates=['date'])
    conn.close()
    df.set_index('date', inplace=True)
    return df

def get_recent_price_series(symbol: str, window: int = 30) -> pd.DataFrame:
    """
    Retrieves the most recent N (window) data points for a given symbol.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').
        window (int): The number of recent data points to retrieve.

    Returns:
        pd.DataFrame: A DataFrame containing the recent price data,
                      sorted by date in ascending order.
                      Returns an empty DataFrame if an error occurs.
    """
    try:
        conn = sqlite3.connect('database/stock_price.db')
        # Fetch the last 'window' rows, sorted by date ascending
        query = f"SELECT * FROM (SELECT * FROM {symbol} ORDER BY date DESC LIMIT {window}) ORDER BY date ASC"
        df = pd.read_sql(query, conn, parse_dates=['date'])
        conn.close()
        return df
    except Exception as e:
        print(f"ERROR: Failed to get recent price series for {symbol}. Reason: {e}")
        return pd.DataFrame() 