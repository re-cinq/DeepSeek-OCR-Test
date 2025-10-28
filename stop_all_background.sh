#!/bin/bash
# Stop both backend and frontend screen sessions

echo "🛑 Stopping DeepSeek OCR background services..."
echo ""

# Stop backend
if screen -list | grep -q "deepseek-backend"; then
    echo "Stopping backend..."
    screen -X -S deepseek-backend quit
    echo "✓ Backend stopped"
else
    echo "Backend not running"
fi

# Stop frontend
if screen -list | grep -q "deepseek-frontend"; then
    echo "Stopping frontend..."
    screen -X -S deepseek-frontend quit
    echo "✓ Frontend stopped"
else
    echo "Frontend not running"
fi

echo ""
echo "✅ All services stopped"
