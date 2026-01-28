from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import market_data
import backtester

router = APIRouter()

class BacktestRequest(BaseModel):
    strategy_id: Optional[str] = None
    market: str = "BTC"
    timeframe: str = "1h"
    logic: Optional[dict] = None # Placeholder for dynamic rules

@router.post("/run")
async def run_backtest_endpoint(req: BacktestRequest):
    # 1. Fetch Real Data
    df = market_data.fetch_candles(req.market, req.timeframe)
    if df.empty:
        return {"error": "Could not fetch market data"}
    
    # 2. Run Backtest
    # Pass 'req.logic' in future for dynamic. Currently defaults to RSI logic in backtester.py
    results = backtester.run_backtest(df, req.logic)
    
    return results

@router.post("/compare")
async def run_comparison(req: BacktestRequest):
    """
    Runs the strategy AND a "Buy & Hold" benchmark.
    """
    df = market_data.fetch_candles(req.market, req.timeframe)
    if df.empty:
        return {"error": "No data"}
        
    # Strategy
    strat_results = backtester.run_backtest(df, req.logic)
    
    # Benchmark (Buy and Hold)
    initial_price = df.iloc[0]['close']
    initial_cap = 10000
    benchmark_curve = []
    
    for index, row in df.iterrows():
        equity = initial_cap * (row['close'] / initial_price)
        benchmark_curve.append({
            "date": row['timestamp'].strftime('%Y-%m-%d %H:%M'),
            "equity": round(equity, 2),
            "price": row['close']
        })
        
    return {
        "strategy": strat_results,
        "benchmark": benchmark_curve
    }

@router.post("/scan")
async def scan_markets(req: BacktestRequest):
    """
    Runs the strategy on multiple assets to find the best performer.
    """
    ASSETS = ["BTC", "ETH", "SOL", "AVAX", "DOGE", "ARB"]
    results = []
    
    for asset in ASSETS:
        try:
            df = market_data.fetch_candles(asset, req.timeframe)
            if df.empty:
                continue
                
            res = backtester.run_backtest(df, req.logic)
            metrics = res["metrics"]
            
            results.append({
                "market": asset,
                "return_pct": metrics["total_return_pct"],
                "trades": metrics["total_trades"],
                "final_equity": metrics["final_equity"]
            })
        except Exception as e:
            print(f"Error scanning {asset}: {e}")
            continue
        
    # Sort by Return Descending
    results.sort(key=lambda x: x["return_pct"], reverse=True)
    
    return {
        "best_asset": results[0] if results else None,
        "all_results": results
    }

@router.post("/optimize")
async def optimize_strategy(req: BacktestRequest):
    """
    Attempts to improve the strategy by iterating over parameters (Take Profit, Stop Loss).
    """
    df = market_data.fetch_candles(req.market, req.timeframe)
    if df.empty: return {"error": "No Data"}
    
    # Baseline
    base_res = backtester.run_backtest(df, req.logic)
    base_return = base_res["metrics"]["total_return_pct"]
    
    best_return = base_return
    best_params = {}
    improvement_log = []
    
    current_params = req.logic.get("params", {}) if req.logic and req.logic.get("params") else {}
    
    # --- Optimization Heuristics ---
    
    # 1. Try Adding Take Profit (1% to 15%)
    for tp in [1, 2, 3, 5, 8, 12, 15]:
        test_params = current_params.copy()
        test_params["take_profit_pct"] = tp
        
        test_logic = req.logic.copy() if req.logic else {}
        test_logic["params"] = test_params
        
        res = backtester.run_backtest(df, test_logic)
        ret = res["metrics"]["total_return_pct"]
        
        if ret > best_return:
            best_return = ret
            best_params = test_params.copy()
            improvement_log.append(f"Adding Take Profit {tp}% increased return from {base_return}% to {ret}%")
            
    # 2. Try Adding Stop Loss (if Take Profit worked, keep it, else clean)
    current_best = best_params if best_params else current_params
    
    for sl in [1, 2, 5, 10]:
        test_params = current_best.copy()
        test_params["stop_loss_pct"] = sl
        
        test_logic = req.logic.copy() if req.logic else {}
        test_logic["params"] = test_params
        
        res = backtester.run_backtest(df, test_logic)
        ret = res["metrics"]["total_return_pct"]
        
        if ret > best_return:
            best_return = ret
            best_params = test_params.copy()
            improvement_log.append(f"Adding Stop Loss {sl}% increased return to {ret}%")

    return {
        "original_return": base_return,
        "best_return": best_return,
        "improved_params": best_params,
        "improvement_log": improvement_log
    }

@router.post("/train")
async def train_oracle(req: BacktestRequest):
    """
    Run Oracle strategy, record stats of every perfect trade, 
    and return the 'Learned' parameters (Mean RSI, etc).
    """
    df = market_data.fetch_candles(req.market, req.timeframe)
    if df.empty: return {"error": "No Data"}
    
    # 1. Run Oracle to get perfect trades
    res = backtester.run_backtest(df, {"type": "ORACLE"})
    trades = res["trades"]
    
    if not trades:
        return {"error": "Oracle found no trades to learn from."}
      
    # 2. Correlate trades with indicators to find patterns
    df = backtester.calculate_indicators(df)
    
    rsi_buys = []
    rsi_sells = []
    macd_buys = []
    
    for t in trades:
        trade_dt = pd.to_datetime(t["date"])
        mask = df['timestamp'] == trade_dt
        row = df[mask]
        
        if not row.empty:
            val_rsi = row.iloc[0]['rsi']
            val_macd = row.iloc[0]['macd']
            
            if t['side'] == 'BUY':
                rsi_buys.append(val_rsi)
                macd_buys.append(val_macd)
            elif t['side'] == 'SELL':
                rsi_sells.append(val_rsi)
                
    # 3. Calculate Learned Thresholds
    avg_rsi_buy = sum(rsi_buys)/len(rsi_buys) if rsi_buys else 30
    avg_rsi_sell = sum(rsi_sells)/len(rsi_sells) if rsi_sells else 70
    avg_macd_buy = sum(macd_buys)/len(macd_buys) if macd_buys else 0
    
    params = {
        "rsi_buy": round(float(avg_rsi_buy), 2),
        "rsi_sell": round(float(avg_rsi_sell), 2),
        "macd_buy": round(float(avg_macd_buy), 4)
    }
    
    return {
        "learned_params": params,
        "message": f"Analyzed {len(trades)} perfect trades. Oracle usually buys at RSI {params['rsi_buy']} and sells at {params['rsi_sell']}."
    }

@router.post("/infer")
async def infer_strategy(req: BacktestRequest):
    """
    Strategy Factory:
    Takes user-marked BUY/SELL points and infers the logic.
    req.logic should contain 'marked_trades' list.
    """
    import strategy_factory
    
    df = market_data.fetch_candles(req.market, req.timeframe)
    if df.empty: return {"error": "No Data"}
    
    marks = req.logic.get("marked_trades", [])
    if not marks:
        return {"error": "No trades marked."}
        
    # Infer
    result = strategy_factory.infer_strategy_from_marks(df, marks)
    
    return result
