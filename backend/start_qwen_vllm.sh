#!/bin/bash
# Start Qwen3-VL with vLLM for technical drawing analysis

echo "🚀 Starting Qwen3-VL-235B-A22B-Instruct with vLLM..."
echo ""
echo "Model: Qwen/Qwen3-VL-235B-A22B-Instruct"
echo "Tensor Parallel: 8 GPUs"
echo "Max Model Length: 8192 tokens"
echo ""

# Check if model is already downloaded
MODEL_PATH="$HOME/.cache/huggingface/hub"
if [ ! -d "$MODEL_PATH" ]; then
    echo "⚠️  Model not found in cache. It will be downloaded on first run."
    echo "   This is a 235B parameter model - download will take time!"
fi

# Start vLLM with Qwen3-VL
python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-VL-235B-A22B-Instruct \
    --tensor-parallel-size 8 \
    --max-model-len 8192 \
    --trust-remote-code \
    --gpu-memory-utilization 0.90 \
    --enforce-eager \
    --port 8000 \
    --host 0.0.0.0

# Alternative for FP8 quantized version (faster, less memory):
# python3 -m vllm.entrypoints.openai.api_server \
#     --model Qwen/Qwen3-VL-235B-A22B-Instruct-FP8 \
#     --tensor-parallel-size 8 \
#     --mm-encoder-tp-mode data \
#     --enable-expert-parallel \
#     --max-model-len 8192 \
#     --trust-remote-code \
#     --gpu-memory-utilization 0.90 \
#     --port 8000 \
#     --host 0.0.0.0
