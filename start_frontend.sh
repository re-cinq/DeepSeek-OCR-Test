#!/bin/bash
# Start DeepSeek-OCR Frontend

echo "🚀 Starting DeepSeek-OCR Frontend..."
echo ""

# Change to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

echo "✓ Frontend dependencies ready"
echo ""
echo "Starting Vite dev server on http://localhost:5173"
echo "Press Ctrl+C to stop"
echo ""

npm run dev
