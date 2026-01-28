import pandas as pd
import numpy as np

def infer_strategy_from_marks(df, marks):
    """
    Analyzes user-marked trades to find common patterns.
    
    Args:
        df (pd.DataFrame): Market data with 'timestamp', 'open', 'high', 'low', 'close'
        marks (list): List of dicts {'date': 'YYYY-MM-DD HH:MM', 'side': 'BUY'|'SELL'}
        
    Returns:
        dict: Inferred strategy logic and explanation.
    """
    # 1. Feature Extraction (Enriched Indicators)
    # We use a comprehensive set to "cast a wide net"
    df = df.copy()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # EMAs
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # MACD
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # Bollinger
    df['std_20'] = df['close'].rolling(window=20).std()
    df['bb_upper'] = (df['close'].rolling(window=20).mean()) + (df['std_20'] * 2)
    df['bb_lower'] = (df['close'].rolling(window=20).mean()) - (df['std_20'] * 2)
    
    # Valid Data Only
    df.dropna(inplace=True)
    
    # 2. Extract Features at Marked Points
    buy_features = {
        "rsi": [],
        "dist_ema200": [], # % distance from EMA200
        "macd_val": [],
        "bb_pos": [] # 0=Lower, 1=Middle, 2=Upper (approx)
    }
    
    marks_count = 0
    
    for mark in marks:
        # Match timestamp
        # Assume mark['date'] matches df['timestamp'] string format or object
        # We'll convert both to string for matching to be safe
        ts_str = pd.to_datetime(mark['date']).strftime('%Y-%m-%d %H:%M')
        
        # Find row (inefficient but safe for small data)
        # Using string matching for simplicity in this prototype
        row = df[df['timestamp'].astype(str).str.contains(ts_str)]
        
        if not row.empty:
            marks_count += 1
            r = row.iloc[0]
            
            if mark['side'] == 'BUY':
                buy_features['rsi'].append(r['rsi'])
                buy_features['dist_ema200'].append( (r['close'] - r['ema_200']) / r['ema_200'] )
                buy_features['macd_val'].append(r['macd'])
                
                # BB Position (0 to 1 scale roughly)
                bb_range = r['bb_upper'] - r['bb_lower']
                bb_pos = (r['close'] - r['bb_lower']) / bb_range if bb_range > 0 else 0.5
                buy_features['bb_pos'].append(bb_pos)

    if marks_count < 2:
        return {"error": "Not enough matched trades to infer pattern. Please mark more points exactly on candles."}

    # 3. Hypothesis Testing / Pattern Recognition
    
    inferred_logic = {
        "type": "LEARNED",
        "params": {},
        "explanation": []
    }
    
    # -- Analyze BUYs --
    if buy_features['rsi']:
        avg_rsi = np.mean(buy_features['rsi'])
        std_rsi = np.std(buy_features['rsi'])
        
        # Hypothesis: RSI Mean Reversion
        if avg_rsi < 40:
            threshold = int(avg_rsi + std_rsi + 2) # Slightly loose upper bound
            inferred_logic['params']['rsi_buy'] = threshold
            inferred_logic['explanation'].append(f"You tend to buy when RSI is low (avg {avg_rsi:.1f}).")
        else:
            inferred_logic['params']['rsi_buy'] = 100 # Disable
            
    if buy_features['dist_ema200']:
        avg_dist = np.mean(buy_features['dist_ema200'])
        
        # Hypothesis: Trend Following
        if avg_dist > 0.005: # Consistently above EMA200
             inferred_logic['params']['trend_filter'] = "ABOVE_EMA200"
             inferred_logic['explanation'].append("Your entries mostly occur in an Uptrend (Above EMA200).")
    
    # Fallback / Defaults
    if 'rsi_buy' not in inferred_logic['params']:
        inferred_logic['params']['rsi_buy'] = 30
        inferred_logic['explanation'].append("No strong RSI pattern found, defaulting to RSI < 30.")

    # Consolidate explanation
    summary = " ".join(inferred_logic['explanation'])
    inferred_logic['description'] = summary
    
    return inferred_logic
