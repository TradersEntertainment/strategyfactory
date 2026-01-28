from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import chat
import backtest_api 

app = FastAPI(title="HyperQuant API")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for production (Railway) 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(backtest_api.router, prefix="/api/backtest", tags=["Backtest"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "HyperQuant API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
