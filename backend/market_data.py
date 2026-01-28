import requests
import pandas as pd
import time
from datetime import datetime, timedelta

HYPERLIQUID_API_URL = "https://api.hyperliquid.xyz/info"

def fetch_candles(coin: str, interval: str = "1h", limit: int = 500):
    """
    Fetches candle data from Hyperliquid.
    Hyperliquid uses 'coin' (e.g., 'BTC') and resolution string.
    """
    # Map common intervals to HL resolution
    # HL expects: "15m", "1h", "4h", "1d" etc.
    
    headers = {'Content-Type': 'application/json'}
    
    # Snapshot requires end time. 
    # Logic: Fetch snapshots backwards if needed, but for MVP 1 snapshot is ~5000 candles usually.
    # Hyperliquid API params: {"type": "candleSnapshot", "req": {"coin": "BTC", "interval": "1h", "startTime": <ms>, "endTime": <ms>}}
    
    end_time = int(time.time() * 1000)
    start_time = int((datetime.now() - timedelta(days=30)).timestamp() * 1000) # Last 30 days
    
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": coin.upper(),
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time
        }
    }
    
    try:
        response = requests.post(HYPERLIQUID_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # HL returns list of: { "t": 165..., "T": 165..., "s": "BTC", "i": "1h", "o": "123.4", "c": "125.6", "h": "126.0", "l": "120.0", "v": "1000", "n": 50 }
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        
        # Rename and Convert
        df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
        df['open'] = df['o'].astype(float)
        df['high'] = df['h'].astype(float)
        df['low'] = df['l'].astype(float)
        df['close'] = df['c'].astype(float)
        df['volume'] = df['v'].astype(float)
        
        # Clean up
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df.sort_values('timestamp', inplace=True)
        return df

    except Exception as e:
        print(f"Error fetching data for {coin}: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Test
    print("Fetching BTC...")
    df = fetch_candles("BTC", "1h")
    print(df.tail())
