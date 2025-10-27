#!/bin/bash
# Start Backend with correct vLLM settings

echo "🚀 Starting Qwen3-VL Backend..."
echo ""
echo "Model: Qwen3-VL-8B-Instruct (non-reasoning, direct answers)"
echo "Engine: V1 (with flash-attn auto-detection)"
echo "GPU Memory: 90% utilization"
echo ""
echo "Note: System will try flash-attn first, fallback to eager mode if needed"
echo "Watch startup logs for: 'Using Flash Attention backend' or 'fallback to eager mode'"
echo ""

# V1 engine is auto-selected for Qwen3-VL
export VLLM_USE_V1=1

# Start FastAPI backend
python main.py
