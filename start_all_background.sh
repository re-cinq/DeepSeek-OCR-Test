#!/bin/bash
# Start both backend and frontend in screen sessions

echo "🚀 Starting DeepSeek OCR in background..."
echo ""

# Check if screen is installed
if ! command -v screen &> /dev/null; then
    echo "❌ screen is not installed. Installing..."
    apt-get update && apt-get install -y screen
fi

# Stop existing sessions if they exist
screen -X -S deepseek-backend quit 2>/dev/null
screen -X -S deepseek-frontend quit 2>/dev/null

echo "📡 Starting Backend in screen session 'deepseek-backend'..."
cd ~/DeepSeek-OCR-Test/backend
screen -dmS deepseek-backend bash -c "source ~/.bashrc && conda activate deepseek-ocr && ./start_backend.sh"

echo "🎨 Starting Frontend in screen session 'deepseek-frontend'..."
cd ~/DeepSeek-OCR-Test/frontend
screen -dmS deepseek-frontend bash -c "source ~/.bashrc && npm run dev -- --host 0.0.0.0"

echo ""
echo "✅ Services started in background!"
echo ""
echo "To view logs:"
echo "  Backend:  screen -r deepseek-backend"
echo "  Frontend: screen -r deepseek-frontend"
echo ""
echo "To detach from screen: Press Ctrl+A, then D"
echo ""
echo "To check status:"
echo "  screen -ls"
echo ""
echo "To stop services:"
echo "  ./stop_all_background.sh"
