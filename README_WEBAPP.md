# DeepSeek-OCR Web Application

A web-based frontend for DeepSeek-OCR optimized for **technical drawings, machine parts, and engineering documentation**.

## Features

### 🎯 Specialized for Technical Drawings
- **Dimension Extraction**: Automatically detect measurements, tolerances, and geometric dimensions
- **Part Number Recognition**: Identify part numbers, item numbers, and callouts
- **BOM Extraction**: Extract Bill of Materials tables with structure preservation
- **Visual Grounding**: Bounding boxes highlight detected elements on the drawing
- **Multiple Analysis Modes**: Choose the right mode for your drawing type

### 🚀 Technical Stack
- **Backend**: FastAPI + existing vLLM installation (no Docker needed!)
- **Frontend**: React + Vite + TailwindCSS
- **Model**: DeepSeek-OCR with vLLM 0.8.5 (already installed)

## Architecture

```
┌─────────────────────┐
│   React Frontend    │  <- http://localhost:5173
│   (Vite Dev Server) │
└──────────┬──────────┘
           │ HTTP API
           ▼
┌─────────────────────┐
│  FastAPI Backend    │  <- http://localhost:8000
│                     │
│  ┌───────────────┐  │
│  │ ocr_service.py│  │  Wraps existing scripts
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │ vLLM Engine   │  │  Uses installed vLLM 0.8.5
│  │ (persistent)  │  │
│  └───────────────┘  │
└─────────────────────┘
           │
           ▼
    ┌─────────────┐
    │ GPU (CUDA)  │
    └─────────────┘
```

## Installation

### Prerequisites
- Python 3.9+ with existing DeepSeek-OCR installation
- Node.js 18+ and npm
- CUDA-capable GPU (already set up with vLLM)

### Backend Setup

The backend uses your **existing vLLM installation** - no need to reinstall!

```bash
# Install backend dependencies only
pip install -r backend/requirements.txt
```

That's it! The backend imports from `DeepSeek-OCR-master/DeepSeek-OCR-vllm/`

### Frontend Setup

```bash
cd frontend
npm install
```

## Usage

### Starting the Application

**Option 1: Using startup scripts (recommended)**

Open two terminal windows:

**Terminal 1 - Backend:**
```bash
chmod +x start_backend.sh
./start_backend.sh
```

**Terminal 2 - Frontend:**
```bash
chmod +x start_frontend.sh
./start_frontend.sh
```

**Option 2: Manual startup**

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Accessing the Application

1. Open your browser to **http://localhost:5173**
2. Select an analysis mode (Technical Drawing, Dimensions, Parts, BOM, etc.)
3. Upload a technical drawing (drag & drop or click to browse)
4. Wait for processing (typically 2-10 seconds depending on image size)
5. View results with interactive bounding boxes

## Analysis Modes

### 📐 Technical Drawing (Default)
Complete analysis extracting:
- Dimensions and measurements
- Part numbers and callouts
- Tables and BOMs
- Drawing metadata (title, number, revision, scale)
- All text annotations

### 📏 Dimensions Only
Focused extraction of:
- Linear dimensions (length, width, height)
- Diameters (Ø) and radii (R)
- Angular dimensions
- Tolerances (±)
- Units of measurement

### 🔢 Part Numbers
Identifies:
- Part numbers (P/N)
- Item numbers
- Position callouts
- Reference designators

### 📋 BOM Extraction
Extracts tables including:
- Bills of Materials
- Part lists
- Dimension tables
- Preserves table structure

### 📄 Plain OCR
Simple text extraction without specialized analysis

## API Endpoints

### `POST /api/ocr`
Process a single technical drawing

**Parameters:**
- `file`: Image file (JPG, PNG, TIFF)
- `mode`: Analysis mode (default: `technical_drawing`)
- `grounding`: Enable bounding boxes (default: `true`)
- `extract_dimensions`: Extract dimensions (default: `true`)
- `extract_part_numbers`: Extract part numbers (default: `true`)
- `extract_tables`: Extract tables (default: `true`)
- `base_size`: Base image size (default: `1024`)
- `image_size`: Crop size (default: `640`)
- `crop_mode`: Enable dynamic cropping (default: `true`)

**Response:**
```json
{
  "text": "Full extracted text",
  "markdown": "Formatted markdown",
  "detected_elements": [...],
  "dimensions": [...],
  "part_numbers": [...],
  "tables": [...],
  "drawing_title": "...",
  "drawing_number": "...",
  "revision": "...",
  "scale": "...",
  "image_width": 2000,
  "image_height": 1500,
  "processing_time": 3.45
}
```

### `POST /api/ocr/batch`
Process multiple drawings (max 50)

### `POST /api/ocr/pdf`
Process multi-page PDF documents

### `GET /api/modes`
List available analysis modes

### `GET /health`
Health check and model status

## Performance

- **Single Image**: 2-10 seconds (depending on size and complexity)
- **Batch Processing**: ~2500 tokens/sec on A100
- **GPU Memory**: ~10-20GB depending on settings
- **Model Loading**: One-time at startup (~30 seconds)

## Configuration

### Backend Configuration

Edit `backend/ocr_service.py` to adjust:

```python
# vLLM settings
self.model = LLM(
    model=self.config.MODEL_PATH,
    tensor_parallel_size=1,
    gpu_memory_utilization=0.9,  # Adjust GPU memory usage
    max_model_len=8192,           # Max sequence length
    max_num_seqs=128,             # Batch size
)

# Sampling parameters
sampling_params = SamplingParams(
    temperature=0.0,              # Deterministic
    max_tokens=8192,              # Max output length
)
```

### Frontend Configuration

Edit `frontend/src/App.jsx`:

```javascript
const API_URL = 'http://localhost:8000';  // Backend URL
```

## Troubleshooting

### Backend won't start
- **Issue**: `ModuleNotFoundError: No module named 'vllm'`
- **Solution**: Make sure you're in the environment where vLLM is installed:
  ```bash
  which python  # Should point to your vLLM environment
  pip list | grep vllm  # Should show vllm-0.8.5
  ```

### Frontend build errors
- **Issue**: `Cannot find module 'tailwindcss'`
- **Solution**: Reinstall dependencies:
  ```bash
  cd frontend
  rm -rf node_modules package-lock.json
  npm install
  ```

### CORS errors
- Check that backend is running on port 8000
- Frontend CORS is configured for localhost:5173 and localhost:3000
- Edit `backend/main.py` to add more origins if needed

### Model loading issues
- **Issue**: `CUDA out of memory`
- **Solution**: Reduce `gpu_memory_utilization` in `ocr_service.py`

### Slow processing
- Check GPU utilization: `nvidia-smi`
- Reduce `base_size` and `image_size` for faster processing
- Disable `crop_mode` for simpler images

## Development

### Backend hot reload (disabled by default)
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Note: Hot reload causes model to reinitialize on every change (slow!)

### Frontend hot reload (enabled)
Vite automatically hot-reloads on file changes

## Extending

### Adding Custom Analysis Modes

1. Add prompt to `backend/ocr_service.py`:
```python
self.prompts = {
    "my_custom_mode": """<image>
    Custom analysis instructions here..."""
}
```

2. Add mode to `frontend/src/components/ModeSelector.jsx`:
```javascript
{
  id: 'my_custom_mode',
  name: 'Custom Analysis',
  icon: '🔧',
  description: 'My custom analysis'
}
```

3. Update API endpoint in `backend/main.py` to handle new mode

## Production Deployment

For production, you'll want to:

1. Build frontend:
```bash
cd frontend
npm run build
```

2. Serve with production server:
```bash
# Backend
gunicorn -w 1 -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:8000

# Frontend (serve dist/)
npx serve -s dist -p 5173
```

3. Use Nginx as reverse proxy:
```nginx
server {
    listen 80;

    location /api {
        proxy_pass http://localhost:8000;
    }

    location / {
        proxy_pass http://localhost:5173;
    }
}
```

## Credits

- **Repository**: [re-cinq/DeepSeek-OCR-Test](https://github.com/re-cinq/DeepSeek-OCR-Test)
- **DeepSeek-OCR**: [deepseek-ai/DeepSeek-OCR](https://github.com/deepseek-ai/DeepSeek-OCR)
- **vLLM**: High-performance LLM inference

## License

Same as DeepSeek-OCR parent project
