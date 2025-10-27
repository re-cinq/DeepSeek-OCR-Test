#!/bin/bash
# Script to properly install flash-attn with correct CUDA version
# This fixes the ABI mismatch issue that was causing symbol errors

echo "🔧 Fixing flash-attn installation for better performance"
echo "========================================================"

# Check if we're in the right environment
echo ""
echo "Step 0: Checking environment..."
if ! python -c "import vllm" 2>/dev/null; then
    echo "❌ Error: vLLM not found in current environment"
    echo ""
    echo "Please activate the correct conda/venv environment first:"
    echo "  conda activate deepseek-ocr"
    echo "  # OR"
    echo "  source /path/to/venv/bin/activate"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✓ vLLM found in current environment"

# Step 1: Remove existing flash-attn
echo ""
echo "Step 1: Removing existing flash-attn..."
pip uninstall flash-attn -y

# Step 2: Check CUDA version
echo ""
echo "Step 2: Checking CUDA version..."
nvidia-smi --query-gpu=driver_version --format=csv,noheader
nvcc --version || echo "⚠️  nvcc not found, but that's ok if PyTorch has CUDA"

# Step 3: Check PyTorch CUDA version
echo ""
echo "Step 3: Checking PyTorch CUDA version..."
if ! python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')" 2>/dev/null; then
    echo "❌ Error: PyTorch not found or failed to import"
    echo "Cannot install flash-attn without PyTorch"
    exit 1
fi

# Step 4: Install flash-attn with proper compilation
echo ""
echo "Step 4: Installing flash-attn (this may take 5-10 minutes)..."
echo "Building from source to match your PyTorch/CUDA versions..."
echo "⏳ This will compile C++/CUDA code, please be patient..."

# Install with no binary to force compilation with correct flags
MAX_JOBS=4 pip install flash-attn --no-build-isolation --verbose

# Step 5: Verify installation
echo ""
echo "Step 5: Verifying flash-attn installation..."
python -c "
try:
    import flash_attn
    print('✓ flash-attn imported successfully')
    print(f'  Version: {flash_attn.__version__}')
except Exception as e:
    print(f'✗ Failed to import flash-attn: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ flash-attn installed successfully!"
    echo ""
    echo "Next step: Update qwen_vision_service.py to remove enforce_eager=True"
    echo "Then restart the backend: ./start_backend.sh"
else
    echo ""
    echo "❌ flash-attn installation failed"
    echo "You can continue without it (slower) or try manual installation"
    exit 1
fi
