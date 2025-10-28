# Systemd Service Setup

This directory contains systemd service files to run the DeepSeek OCR application as background services.

## Installation Steps

### 1. Edit the service files

Replace `YOUR_USERNAME` with your actual username in both files:
- `deepseek-ocr-backend.service`
- `deepseek-ocr-frontend.service`

Also verify the paths match your installation:
- Repository path: `/home/YOUR_USERNAME/DeepSeek-OCR-Test`
- Virtual environment: `/home/YOUR_USERNAME/DeepSeek-OCR-Test/venv`
- Node.js path: check with `which node` and `which npm`

### 2. Copy service files to systemd

```bash
sudo cp deepseek-ocr-backend.service /etc/systemd/system/
sudo cp deepseek-ocr-frontend.service /etc/systemd/system/
```

### 3. Create log files

```bash
sudo touch /var/log/deepseek-ocr-backend.log
sudo touch /var/log/deepseek-ocr-frontend.log
sudo chown YOUR_USERNAME:YOUR_USERNAME /var/log/deepseek-ocr-backend.log
sudo chown YOUR_USERNAME:YOUR_USERNAME /var/log/deepseek-ocr-frontend.log
```

### 4. Enable and start services

```bash
# Reload systemd to recognize new services
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable deepseek-ocr-backend
sudo systemctl enable deepseek-ocr-frontend

# Start services now
sudo systemctl start deepseek-ocr-backend
sudo systemctl start deepseek-ocr-frontend
```

## Managing Services

### Check status
```bash
sudo systemctl status deepseek-ocr-backend
sudo systemctl status deepseek-ocr-frontend
```

### View logs
```bash
# Real-time logs
sudo journalctl -u deepseek-ocr-backend -f
sudo journalctl -u deepseek-ocr-frontend -f

# Or view log files directly
tail -f /var/log/deepseek-ocr-backend.log
tail -f /var/log/deepseek-ocr-frontend.log
```

### Restart services
```bash
sudo systemctl restart deepseek-ocr-backend
sudo systemctl restart deepseek-ocr-frontend
```

### Stop services
```bash
sudo systemctl stop deepseek-ocr-backend
sudo systemctl stop deepseek-ocr-frontend
```

### Disable services (prevent auto-start on boot)
```bash
sudo systemctl disable deepseek-ocr-backend
sudo systemctl disable deepseek-ocr-frontend
```

## Alternative: Screen Method (Recommended for Conda Environments)

**This is the easiest method if you're using conda instead of venv!**

We provide automated scripts:

```bash
# Start both services in background
./start_all_background.sh

# Check status
./status_background.sh

# Stop all services
./stop_all_background.sh
```

### Manual screen usage:

### Using screen:

```bash
# Start backend in screen
screen -S deepseek-backend
cd ~/DeepSeek-OCR-Test/backend
./start_backend.sh
# Press Ctrl+A, then D to detach

# Start frontend in screen
screen -S deepseek-frontend
cd ~/DeepSeek-OCR-Test/frontend
npm run dev -- --host 0.0.0.0
# Press Ctrl+A, then D to detach

# List screens
screen -ls

# Reattach to a screen
screen -r deepseek-backend
screen -r deepseek-frontend

# Kill a screen session
screen -X -S deepseek-backend quit
```

### Using tmux:

```bash
# Start backend in tmux
tmux new -s deepseek-backend
cd ~/DeepSeek-OCR-Test/backend
./start_backend.sh
# Press Ctrl+B, then D to detach

# Start frontend in tmux
tmux new -s deepseek-frontend
cd ~/DeepSeek-OCR-Test/frontend
npm run dev -- --host 0.0.0.0
# Press Ctrl+B, then D to detach

# List sessions
tmux ls

# Reattach to a session
tmux attach -t deepseek-backend
tmux attach -t deepseek-frontend

# Kill a session
tmux kill-session -t deepseek-backend
```

## Alternative: nohup Method

Simple background execution with nohup:

```bash
# Backend
cd ~/DeepSeek-OCR-Test/backend
nohup ./start_backend.sh > backend.log 2>&1 &
echo $! > backend.pid

# Frontend
cd ~/DeepSeek-OCR-Test/frontend
nohup npm run dev -- --host 0.0.0.0 > frontend.log 2>&1 &
echo $! > frontend.pid

# Check logs
tail -f backend.log
tail -f frontend.log

# Stop processes
kill $(cat backend.pid)
kill $(cat frontend.pid)
```

## Troubleshooting

### Service fails to start
1. Check logs: `sudo journalctl -u deepseek-ocr-backend -n 50`
2. Verify paths in service file are correct
3. Check permissions on log files
4. Ensure virtual environment is activated correctly

### Frontend can't find node/npm
1. Find node path: `which node`
2. Update `Environment="PATH=..."` in service file
3. Reload and restart: `sudo systemctl daemon-reload && sudo systemctl restart deepseek-ocr-frontend`

### Backend GPU issues
1. Ensure user has GPU access: `nvidia-smi`
2. Check CUDA environment variables in service file
3. Verify vLLM installation: `source venv/bin/activate && pip show vllm`
