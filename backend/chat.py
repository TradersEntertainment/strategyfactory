import os
import json
import dashscope
from dashscope import Generation
from models import ChatRequest, ChatResponse, Strategy, Indicator, Rule, RiskSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
async def chat_handler(request: ChatRequest):
    """
    Real AI Endpoint using Alibaba Cloud Qwen (DashScope).
    """
    user_msg = request.message
    
    # System prompt to guide the AI to return JSON matching our schema
    system_prompt = """
    You are an expert crypto trading strategy assistant.
    Your goal is to parse the user's request and create a trading strategy in JSON format.
    
    The JSON structure MUST match this Pydantic schema:
    {
        "text": "A brief explanation of what you created.",
        "strategy": {
            "name": "Strategy Name",
            "description": "Short description",
            "market": "BTC-PERP or ETH-PERP depending on user",
            "timeframe": "1m, 5m, 15m, 1h, 4h, 1d",
            "indicators": [
                { "id": "rsi_1", "type": "RSI, SMA, EMA, MACD", "params": { "length": 14, "source": "close" } }
            ],
            "rules": [
                { "condition": "rsi_1 < 30", "action": "BUY" },
                { "condition": "rsi_1 > 70", "action": "SELL" }
            ],
            "risk": {
                 "stop_loss_pct": 2.0,
                 "take_profit_pct": 5.0,
                 "max_leverage": 5,
                 "position_size_pct": 10.0
            }
        }
    }
    
    If the user just says "hello" or asks a general question without strategy intent, set "strategy" to null in the JSON.
    ALWAYS RETURN RAW JSON only. No markdown formatting like ```json ... ```.
    """

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_msg}
    ]

    try:
        response = Generation.call(
            Generation.Models.qwen_turbo,
            messages=messages,
            result_format='message'  # set the result to be "message" format.
        )

        if response.status_code == 200:
            content = response.output.choices[0].message.content
            print(f"AI Response: {content}") # Debug log
            
            # Clean up potential markdown formatting
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            
            try:
                data = json.loads(content)
                
                strategy_data = data.get("strategy")
                strategy_obj = None
                
                if strategy_data:
                    # Map JSON to Pydantic models
                    indicators = [Indicator(**i) for i in strategy_data.get("indicators", [])]
                    rules = [Rule(**r) for r in strategy_data.get("rules", [])]
                    risk = RiskSettings(**strategy_data.get("risk", {}))
                    
                    strategy_obj = Strategy(
                        name=strategy_data["name"],
                        description=strategy_data["description"],
                        market=strategy_data["market"],
                        timeframe=strategy_data["timeframe"],
                        indicators=indicators,
                        rules=rules,
                        risk=risk
                    )

                return ChatResponse(
                    text=data.get("text", "Here is your strategy."),
                    strategy=strategy_obj
                )
            except json.JSONDecodeError:
                return ChatResponse(text="Failed to parse AI response. Please try again.")
        else:
            return ChatResponse(text=f"AI Error: {response.code} - {response.message}")
            
    except Exception as e:
        print(f"Error calling DashScope: {e}")
        return ChatResponse(text=f"Internal Server Error: {str(e)}")
