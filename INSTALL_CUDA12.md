# DeepSeek-OCR Installation Guide for CUDA 12.0+

This guide provides installation instructions for DeepSeek-OCR when using **CUDA driver 12.0 or newer**.

## Background

The official README specifies CUDA 11.8 + PyTorch 2.6.0, but this combination has compatibility issues:
- **PyTorch 2.6.0** does not support CUDA 12.0 (only cu118, cu124, cu126)
- **vLLM 0.8.5** only provides a **cu121** wheel
- **CUDA driver 12.0** is the oldest version available on newer systems

## Solution: Use PyTorch 2.5.1 with CUDA 12.1

The recommended approach is to use **PyTorch 2.5.1 with cu121** to match the vLLM wheel. Your CUDA 12.0 driver supports CUDA 12.1 applications through forward compatibility.

## Installation Steps

### 1. Create Python Environment

```bash
conda create -n deepseek-ocr python=3.12.9 -y
conda activate deepseek-ocr
```

### 2. Install PyTorch 2.5.1 with CUDA 12.1

```bash
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
  --index-url https://download.pytorch.org/whl/cu121
```

### 3. Install vLLM 0.8.5

Download the vLLM 0.8.5+cu121 wheel from the [GitHub releases page](https://github.com/vllm-project/vllm/releases/tag/v0.8.5):

```bash
# Download the cu121 wheel file, then:
pip install vllm-0.8.5+cu121-cp38-abi3-manylinux1_x86_64.whl
```

**Note:** You may see a warning about vLLM requiring `transformers>=4.51.1`. This can be safely ignored when running both vLLM and transformers code in the same environment.

### 4. Install Additional Dependencies

```bash
pip install -r requirements.txt
pip install flash-attn==2.7.3 --no-build-isolation
```

## Why This Works

| Component | Version | Compatibility |
|-----------|---------|---------------|
| CUDA Driver | 12.0 | ✅ Supports CUDA 12.1 apps (forward compatibility) |
| PyTorch | 2.5.1+cu121 | ✅ Officially supports CUDA 12.1 |
| vLLM | 0.8.5+cu121 | ✅ Matches PyTorch CUDA version |
| Flash Attention | 2.7.3 | ✅ Compiles with CUDA 12.0/12.1 |

**Important:** Mixing CUDA versions (e.g., PyTorch cu124 + vLLM cu121) causes binary incompatibility and runtime errors.

## Alternative Options

### Option A: Use Upstream vLLM (Newer Versions)

As of October 23, 2025, DeepSeek-OCR is officially supported in upstream vLLM. Consider using the latest version:

```bash
# Create fresh environment
uv venv
source .venv/bin/activate

# Install latest vLLM from nightly
uv pip install -U vllm --pre --extra-index-url https://wheels.vllm.ai/nightly
```

Then use the simplified API:

```python
from vllm import LLM, SamplingParams
from vllm.model_executor.models.deepseek_ocr import NGramPerReqLogitsProcessor
from PIL import Image

# Create model instance
llm = LLM(
    model="deepseek-ai/DeepSeek-OCR",
    enable_prefix_caching=False,
    mm_processor_cache_gb=0,
    logits_processors=[NGramPerReqLogitsProcessor]
)

# Prepare input
image = Image.open("your_image.png").convert("RGB")
prompt = "<image>\nFree OCR."

model_input = [{
    "prompt": prompt,
    "multi_modal_data": {"image": image}
}]

sampling_param = SamplingParams(
    temperature=0.0,
    max_tokens=8192,
    extra_args=dict(
        ngram_size=30,
        window_size=90,
        whitelist_token_ids={128821, 128822},  # <td>, </td>
    ),
    skip_special_tokens=False,
)

# Generate output
model_outputs = llm.generate(model_input, sampling_param)
print(model_outputs[0].outputs[0].text)
```

### Option B: Build vLLM from Source

If you prefer to use PyTorch 2.6.0 with cu124 or cu126:

```bash
# Install PyTorch 2.6.0 with your preferred CUDA version
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 \
  --index-url https://download.pytorch.org/whl/cu124

# Build vLLM from source to match your CUDA version
git clone https://github.com/vllm-project/vllm.git
cd vllm
git checkout v0.8.5
pip install -e .
```

## Verification

After installation, verify your setup:

```python
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")

import vllm
print(f"vLLM version: {vllm.__version__}")
```

Expected output:
```
PyTorch version: 2.5.1+cu121
CUDA available: True
CUDA version: 12.1
vLLM version: 0.8.5+cu121
```

## Troubleshooting

### CUDA Driver Mismatch Errors

If you see "CUDA driver mismatch" or "unspecified launch failure":
- Ensure PyTorch and vLLM use the **same CUDA version** (both cu121)
- Verify your driver version: `nvidia-smi`
- CUDA driver 12.0 requires at least version 525.60.13 (Linux) or 527.41 (Windows)

### Flash Attention Build Errors

If flash-attn fails to compile:
```bash
# Ensure you have the correct build tools
pip install ninja packaging wheel
pip install flash-attn==2.7.3 --no-build-isolation
```

### ImportError or Version Conflicts

If you encounter transformers version conflicts:
- This is expected and can be safely ignored
- Both vLLM and transformers will work correctly despite the warning
- If issues persist, create a fresh conda environment

## Running the Model

After successful installation, refer to the main README for usage examples:

- **vLLM Inference**: See [vLLM-Inference](#) section
- **Transformers Inference**: See [Transformers-Inference](#) section
- **Examples**: Check `DeepSeek-OCR-master/DeepSeek-OCR-vllm/` and `DeepSeek-OCR-master/DeepSeek-OCR-hf/` directories

## References

- [Official DeepSeek-OCR Repository](https://github.com/deepseek-ai/DeepSeek-OCR)
- [vLLM v0.8.5 Release](https://github.com/vllm-project/vllm/releases/tag/v0.8.5)
- [PyTorch Previous Versions](https://pytorch.org/get-started/previous-versions/)
- [CUDA Compatibility Guide](https://docs.nvidia.com/deploy/cuda-compatibility/)
