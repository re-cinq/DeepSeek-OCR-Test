#!/bin/bash
# Start Qwen3-VL with vLLM for technical drawing analysis

echo "🚀 Starting Qwen3-VL-30B-A3B-Instruct with vLLM..."
echo ""
echo "Model: Qwen/Qwen3-VL-30B-A3B-Instruct"
echo "Tensor Parallel: 1 GPU (can use 2 for better performance)"
echo "Max Model Length: 8192 tokens"
echo "Memory Required: ~15-20GB VRAM"
echo ""

# Check if model is already downloaded
MODEL_PATH="$HOME/.cache/huggingface/hub"
if [ ! -d "$MODEL_PATH" ]; then
    echo "⚠️  Model not found in cache. It will be downloaded on first run."
    echo "   This is a 30B parameter model (3B active) - download ~20GB"
fi

echo ""
echo "Note: Backend (main.py) uses AsyncLLMEngine directly."
echo "This script is only needed if you want to run vLLM as a separate API server."
echo ""
read -p "Press Enter to start vLLM API server, or Ctrl+C to cancel..."
echo ""

# Start vLLM with Qwen3-VL-30B (1 GPU)
python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-VL-30B-A3B-Instruct \
    --tensor-parallel-size 1 \
    --max-model-len 8192 \
    --trust-remote-code \
    --gpu-memory-utilization 0.90 \
    --port 8001 \
    --host 0.0.0.0

# For 2 GPUs (better performance):
# python3 -m vllm.entrypoints.openai.api_server \
#     --model Qwen/Qwen3-VL-30B-A3B-Instruct \
#     --tensor-parallel-size 2 \
#     --max-model-len 8192 \
#     --trust-remote-code \
#     --gpu-memory-utilization 0.90 \
#     --port 8001 \
#     --host 0.0.0.0
