#!/bin/bash
# Start DeepSeek-OCR Backend Server

echo "🚀 Starting DeepSeek-OCR Backend..."
echo ""

# Check if FastAPI is installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing backend dependencies..."
    pip install -r backend/requirements.txt
    echo ""
fi

# Verify installation
if ! python -c "import fastapi, uvicorn, pydantic" 2>/dev/null; then
    echo "❌ Failed to install backend dependencies"
    echo "Please run manually: pip install -r backend/requirements.txt"
    exit 1
fi

echo "✓ Backend dependencies ready"
echo "✓ Using existing vLLM installation from DeepSeek-OCR-master/"
echo ""
echo "Starting FastAPI server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Change to backend directory and start server
cd backend
python main.py
