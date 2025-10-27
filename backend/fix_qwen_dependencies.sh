#!/bin/bash
# Fix dependencies for Qwen3-VL support

echo "🔧 Fixing dependencies for Qwen3-VL-30B-A3B-Instruct..."
echo ""

# Step 1: Fix huggingface-hub version conflict
echo "1️⃣ Downgrading huggingface-hub to <1.0..."
pip install 'huggingface-hub<1.0' --upgrade
echo "✅ huggingface-hub fixed"
echo ""

# Step 2: Upgrade transformers to latest version
echo "2️⃣ Upgrading transformers to latest version..."
pip install --upgrade transformers
echo "✅ transformers upgraded"
echo ""

# Step 3: Check if qwen3_vl_moe is supported
echo "3️⃣ Checking if qwen3_vl_moe architecture is supported..."
python -c "from transformers import AutoConfig; config = AutoConfig.from_pretrained('Qwen/Qwen3-VL-30B-A3B-Instruct'); print('✅ Model type supported:', config.model_type)" 2>&1

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  qwen3_vl_moe not yet in stable transformers release"
    echo "Installing transformers from source (latest main branch)..."
    echo ""

    # Install from source
    pip install git+https://github.com/huggingface/transformers.git

    echo ""
    echo "✅ Transformers installed from source"
    echo ""

    # Verify again
    echo "🔍 Verifying installation..."
    python -c "from transformers import AutoConfig; config = AutoConfig.from_pretrained('Qwen/Qwen3-VL-30B-A3B-Instruct', trust_remote_code=True); print('✅ Model type supported:', config.model_type)"
fi

echo ""
echo "4️⃣ Installing additional dependencies..."
pip install qwen-vl-utils==0.0.14
echo "✅ qwen-vl-utils installed"

echo ""
echo "✅ All dependencies fixed!"
echo ""
echo "You can now start the backend with:"
echo "  python main.py"
