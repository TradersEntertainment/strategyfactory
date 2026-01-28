from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any

# --- Strategy Models ---

class IndicatorParam(BaseModel):
    name: str  # e.g., "period", "source"
    value: Union[int, float, str]

class Indicator(BaseModel):
    id: str        # e.g., "rsi_1"
    type: str      # "RSI", "EMA", "MACD"
    params: Dict[str, Any]

class Rule(BaseModel):
    condition: str # e.g., "RSI < 30" (Simplified for JSON, in reality needs AST or Structured)
    action: str    # "BUY", "SELL", "CLOSE"

class RiskSettings(BaseModel):
    stop_loss_pct: float
    take_profit_pct: float
    max_leverage: int
    position_size_pct: float

class Strategy(BaseModel):
    name: str
    description: str
    market: str     # "BTC-PERP"
    timeframe: str  # "1h"
    indicators: List[Indicator]
    rules: List[Rule]
    risk: RiskSettings

# --- Chat Models ---

class ChatRequest(BaseModel):
    message: str
    wallet_address: Optional[str] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    text: str
    strategy: Optional[Strategy] = None # If the AI generated a strategy
    should_confirm: bool = False
