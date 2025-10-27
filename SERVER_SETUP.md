# Server Setup Guide

## Setting up DeepSeek-OCR Web App on Your Server

Repository: https://github.com/re-cinq/DeepSeek-OCR-Test

## Prerequisites on Server

- Ubuntu/Debian server with GPU
- CUDA installed
- Python 3.9+
- Node.js 18+
- Git

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/re-cinq/DeepSeek-OCR-Test.git
cd DeepSeek-OCR-Test
```

### 2. Set Up Python Environment

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install existing DeepSeek-OCR requirements
pip install -r requirements.txt

# Install backend requirements
pip install -r backend/requirements.txt
```

### 3. Set Up Frontend

```bash
cd frontend
npm install
cd ..
```

### 4. Verify Setup

```bash
python test_setup.py
```

This will check:
- Python version and packages
- GPU/CUDA availability
- DeepSeek-OCR files
- Backend and frontend files

## Running the Application

### Development Mode

**Option 1: Using startup scripts**

Terminal 1 (Backend):
```bash
./start_backend.sh
```

Terminal 2 (Frontend):
```bash
./start_frontend.sh
```

**Option 2: Using tmux or screen**

```bash
# Start backend in background
tmux new -s deepseek-backend -d './start_backend.sh'

# Start frontend in background
tmux new -s deepseek-frontend -d './start_frontend.sh'

# Check sessions
tmux ls

# Attach to a session
tmux attach -t deepseek-backend
```

### Production Mode

For production deployment on server:

#### 1. Build Frontend

```bash
cd frontend
npm run build
cd ..
```

#### 2. Set Up Systemd Services

Create backend service: `/etc/systemd/system/deepseek-backend.service`

```ini
[Unit]
Description=DeepSeek-OCR Backend API
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/DeepSeek-OCR-Test
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python backend/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create frontend service: `/etc/systemd/system/deepseek-frontend.service`

```ini
[Unit]
Description=DeepSeek-OCR Frontend
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/DeepSeek-OCR-Test/frontend
ExecStart=/usr/bin/npx serve -s dist -p 5173
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable deepseek-backend deepseek-frontend
sudo systemctl start deepseek-backend deepseek-frontend

# Check status
sudo systemctl status deepseek-backend
sudo systemctl status deepseek-frontend
```

#### 3. Set Up Nginx Reverse Proxy

Create Nginx config: `/etc/nginx/sites-available/deepseek-ocr`

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Change this

    # Increase max upload size for large drawings
    client_max_body_size 100M;

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Increase timeout for long processing
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/deepseek-ocr /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 4. Optional: Add SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Firewall Configuration

Allow necessary ports:

```bash
# For development
sudo ufw allow 8000  # Backend
sudo ufw allow 5173  # Frontend

# For production (with Nginx)
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
```

## Environment Configuration

### Backend Configuration

Edit `backend/ocr_service.py` to adjust GPU settings:

```python
self.model = LLM(
    model=self.config.MODEL_PATH,
    tensor_parallel_size=1,
    gpu_memory_utilization=0.9,  # Adjust based on GPU memory
    max_model_len=8192,
    max_num_seqs=128,
)
```

### Frontend Configuration

Edit `frontend/src/App.jsx` to use server URL:

```javascript
const API_URL = 'http://your-domain.com/api';  // Production
// const API_URL = 'http://localhost:8000';     // Development
```

Or use environment variable in `frontend/.env`:

```bash
VITE_API_URL=http://your-domain.com
```

Then in `App.jsx`:

```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

## Monitoring

### Check Logs

```bash
# Backend logs
sudo journalctl -u deepseek-backend -f

# Frontend logs
sudo journalctl -u deepseek-frontend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### GPU Monitoring

```bash
# Watch GPU usage
watch -n 1 nvidia-smi

# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"
```

### API Health Check

```bash
curl http://localhost:8000/health
```

## Performance Tuning

### For Limited GPU Memory

Reduce memory usage in `backend/ocr_service.py`:

```python
gpu_memory_utilization=0.7  # From 0.9
max_num_seqs=64              # From 128
```

### For Faster Processing

Adjust image processing:

```python
# In frontend or API calls
base_size = 768              # From 1024
image_size = 512             # From 640
crop_mode = False            # For simple images
```

## Backup and Updates

### Update from Git

```bash
cd DeepSeek-OCR-Test
git pull origin main

# Rebuild frontend if needed
cd frontend
npm install
npm run build
cd ..

# Restart services
sudo systemctl restart deepseek-backend deepseek-frontend
```

### Backup Important Files

```bash
# Backup configuration
tar -czf deepseek-backup-$(date +%Y%m%d).tar.gz \
  backend/ \
  frontend/src/ \
  frontend/package.json \
  *.sh \
  *.md
```

## Troubleshooting

### Backend won't start

```bash
# Check Python environment
source venv/bin/activate
which python
pip list | grep vllm

# Check logs
sudo journalctl -u deepseek-backend -n 100
```

### GPU not detected

```bash
# Check CUDA
nvidia-smi
nvcc --version

# Check PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

### Out of memory errors

1. Reduce `gpu_memory_utilization` in `backend/ocr_service.py`
2. Reduce `max_num_seqs`
3. Close other GPU processes: `fuser -v /dev/nvidia*`

### Port conflicts

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill process if needed
sudo kill -9 <PID>
```

## Security Recommendations

1. **Firewall**: Only expose necessary ports
2. **Authentication**: Add API authentication for production
3. **Rate Limiting**: Implement rate limiting on API
4. **File Validation**: Verify uploaded file types
5. **HTTPS**: Use SSL certificates in production
6. **Updates**: Keep dependencies updated
7. **Logging**: Monitor access logs for suspicious activity

## Support

For issues:
- Check logs: `sudo journalctl -u deepseek-backend -f`
- Run setup test: `python test_setup.py`
- See [README_WEBAPP.md](README_WEBAPP.md) for detailed documentation
- Open issue at: https://github.com/re-cinq/DeepSeek-OCR-Test/issues

## Quick Commands Reference

```bash
# Start services (development)
./start_backend.sh
./start_frontend.sh

# Start services (production)
sudo systemctl start deepseek-backend deepseek-frontend

# Stop services
sudo systemctl stop deepseek-backend deepseek-frontend

# Restart services
sudo systemctl restart deepseek-backend deepseek-frontend

# View logs
sudo journalctl -u deepseek-backend -f
sudo journalctl -u deepseek-frontend -f

# Check status
sudo systemctl status deepseek-backend
sudo systemctl status deepseek-frontend

# Test API
curl http://localhost:8000/health

# Monitor GPU
watch -n 1 nvidia-smi
```
