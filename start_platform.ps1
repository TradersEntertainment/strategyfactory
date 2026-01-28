Write-Host "Starting Hyperliquid Platform..."

# Start Backend
Write-Host "Starting Backend on Port 8000..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; uvicorn main:app --reload --port 8000"

# Start Frontend
Write-Host "Starting Frontend on Port 3000..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "Services started in new windows."
