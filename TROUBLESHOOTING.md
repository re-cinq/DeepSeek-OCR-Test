# Troubleshooting Guide

## Common Issues and Solutions

### Backend Issues

#### 1. ImportError: cannot import name 'Config' from 'config'

**Error:**
```
ImportError: cannot import name 'Config' from 'config'
```

**Solution:**
This was fixed in commit `12d437a`. Pull the latest changes:
```bash
git pull origin main
```

---

#### 2. ValueError: Model architectures ['TransformersForCausalLM'] failed to be inspected

**Error:**
```
ValueError: Model architectures ['TransformersForCausalLM'] failed to be inspected. Please check the logs for more details.
```

**Cause:**
The custom DeepSeek-OCR model architecture is not registered with vLLM.

**Solution:**
This was fixed in the latest commit. The model is now registered before initialization. Pull the latest changes:
```bash
git pull origin main
```

The fix adds:
```python
from vllm.model_executor.models.registry import ModelRegistry
from deepseek_ocr import DeepseekOCRForCausalLM

# Register the custom model
ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)
```

---

#### 3. ModuleNotFoundError: No module named 'vllm'

**Error:**
```
ModuleNotFoundError: No module named 'vllm'
```

**Solution:**
Make sure you're using the correct Python environment where vLLM is installed:
```bash
# Check which Python you're using
which python

# Verify vLLM is installed
pip list | grep vllm

# If not in the right environment, activate it
source /path/to/your/venv/bin/activate

# Or install vLLM (check main requirements.txt)
pip install -r requirements.txt
```

---

#### 4. ModuleNotFoundError: No module named 'fastapi'

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
Install backend dependencies:
```bash
pip install -r backend/requirements.txt
```

---

#### 5. CUDA out of memory

**Error:**
```
torch.cuda.OutOfMemoryError: CUDA out of memory
```

**Solution:**
Reduce GPU memory usage in `backend/ocr_service.py`:
```python
self.model = LLM(
    model=self.model_path,
    tensor_parallel_size=1,
    gpu_memory_utilization=0.7,  # Reduce from 0.9
    trust_remote_code=True,
    max_model_len=8192,
    max_num_seqs=64,              # Reduce from 128
)
```

---

#### 6. Model not found error

**Error:**
```
OSError: deepseek-ai/DeepSeek-OCR is not a local folder and is not a valid model identifier
```

**Solution:**
The model needs to be downloaded first. Check the DeepSeek-OCR main README for model download instructions, or update `MODEL_PATH` in `DeepSeek-OCR-master/DeepSeek-OCR-vllm/config.py` to point to your local model path.

---

#### 7. Port already in use

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
Check what's using port 8000:
```bash
lsof -i :8000
# Kill the process
kill -9 <PID>

# Or change the port in backend/main.py:
uvicorn.run(..., port=8001)
```

---

### Frontend Issues

#### 1. Node.js version too old - SyntaxError: Unexpected token '.'

**Error:**
```
SyntaxError: Unexpected token '.'
    at Loader.moduleStrategy (internal/modules/esm/translators.js:133:18)
```

**Cause:**
Node.js version is too old. Vite 5 requires Node.js 18 or higher.

**Solution:**

Check your Node version:
```bash
node --version
bash check_node.sh
```

Upgrade to Node.js 18+:

**Option 1: Using NodeSource (recommended for Ubuntu/Debian):**
```bash
# Remove old Node.js
sudo apt-get remove nodejs npm

# Install Node.js 20 (LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
node --version  # Should show v20.x.x
```

**Option 2: Using nvm:**
```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc

# Install Node.js 20
nvm install 20
nvm use 20
nvm alias default 20
```

**Option 3: Using Conda:**
```bash
conda install -c conda-forge nodejs=20
```

After upgrading:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
./start_frontend.sh
```

---

#### 2. Frontend won't start - tailwindcss error

**Error:**
```
npm error could not determine executable to run
```

**Solution:**
Manually create Tailwind config (already done in the repo):
```bash
cd frontend
npm install -D tailwindcss postcss autoprefixer
```

---

#### 3. Module not found errors

**Error:**
```
Cannot find module 'react' or its corresponding type declarations
```

**Solution:**
Reinstall node_modules:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

#### 4. Connection refused / Network error

**Error in browser:**
```
Failed to fetch
net::ERR_CONNECTION_REFUSED
```

**Solution:**
1. Make sure backend is running on port 8000
2. Check backend logs for errors
3. Verify CORS settings in `backend/main.py`:
```python
allow_origins=["http://localhost:5173", "http://your-domain.com"]
```

---

#### 5. Blank page / White screen

**Solution:**
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify API_URL in `frontend/src/App.jsx`:
```javascript
const API_URL = 'http://localhost:8000';
```

---

### Processing Issues

#### 1. Processing takes too long

**Solutions:**
1. Reduce image size before upload
2. Disable crop mode for simple images
3. Adjust processing parameters:
```python
# In API call or defaults
base_size = 768      # From 1024
image_size = 512     # From 640
crop_mode = False    # For simple images
```

---

#### 2. Bounding boxes not showing

**Solutions:**
1. Check "Show Bounding Boxes" checkbox is enabled
2. Verify `grounding=true` in API request
3. Check that model returned detected_elements in response
4. Look for JavaScript console errors

---

#### 3. Poor OCR quality

**Solutions:**
1. Use higher quality source images
2. Try different analysis modes
3. Enable crop_mode for large images
4. Increase base_size for detailed drawings:
```python
base_size = 1280     # From 1024
```

---

### Installation Issues

#### 1. Python version too old

**Error:**
```
SyntaxError: invalid syntax
```

**Solution:**
Upgrade to Python 3.9+:
```bash
python --version
# If < 3.9, install newer Python
sudo apt install python3.10
python3.10 -m venv venv
source venv/bin/activate
```

---

#### 2. Node.js version too old

**Error:**
```
npm ERR! engine Unsupported engine
```

**Solution:**
Upgrade to Node.js 18+:
```bash
node --version
# If < 18, install newer Node
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

---

#### 3. Git clone fails

**Error:**
```
fatal: repository not found
```

**Solution:**
Make sure you have access to the repository:
```bash
git clone https://github.com/re-cinq/DeepSeek-OCR-Test.git
# If private, you may need to authenticate
```

---

### System Issues

#### 1. Permission denied errors

**Error:**
```
Permission denied: './start_backend.sh'
```

**Solution:**
```bash
chmod +x start_backend.sh start_frontend.sh test_setup.py
```

---

#### 2. Disk space full

**Error:**
```
OSError: [Errno 28] No space left on device
```

**Solution:**
```bash
# Check disk space
df -h

# Clear npm cache
npm cache clean --force

# Clear pip cache
pip cache purge

# Clear temp files
rm -rf /tmp/*
```

---

#### 3. Too many open files

**Error:**
```
OSError: [Errno 24] Too many open files
```

**Solution:**
```bash
# Increase file descriptor limit
ulimit -n 4096

# Make permanent by adding to ~/.bashrc:
echo "ulimit -n 4096" >> ~/.bashrc
```

---

## Debugging Tips

### Enable verbose logging

**Backend:**
```python
# In backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```javascript
// In frontend/src/App.jsx
console.log('API_URL:', API_URL);
console.log('Request:', formData);
console.log('Response:', data);
```

### Check API health

```bash
# Basic health check
curl http://localhost:8000/health

# Test OCR endpoint
curl -X POST http://localhost:8000/api/ocr \
  -F "file=@test_image.jpg" \
  -F "mode=plain_ocr"
```

### Monitor GPU usage

```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# Check CUDA
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### Check service status (production)

```bash
# Systemd services
sudo systemctl status deepseek-backend
sudo systemctl status deepseek-frontend

# View logs
sudo journalctl -u deepseek-backend -f
sudo journalctl -u deepseek-frontend -f
```

---

## Performance Optimization

### For limited GPU memory

```python
# backend/ocr_service.py
gpu_memory_utilization=0.6  # From 0.9
max_num_seqs=32             # From 128
```

### For faster processing

```python
# Disable features for speed
crop_mode=False             # Skip multi-crop
base_size=768              # Smaller base size
grounding=False            # Skip bounding boxes
```

### For better quality

```python
# Increase for quality
base_size=1280             # Larger base
image_size=1024            # Larger crops
crop_mode=True             # Enable multi-crop
```

---

## Getting Help

1. **Run the test script:**
   ```bash
   python test_setup.py
   ```

2. **Check the documentation:**
   - [QUICKSTART.md](QUICKSTART.md)
   - [README_WEBAPP.md](README_WEBAPP.md)
   - [SERVER_SETUP.md](SERVER_SETUP.md)

3. **Open an issue:**
   - https://github.com/re-cinq/DeepSeek-OCR-Test/issues

4. **Include in bug reports:**
   - Error messages (full traceback)
   - Output of `python test_setup.py`
   - Backend logs
   - Browser console errors (F12)
   - System info: OS, Python version, Node version, GPU

---

## Quick Fix Commands

```bash
# Restart everything
sudo systemctl restart deepseek-backend deepseek-frontend

# Or in development
pkill -f "python backend/main.py"
pkill -f "npm run dev"
./start_backend.sh &
./start_frontend.sh &

# Clear all caches
pip cache purge
npm cache clean --force
rm -rf frontend/node_modules frontend/.vite

# Reinstall everything
pip install -r requirements.txt
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

# Check everything
python test_setup.py
curl http://localhost:8000/health
```

---

**Still having issues?** Open an issue with detailed error messages and system information!
