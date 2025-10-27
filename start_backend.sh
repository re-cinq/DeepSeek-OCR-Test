#!/bin/bash
# Start DeepSeek-OCR Backend Server

echo "🚀 Starting DeepSeek-OCR Backend..."
echo ""

# Check if backend requirements are installed
if [ ! -d "backend/__pycache__" ]; then
    echo "📦 Installing backend dependencies..."
    pip install -r backend/requirements.txt
fi

# Change to backend directory
cd backend

# Start FastAPI server
echo "✓ Backend dependencies ready"
echo "✓ Using existing vLLM installation from DeepSeek-OCR-master/"
echo ""
echo "Starting FastAPI server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

python main.py
