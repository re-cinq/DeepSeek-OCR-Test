# Installation Guide

## Prerequisites

- Python 3.9+
- CUDA-capable GPU (for inference)
- Node.js 18+ (for frontend)
- Git

## Step-by-Step Installation

### 1. Clone Repository

```bash
git clone https://github.com/re-cinq/DeepSeek-OCR-Test.git
cd DeepSeek-OCR-Test
```

### 2. Install Main Dependencies (Required!)

These are the **heavy dependencies** including PyTorch, vLLM, and the DeepSeek model:

```bash
# This installs: torch, vllm, transformers, flash-attn, etc.
pip install -r requirements.txt
```

**⚠️ Important:** This step is REQUIRED and will take 10-30 minutes depending on your connection.

### 3. Install Backend Dependencies

These are lightweight web server dependencies:

```bash
# This installs: fastapi, uvicorn, pydantic, etc.
pip install -r backend/requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Verify Installation

```bash
# Run the environment check
python check_env.py
```

You should see all checkmarks (✓) for:
- PyTorch
- vLLM
- Transformers
- FastAPI
- Uvicorn
- Pydantic
- Pillow

### 6. Start the Application

**Terminal 1 - Backend:**
```bash
./start_backend.sh
```

Wait for:
```
✓ OCR service initialized successfully
✓ GPU available: True
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```bash
./start_frontend.sh
```

Wait for:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

### 7. Access the Application

Open your browser to: **http://localhost:5173**

---

## Dependency Overview

### Main Dependencies (requirements.txt)
**Size: ~10-20GB**

These are the ML/AI dependencies that take a long time to install:

- `torch` - PyTorch deep learning framework
- `torchvision` - Computer vision utilities
- `vllm-0.8.5` - Fast LLM inference engine (CUDA 11.8 build)
- `transformers` - HuggingFace model library
- `flash-attn` - Fast attention mechanism
- `einops` - Tensor operations
- `PyMuPDF` - PDF processing
- `Pillow` - Image processing

**Installation time:** 10-30 minutes

### Backend Dependencies (backend/requirements.txt)
**Size: ~50MB**

Lightweight web server dependencies:

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `python-multipart` - File upload handling
- `Pillow` - Image processing (also needed here)
- `PyMuPDF` - PDF processing (also needed here)

**Installation time:** 1-2 minutes

### Frontend Dependencies (frontend/package.json)
**Size: ~200MB**

React and build tools:

- `react` - UI framework
- `vite` - Build tool
- `tailwindcss` - CSS framework
- Various plugins

**Installation time:** 1-2 minutes

---

## Common Installation Issues

### Issue: "ModuleNotFoundError: No module named 'torch'"

**Cause:** Main dependencies (requirements.txt) not installed

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "ModuleNotFoundError: No module named 'vllm'"

**Cause:** Main dependencies not installed OR wrong Python environment

**Solution:**
```bash
# Check you're in the right environment
which python

# Install main dependencies
pip install -r requirements.txt
```

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Cause:** Backend dependencies not installed

**Solution:**
```bash
pip install -r backend/requirements.txt
```

### Issue: CUDA errors during installation

**Cause:** Wrong CUDA version or no GPU

**Solution:**

Check CUDA version:
```bash
nvcc --version
nvidia-smi
```

The requirements.txt is configured for CUDA 11.8. If you have a different version:

1. Modify `requirements.txt` to use a different vLLM build
2. Or install PyTorch for your CUDA version first:
   ```bash
   # For CUDA 12.1 (example)
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   ```

### Issue: Out of disk space

**Cause:** ML dependencies are large

**Solution:**
```bash
# Check disk space
df -h

# You need at least 30GB free for a full installation
```

---

## Using Virtual Environments (Recommended)

### Option 1: Python venv

```bash
# Create virtual environment
python -m venv deepseek-env

# Activate it
source deepseek-env/bin/activate  # Linux/Mac
# OR
deepseek-env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

### Option 2: Conda

```bash
# Create conda environment
conda create -n deepseek-ocr python=3.10

# Activate it
conda activate deepseek-ocr

# Install dependencies
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

---

## Verifying GPU Setup

```bash
# Check CUDA
nvidia-smi

# Check PyTorch can see GPU
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"

# Check vLLM
python -c "import vllm; print('vLLM installed')"
```

Expected output:
```
CUDA available: True
GPU: NVIDIA A100-SXM4-80GB
vLLM installed
```

---

## Production Installation

For production deployment on a server:

### 1. Install in virtual environment

```bash
cd /opt/deepseek-ocr
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

### 2. Build frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Set up systemd services

See [SERVER_SETUP.md](SERVER_SETUP.md) for complete systemd setup.

---

## Troubleshooting Installation

### Check Python version

```bash
python --version  # Should be 3.9+
```

### Check pip version

```bash
pip --version
# Upgrade if needed
pip install --upgrade pip
```

### Clear caches if installation fails

```bash
pip cache purge
rm -rf ~/.cache/pip
```

### Install with verbose output

```bash
pip install -r requirements.txt -v
```

### Check specific package

```bash
pip show torch
pip show vllm
pip show fastapi
```

---

## Next Steps

After successful installation:

1. Read [QUICKSTART.md](QUICKSTART.md) for usage
2. Check [README_WEBAPP.md](README_WEBAPP.md) for features
3. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if issues arise

---

## Minimal Test

After installation, test that imports work:

```python
python << 'EOF'
import torch
import vllm
import transformers
import fastapi
import uvicorn
print("✓ All core dependencies available")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
EOF
```

Expected output:
```
✓ All core dependencies available
PyTorch version: 2.x.x
CUDA available: True
```

---

## Getting Help

- Run `python check_env.py` to diagnose issues
- Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Check existing issues: https://github.com/re-cinq/DeepSeek-OCR-Test/issues
- Open new issue with output from `python check_env.py`
