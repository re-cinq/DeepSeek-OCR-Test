#!/bin/bash
# Start Backend with correct vLLM settings

echo "🚀 Starting Qwen3-VL Backend..."
echo ""
echo "Model: Qwen3-VL-8B-Thinking"
echo "Engine: V1 (with eager mode - no flash-attn)"
echo "GPU Memory: 90% utilization"
echo ""

# V1 engine is auto-selected for Qwen3-VL
export VLLM_USE_V1=1

# Start FastAPI backend
python main.py
