import pandas as pd
import numpy as np

def calculate_performance_metrics(group):
    """
    計算單一策略組的績效指標。
    此函數為 M2-2 和 M4-2 共用。
    group: 一個 DataFrame，包含單一 param_id 的所有數據。
    """
    # 將 date 設為索引，確保時間序列運算正確
    group = group.set_index('date').sort_index()

    result = {
        'total_return': np.nan,
        'max_drawdown': np.nan,
        'sharpe': np.nan
    }
    
    # 核心邏輯：不信任任何傳入的 position，永遠根據 signal 重新計算。
    # 這是為了確保無論輸入數據如何，計算都是基於最原始的信號。
    position = group['signal'].replace(0, np.nan).ffill().fillna(0)
    
    # 如果沒有任何交易訊號，直接返回 0
    if (position == 0).all():
        return pd.Series(result)

    # 找到第一個交易訊號的位置 (使用 .ne(0).idxmax() 更穩健)
    first_trade_idx = position.ne(0).idxmax()
    
    # 從第一個交易訊號開始計算
    position = position.loc[first_trade_idx:]
    close = group['close'].loc[first_trade_idx:]
    
    # 計算每日報酬率和淨值 (NAV)
    # 報酬率是根據前一天的倉位，和今天的價格變化計算
    daily_returns = position.shift(1).fillna(0) * close.pct_change().fillna(0)
    
    if len(daily_returns) <= 1:
        return pd.Series(result)

    nav = (1 + daily_returns).cumprod()
    
    # 計算總報酬率
    result['total_return'] = nav.iloc[-1] - 1
    
    # 計算最大回撤
    peak = nav.expanding().max()
    drawdown = (nav - peak) / peak
    result['max_drawdown'] = drawdown.min()
    
    # 計算夏普比率 (年化)
    # 檢查以避免除以零
    if daily_returns.std() > 0:
        # 假設無風險利率為 0
        ann_ret = np.mean(daily_returns) * 252
        ann_vol = np.std(daily_returns) * np.sqrt(252)
        # 避免 ann_vol 為 0 的情況
        result['sharpe'] = ann_ret / ann_vol if ann_vol > 0 else 0.0
    else:
        result['sharpe'] = 0.0
    
    return pd.Series(result) 