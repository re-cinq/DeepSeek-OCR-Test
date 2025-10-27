# Flash-Attention Installation Guide

The system currently runs without flash-attention (slower, using eager mode). This guide shows how to enable flash-attention for 20-30% better performance.

## Current Status

Your error shows:
```
ModuleNotFoundError: No module named 'torch'
```

This means you're running in the `base` conda environment, which doesn't have the required packages.

## Solution: Activate the Correct Environment

You need to activate the environment where vLLM and PyTorch are installed.

### Step 1: Find Your Environment

Check which conda environments exist:
```bash
conda env list
```

Look for an environment with vLLM/PyTorch, typically named:
- `deepseek-ocr`
- `vllm`
- `qwen-vl`
- Or another name you created

### Step 2: Activate the Environment

```bash
conda activate <your-environment-name>
```

For example:
```bash
conda activate deepseek-ocr
```

### Step 3: Verify the Environment

Check that PyTorch and vLLM are available:
```bash
python -c "import torch; print(torch.__version__)"
python -c "import vllm; print(vllm.__version__)"
```

Both should work without errors.

### Step 4: Install Flash-Attention

Now run the fix script:
```bash
cd backend
./fix_flash_attn.sh
```

This will:
1. Remove old flash-attn (if any)
2. Check CUDA version compatibility
3. Compile flash-attn from source (5-10 minutes)
4. Verify installation

### Step 5: Restart Backend

After successful installation:
```bash
./start_backend.sh
```

Check the startup logs - you should see:
```
✓ Qwen3-VL AsyncLLMEngine initialized with flash-attn!
```

Instead of:
```
⚠️  flash-attn failed, falling back to eager mode...
```

## Alternative: Pre-built Wheels

If compilation fails, you can try pre-built wheels:

```bash
# For CUDA 12.1
pip install flash-attn --no-build-isolation

# For CUDA 11.8
pip install flash-attn==2.5.8
```

## If Flash-Attention Doesn't Work

The system will automatically fall back to eager mode. This is slower (~20-30%) but fully functional.

To use eager mode permanently without warning messages, you can manually set:
```python
# In qwen_vision_service.py, line 67
enforce_eager=True  # Force eager mode, skip flash-attn
```

## Troubleshooting

### Error: "No module named 'torch'"
- **Cause**: Wrong conda/venv environment
- **Fix**: Activate the environment with PyTorch/vLLM

### Error: "CUDA version mismatch"
- **Cause**: flash-attn compiled for different CUDA version
- **Fix**: Compile from source or use correct pre-built wheel

### Error: "undefined symbol"
- **Cause**: ABI incompatibility between flash-attn and PyTorch
- **Fix**: Compile flash-attn in the same environment as PyTorch

### Compilation takes too long
- **Cause**: Compiling CUDA kernels is slow
- **Solution**: Be patient, it's normal (5-10 minutes)
- **Speedup**: Set `MAX_JOBS=8` for faster compilation (if you have enough CPU cores)

## Performance Comparison

| Mode | Speed | Memory |
|------|-------|--------|
| Flash-attention | 100% (baseline) | Lower |
| Eager mode | ~70-80% | Higher |

**Recommendation**: Try to get flash-attention working for best performance, but eager mode is acceptable if you have issues.

## Current Working Mode

The backend is already configured to:
1. Try flash-attention first
2. Fall back to eager mode if it fails
3. Print clear messages about which mode is active

So the system **works fine without flash-attention**, it's just slower. This guide is only if you want to optimize performance.
