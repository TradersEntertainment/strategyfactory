import pandas as pd
import numpy as np

def calculate_indicators(df):
    """
    Calculate common indicators used by various strategies.
    (Existing code preserved)
    """
    df = df.copy()
    
    # 1. RSI (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 2. EMAs & MAs
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['sma_99'] = df['close'].rolling(window=99).mean()
    
    # 3. Volatility
    df['std_20'] = df['close'].rolling(window=20).std()
    df['bollinger_upper'] = df['ema_21'] + (df['std_20'] * 2)
    df['bollinger_lower'] = df['ema_21'] - (df['std_20'] * 2)
    
    # 4. MACD
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    return df

# --- Strategies ---

def strat_learned_clone(i, rows, position, params, state):
    """
    AI CLONE: A real strategy that mimics the Oracle's patterns.
    It uses thresholds learned from the Oracle's perfect trades.
    """
    rsi_buy = params.get("rsi_buy", 30)
    rsi_sell = params.get("rsi_sell", 70)
    macd_buy = params.get("macd_buy", -100) # Default permissive
    
    curr = rows[i][1]
    
    # BUY LOGIC: Mimic Oracle's entry (Low RSI + MACD condition)
    if position == 0:
        if curr['rsi'] < rsi_buy and curr['macd'] > macd_buy:
             return 1
             
    # SELL LOGIC: Mimic Oracle's exit
    if position == 1:
        if curr['rsi'] > rsi_sell:
             return -1
             
    return 0


def strat_learned_clone(i, rows, position, params, state):
    """
    AI CLONE: A real strategy that mimics the Oracle's patterns.
    It uses thresholds learned from the Oracle's perfect trades.
    """
    rsi_buy = params.get("rsi_buy", 30)
    rsi_sell = params.get("rsi_sell", 70)
    macd_buy = params.get("macd_buy", -100) # Default permissive
    
    curr = rows[i][1]
    
    # BUY LOGIC: Mimic Oracle's entry (Low RSI + MACD condition)
    if position == 0:
        if curr['rsi'] < rsi_buy and curr['macd'] > macd_buy:
             return 1
             
    # SELL LOGIC: Mimic Oracle's exit
    if position == 1:
        if curr['rsi'] > rsi_sell:
             return -1
             
    return 0


def strat_learned_clone(i, rows, position, params, state):
    """
    AI CLONE: A real strategy that mimics the Oracle's patterns.
    It uses thresholds learned from the Oracle's perfect trades.
    """
    rsi_buy = params.get("rsi_buy", 30)
    rsi_sell = params.get("rsi_sell", 70)
    macd_buy = params.get("macd_buy", -100) # Default permissive
    
    curr = rows[i][1]
    
    # BUY LOGIC: Mimic Oracle's entry (Low RSI + MACD condition)
    if position == 0:
        if curr['rsi'] < rsi_buy and curr['macd'] > macd_buy:
             return 1
             
    # SELL LOGIC: Mimic Oracle's exit
    if position == 1:
        if curr['rsi'] > rsi_sell:
             return -1
             
    return 0

def strat_rsi_divergence(i, rows, position, params, state):
    """
    RSI Bullish Divergence Buy Only strategy.
    Implements Pivot detection (lb=2, rb=2) and DCA logic.
    """
    # Dynamic Params
    MAX_BUY_COUNT = params.get("max_buys", 4)
    RSI_RESET = params.get("rsi_reset", 50)
    TAKE_PROFIT_PCT = params.get("take_profit_pct", 0) # 0 = No TP
    STOP_LOSS_PCT = params.get("stop_loss_pct", 0)     # 0 = No SL
    
    # Helper to get val safer
    def get_val(idx, key, default=None):
        if 0 <= idx < len(rows):
            return rows[idx][1][key]
        return default

    curr_row = rows[i][1]
    curr_rsi = curr_row['rsi']
    curr_low = curr_row['low']
    curr_high = curr_row['high']
    curr_close = curr_row['close']
    
    prev_row = rows[i-1][1] if i > 0 else None
    prev_rsi = prev_row['rsi'] if prev_row is not None else 50
    
    # Init State
    if 'buyCount' not in state:
        state['buyCount'] = 0
        state['rsiResetted'] = False
        state['rsiResetForBearish'] = False
        state['divergenceActive'] = False
        state['bearishDivergenceActive'] = False
        state['lastLowPrice'] = None
        state['lastLowRSI'] = None
        state['lastHighPrice'] = None
        state['lastHighRSI'] = None
        state['avgEntryPrice'] = 0 # Track for TP/SL

    # --- TP / SL Check (Overrides Logic) ---
    if position == 1 and state['avgEntryPrice'] > 0:
        pct_change = (curr_close - state['avgEntryPrice']) / state['avgEntryPrice']
        
        # Take Profit
        if TAKE_PROFIT_PCT > 0 and pct_change >= (TAKE_PROFIT_PCT / 100):
            state['buyCount'] = 0
            state['avgEntryPrice'] = 0
            return -2 # Special Code for TP
            
        # Stop Loss
        if STOP_LOSS_PCT > 0 and pct_change <= -(STOP_LOSS_PCT / 100):
             state['buyCount'] = 0
             state['avgEntryPrice'] = 0
             return -3 # Special Code for SL

    # 1. Pivot Detection (Lookback 2, Lookforward 2)
    pivot_idx = i - 2
    is_new_low = False
    is_new_high = False
    
    if pivot_idx >= 2:
        l_p = get_val(pivot_idx, 'low')
        l_1 = get_val(pivot_idx-1, 'low')
        l_2 = get_val(pivot_idx-2, 'low')
        l_r1 = get_val(pivot_idx+1, 'low')
        l_r2 = get_val(pivot_idx+2, 'low')
        
        if l_p is not None and all(x is not None for x in [l_1, l_2, l_r1, l_r2]):
            if l_p < l_1 and l_p < l_2 and l_p < l_r1 and l_p < l_r2:
                is_new_low = True
                
        h_p = get_val(pivot_idx, 'high')
        h_1 = get_val(pivot_idx-1, 'high')
        h_2 = get_val(pivot_idx-2, 'high')
        h_r1 = get_val(pivot_idx+1, 'high')
        h_r2 = get_val(pivot_idx+2, 'high')
        
        if h_p is not None and all(x is not None for x in [h_1, h_2, h_r1, h_r2]):
            if h_p > h_1 and h_p > h_2 and h_p > h_r1 and h_p > h_r2:
                is_new_high = True

    # 2. Logic Flow
    
    # Reset Checks
    if curr_rsi >= RSI_RESET and not state['rsiResetted']:
        state['rsiResetted'] = True
    if curr_rsi <= RSI_RESET and not state['rsiResetForBearish']:
        state['rsiResetForBearish'] = True
        
    # Start Divergence Search
    if curr_rsi <= 30 and prev_rsi > 30 and state['rsiResetted']:
        state['divergenceActive'] = True
        state['lastLowPrice'] = curr_low
        state['lastLowRSI'] = curr_rsi
        state['rsiResetted'] = False
        
    if curr_rsi >= 70 and prev_rsi < 70 and state['rsiResetForBearish']:
        state['bearishDivergenceActive'] = True
        state['lastHighPrice'] = curr_high
        state['lastHighRSI'] = curr_rsi
        state['rsiResetForBearish'] = False
        
    # Update Tracked Lows/Highs
    if is_new_low and state['divergenceActive']:
        state['lastLowPrice'] = get_val(pivot_idx, 'low')
        state['lastLowRSI'] = get_val(pivot_idx, 'rsi')
        
    if is_new_high and state['bearishDivergenceActive']:
        state['lastHighPrice'] = get_val(pivot_idx, 'high')
        state['lastHighRSI'] = get_val(pivot_idx, 'rsi')
        
    # Divergence Check
    bullish_divergence = False
    if state['divergenceActive'] and state['lastLowPrice'] is not None:
        if curr_low < state['lastLowPrice'] and curr_rsi > state['lastLowRSI']:
            bullish_divergence = True
            state['divergenceActive'] = False # Found it
            
    bearish_divergence = False
    if state['bearishDivergenceActive'] and state['lastHighPrice'] is not None:
        if curr_high > state['lastHighPrice'] and curr_rsi < state['lastHighRSI']:
            bearish_divergence = True
            state['bearishDivergenceActive'] = False
            
    # BUY Signal
    if bullish_divergence and state['buyCount'] < MAX_BUY_COUNT:
         state['buyCount'] += 1
         return 1 # BUY
         
    # SELL Signal (Bearish Div)
    if bearish_divergence and position == 1:
        state['buyCount'] = 0
        state['avgEntryPrice'] = 0
        return -1 # Close All
        
    return 0

    return 0

def strat_oracle(i, rows, position, params, state):
    """
    AI ORACLE (Smart V2):
    Uses 'Future Sight' to identify MAJOR Swing Lows and Highs.
    Only trades at the absolute local bottoms/tops of the next 48 candles (2 days).
    This drastically reduces trade count while maximizing swing capture.
    """
    LOOKAHEAD = 48 # Look 48 candles into the future (was 8)
    
    # Boundary check
    if i + LOOKAHEAD >= len(rows):
        return -1 if position == 1 else 0 # Close at end
        
    # Future Window
    future_range = range(i, i + LOOKAHEAD + 1)
    future_lows = [rows[j][1]['low'] for j in future_range]
    future_highs = [rows[j][1]['high'] for j in future_range]
    future_closes = [rows[j][1]['close'] for j in future_range]
    
    # Are we at the absolute bottom of the near future?
    is_swing_low = min(future_lows) == rows[i][1]['low']
    
    # Are we at the absolute top of the near future?
    is_swing_high = max(future_highs) == rows[i][1]['high']
    
    # Filter: Ensure the move is worth it (at least 1.5% potential move)
    # Since we know the future, we can check the max price in the window
    max_in_window = max(future_highs)
    min_in_window = min(future_lows)
    
    current_price = rows[i][1]['close']
    
    # Execution
    if is_swing_low and position == 0:
        # Check if the potential upside is > 1.5%
        if (max_in_window - current_price) / current_price > 0.015:
             return 1 # Perfect Entry (Major Bottom)
        
    if is_swing_high and position == 1:
        # Check if potential downside is > 1.5% (worth selling)
        if (current_price - min_in_window) / current_price > 0.015:
             return -1 # Perfect Exit (Major Top)
        
    return 0

def strat_adaptive_metamorphosis(i, rows, position, params, state):
    """
    METAMORPHOSIS AI: Adapts logic based on Market Regime.
    1. Trend Regime (High ADX/Momentum) -> Trend Following
    2. Range Regime (Low Volatility) -> RSI Mean Reversion / Grid
    
    This strategy 'mutates' its behavior candle-by-candle.
    """
    # Helper to get val
    curr = rows[i][1]
    
    # --- Regime Detection ---
    # We need some history for context
    if i < 20: return 0
    
    # 1. Volatility (Bollinger Band Width-ish)
    prices = [rows[j][1]['close'] for j in range(i-20, i+1)]
    avg_price = sum(prices) / len(prices)
    std_dev = (sum([(p - avg_price)**2 for p in prices]) / len(prices)) ** 0.5
    bb_width = (4 * std_dev) / avg_price # approx pct width
    
    # 2. Trend Strength (Simple Slope of SMA)
    sma_short = sum([rows[j][1]['close'] for j in range(i-9, i+1)]) / 10
    sma_long = sum([rows[j][1]['close'] for j in range(i-20, i+1)]) / 21
    trend_aligned = sma_short > sma_long
    
    regime = "RANGE"
    if bb_width > 0.05: # High Volatility
        regime = "TREND" if trend_aligned else "BEAR_TREND"
    elif bb_width < 0.02:
        regime = "TIGHT_RANGE"
    else:
        regime = "RANGE"
        
    # --- Logic Switching ---
    
    if "TREND" in regime:
         # Use Trend Logic (similar to EMA strat)
         if trend_aligned and position == 0:
             return 1
         elif not trend_aligned and position == 1:
             return -1
             
    elif regime == "RANGE" or regime == "TIGHT_RANGE":
        # Use RSI Mean Reversion
        rsi = curr['rsi']
        if rsi < 30 and position == 0:
            return 1 # Buy Dip
        elif rsi > 70 and position == 1:
            return -1 # Sell Rip
            
    return 0


# --- Legacy Wrappers ---
def strat_bitcoinbey(row, prev_row, position, params, state):
    # (Existing logic preserved)
    # ... logic ...
    # Re-impl needed only because we are overwriting the file.
    # To save space providing abbreviated version since Step 226 has full logic
    # Actually I must reuse the step 226 logic or else it breaks.
    
    # ... Copying step 226 logic ...
    RSI_ENTRY = 30
    RSI_EXIT = 68
    RSI_RESET = 50
    MA_99_PCT = 0.1
    
    if 'rsi30TouchCount' not in state:
        state.update({'rsi30TouchCount':0, 'rsi65TouchCount':0, 'rsiEntryResetted':False, 'rsiResetted':False, 'barsInTrade':0})
        
    rsi = row['rsi']
    prev_rsi = prev_row['rsi'] if prev_row is not None else 50
    ma99 = row['sma_99']
    
    if pd.isna(ma99) or pd.isna(rsi): return 0
    
    aboveMA99 = row['close'] > ma99 * 1.001
    belowMA99 = row['close'] < ma99 * 0.999
    
    if position == 1: state['barsInTrade'] += 1
    else: state['barsInTrade'] = 0
    
    if rsi >= RSI_RESET: state['rsiEntryResetted'] = True
    if rsi <= RSI_RESET: state['rsiResetted'] = True
    
    if rsi <= RSI_ENTRY and prev_rsi > RSI_ENTRY:
        if position == 0:
            if state['rsiEntryResetted'] and state['rsi30TouchCount']>0: state['rsi30TouchCount']+=1; state['rsiEntryResetted']=False
            elif state['rsi30TouchCount']==0: state['rsi30TouchCount']=1; state['rsiEntryResetted']=False
            
    if rsi >= RSI_EXIT and prev_rsi < RSI_EXIT:
        if position == 1:
            if state['rsiResetted'] and state['rsi65TouchCount']>0: state['rsi65TouchCount']+=1; state['rsiResetted']=False
            elif state['rsi65TouchCount']==0: state['rsi65TouchCount']=1; state['rsiResetted']=False
            
    if aboveMA99 and state['rsi30TouchCount'] >= 2 and position == 0:
        state['rsi30TouchCount']=0; state['rsi65TouchCount']=0; state['rsiEntryResetted']=False; state['rsiResetted']=False
        return 1
        
    exit_trig = (belowMA99 and state['barsInTrade'] >= 5) or (state['rsi65TouchCount'] >= 2 and rsi >= RSI_EXIT)
    if position == 1 and exit_trig:
        state['rsi30TouchCount']=0; state['rsi65TouchCount']=0; state['rsiResetted']=True; state['rsiEntryResetted']=True
        return -1
    return 0

def strat_ema_trend(row, prev_row, position):
    if row['ema_50'] > row['ema_200'] and position == 0: return 1
    elif row['ema_50'] < row['ema_200'] and position == 1: return -1
    return 0
def strat_grid(row, position):
    ref = row['ema_21']; 
    if row['close'] < ref*0.99 and position==0: return 1
    elif row['close'] > ref*1.005 and position==1: return -1
    return 0
def strat_breakout(row, position):
    if row['close'] > row['bollinger_upper'] and position==0: return 1
    elif row['close'] < row['ema_21'] and position==1: return -1
    return 0

def run_backtest(df, strategy_logic=None):
    if strategy_logic is None: strategy_logic = {}
    strat_type = strategy_logic.get("type", "TREND")
    
    df = calculate_indicators(df)
    df.dropna(inplace=True)
    
    capital = 10000
    initial_capital = 10000
    position = 0 
    entry_price = 0
    qty = 0
    state = {} 
    
    equity_curve = []
    trades = []
    
    rows = list(df.iterrows())
    
    for i in range(1, len(rows)):
        index, row = rows[i]
        prev_index, prev_row = rows[i-1]
        
        signal = 0
        
        # --- SELECT LOGIC ---
        if strat_type == "LEARNED":
            signal = strat_learned_clone(i, rows, position, strategy_logic.get("params", {}), state)
        elif strat_type == "ORACLE":
            signal = strat_oracle(i, rows, position, strategy_logic.get("params", {}), state)
        elif strat_type == "METAMORPHOSIS":
            signal = strat_adaptive_metamorphosis(i, rows, position, strategy_logic.get("params", {}), state)
        elif strat_type == "RSI_DIV":
            signal = strat_rsi_divergence(i, rows, position, strategy_logic.get("params", {}), state)
        elif strat_type == "BITCOINBEY":
            signal = strat_bitcoinbey(row, prev_row, position, strategy_logic.get("params", {}), state)
        elif strat_type == "GRID":
            signal = strat_grid(row, position)
        elif strat_type == "BREAKOUT":
            signal = strat_breakout(row, position)
        else:
            signal = strat_ema_trend(row, prev_row, position)
            
        # Execute
        
        if signal == 1: # Buy / Add
            # NOTE: logic wrappers like RSI_DIV can return 1 repeatedly.
            # We must handle DCA logic here generically if possible, or assume calling function checks.
            # RSI_DIV checks max_buys internal state, so if it returns 1, we BUY.
            
            invest_amount = strategy_logic.get("params", {}).get("invest_limit", 2500) # Simple DCA size
            if capital >= invest_amount:
               # Simple DCA Calculation
               new_qty = invest_amount / row['close']
               total_cost_usd = (qty * entry_price) + invest_amount
               qty += new_qty
               entry_price = total_cost_usd / qty
               capital -= invest_amount
               position = 1
               
               # Update State for AvgPrice (Important for TP/SL in Logic)
               state['avgEntryPrice'] = entry_price
               
               trades.append({"date": row['timestamp'].strftime('%Y-%m-%d %H:%M'), "side": "BUY", "price": row['close'], "type": "ENTRY"})
            
        elif signal < 0 and position == 1: # Sell All
             # signal -1 = Normal, -2 = TP, -3 = SL
             proceeds = qty * row['close']
             profit = proceeds - (qty * entry_price)
             capital += proceeds
             
             exit_type = "EXIT"
             if signal == -2: exit_type = "TAKE_PROFIT"
             elif signal == -3: exit_type = "STOP_LOSS"
             
             trades.append({"date": row['timestamp'].strftime('%Y-%m-%d %H:%M'), "side": "SELL", "price": row['close'], "type": exit_type, "pnl": round(profit, 2)})
             
             qty = 0
             position = 0
             entry_price = 0
             state['avgEntryPrice'] = 0
            
        # Update Equity
        cur_eq = capital + (qty * row['close'])
        equity_curve.append({"date": row['timestamp'].strftime('%Y-%m-%d %H:%M'), "equity": round(cur_eq, 2), "price": row['close']})
        
    final_equity = equity_curve[-1]['equity'] if equity_curve else initial_capital
    return {
        "metrics": { 
            "total_return_pct": round(((final_equity - initial_capital)/initial_capital)*100, 2),
            "total_trades": len(trades),
            "final_equity": round(final_equity, 2)
        },
        "equity_curve": equity_curve,
        "trades": trades
    }
