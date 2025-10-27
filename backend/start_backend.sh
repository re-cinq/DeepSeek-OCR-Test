#!/bin/bash
# Start Backend with correct vLLM settings

echo "🚀 Starting Qwen3-VL Backend..."
echo ""

# Set vLLM to use V0 engine (more stable)
export VLLM_USE_V1=0

# Start FastAPI backend
python main.py
