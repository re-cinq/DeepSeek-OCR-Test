#!/bin/bash
# Check status of background services

echo "📊 DeepSeek OCR Background Services Status"
echo "=========================================="
echo ""

# Check backend
if screen -list | grep -q "deepseek-backend"; then
    echo "✅ Backend: RUNNING"
    echo "   View logs: screen -r deepseek-backend"
else
    echo "❌ Backend: NOT RUNNING"
fi

# Check frontend
if screen -list | grep -q "deepseek-frontend"; then
    echo "✅ Frontend: RUNNING"
    echo "   View logs: screen -r deepseek-frontend"
else
    echo "❌ Frontend: NOT RUNNING"
fi

echo ""
echo "All screen sessions:"
screen -ls

echo ""
echo "To attach to a session: screen -r <name>"
echo "To detach: Ctrl+A, then D"
