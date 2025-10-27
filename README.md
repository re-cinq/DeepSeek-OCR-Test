# 💬 re:cinq Technical Drawing Chat System

A conversational AI system for analyzing technical drawings, powered by **Qwen3-VL-8B-Instruct** with vLLM.

![](assets/logo.svg)

## 🌟 Features

- **Conversational Q&A**: Ask questions about technical drawings in natural language
- **Instant Upload**: Upload once, ask multiple questions without re-uploading
- **View Detection**: Automatically detect and highlight different views (front, side, top, sections)
- **Background Processing**: View detection runs in background - start chatting immediately
- **Bounding Box Visualization**: See detected elements highlighted on the drawing
- **Fast Inference**: Optimized with flash-attention and vLLM
- **German & English**: Supports both languages

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (for frontend)
- CUDA 12.0+ with 48GB+ VRAM (for GPU acceleration)
- Conda or venv

### 1. Setup Backend

```bash
# Create and activate environment
conda create -n deepseek-ocr python=3.12
conda activate deepseek-ocr

# Install dependencies
cd backend
pip install -r requirements_qwen.txt

# (Optional) Install flash-attention for 20-30% speedup
./fix_flash_attn.sh

# Start backend
./start_backend.sh
```

Backend will be available at `http://localhost:8000`

### 2. Setup Frontend

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## 📖 Usage

### Upload & Chat Workflow

1. **Upload drawing** - Drag & drop or click to upload (image or PDF)
2. **Wait < 1 second** - Upload completes instantly
3. **Start asking questions** - Chat immediately, no waiting!
4. **Bounding boxes appear** - View detection completes in background (5-10s)

### Example Questions

**German:**
- "Was ist der Außendurchmesser?"
- "Liste alle Maße mit Toleranzen auf"
- "Was steht in der Stückliste?"
- "Zeige mir alle Ansichten (Views) in dieser Zeichnung"

**English:**
- "What is the outer diameter?"
- "List all dimensions with tolerances"
- "What's in the bill of materials?"
- "Show me all views in this drawing"

### Quick Access Questions

The interface provides predefined questions for common queries:
- Dimensions and tolerances
- Part numbers
- Material specifications
- BOM (Bill of Materials)
- Scale
- View detection

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │  React + Vite + TailwindCSS
│  Port 5173  │
└──────┬──────┘
       │ HTTP
┌──────▼──────┐
│   Backend   │  FastAPI + vLLM
│  Port 8000  │
└──────┬──────┘
       │
┌──────▼──────────────────┐
│ Qwen3-VL-8B-Instruct   │  Vision-Language Model
│ with flash-attention    │  Direct, concise answers
└─────────────────────────┘
```

## 🔧 Configuration

### Model Selection

Default: `Qwen/Qwen3-VL-8B-Instruct` (non-reasoning, direct answers)

To change model, edit `backend/qwen_vision_service.py`:
```python
def __init__(self, model_path: str = "Qwen/Qwen3-VL-8B-Instruct"):
```

Alternative models:
- `Qwen/Qwen3-VL-8B-Thinking` - Shows reasoning (verbose)
- `Qwen/Qwen3-VL-4B-Instruct` - Smaller, faster
- `Qwen/Qwen3-VL-30B-A3B-Instruct` - Larger, more capable (needs more VRAM)

### Performance Tuning

**Temperature & Response Length:**
```python
# In qwen_vision_service.py, adjust:
temperature=0.0  # 0.0 = most concise, 0.7 = more creative
max_tokens=512   # Lower = shorter answers
```

**GPU Memory:**
```python
# In qwen_vision_service.py:
gpu_memory_utilization=0.90  # Use 90% of GPU memory
```

**Flash-Attention:**
```bash
# Install for 20-30% speedup:
cd backend
./fix_flash_attn.sh
```

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── qwen_vision_service.py     # Vision model service
│   ├── models.py                  # Data models
│   ├── start_backend.sh           # Startup script
│   ├── fix_flash_attn.sh          # Flash-attn installer
│   ├── requirements_qwen.txt      # Python dependencies
│   ├── README.md                  # Backend docs
│   ├── SETUP_QWEN.md              # Setup guide
│   └── FLASH_ATTN_FIX.md          # Flash-attn troubleshooting
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Main app component
│   │   ├── components/
│   │   │   ├── ConversationalMode.jsx
│   │   │   ├── BoundingBoxOverlay.jsx
│   │   │   ├── ImageUpload.jsx
│   │   │   └── ...
│   │   └── main.jsx
│   ├── package.json               # NPM dependencies
│   └── README.md                  # Frontend docs
│
├── VIEW_DETECTION.md              # View detection feature docs
├── requirements.txt               # Root dependencies
├── README.md                      # This file
└── LICENSE
```

## 🎯 Key Features Deep Dive

### 1. View Detection

Automatically detects and highlights different views in technical drawings:
- Front, side, top views
- Section views (A-A, B-B, etc.)
- Detail views
- Isometric/3D views

See [VIEW_DETECTION.md](VIEW_DETECTION.md) for details.

### 2. Background Processing

Upload → Chat immediately → Bounding boxes appear automatically

No more waiting for processing before you can ask questions!

### 3. Grounding Support

The system can return bounding box coordinates for detected elements in JSON format:
```json
[
  {"bbox_2d": [x1, y1, x2, y2], "label": "front view"},
  {"bbox_2d": [x1, y1, x2, y2], "label": "Ø76"}
]
```

Grounding is automatically enabled for questions containing keywords like:
- ansicht, view, zeige, show, wo ist, finde

### 4. Session Management

- Upload once, ask multiple questions
- 24-hour session expiry
- Automatic cleanup of expired sessions
- Sessions stored in `/tmp/deepseek_ocr_sessions/`

## 🔍 API Endpoints

### POST `/api/upload`
Upload an image for analysis.

**Request:**
- `file`: Image or PDF file

**Response:**
```json
{
  "session_id": "abc-123-def-456",
  "filename": "drawing.pdf",
  "status": "ready",
  "message": "Bild erfolgreich hochgeladen",
  "detection_status": "processing"
}
```

### POST `/api/chat`
Ask a question about an uploaded image.

**Request:**
- `session_id`: Session ID from upload
- `question`: Question text
- `use_grounding`: Enable bounding boxes (default: true)

**Response:**
```json
{
  "text": "90 mm",
  "markdown": "90 mm",
  "detected_elements": [...],
  "image_width": 1920,
  "image_height": 1080,
  "processing_time": 2.34
}
```

### GET `/api/detection-status/{session_id}`
Check background view detection status.

**Response:**
```json
{
  "detection_status": "completed",
  "detected_elements": [...],
  "elements_count": 4
}
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if environment is activated
conda activate deepseek-ocr

# Check if port 8000 is available
lsof -ti:8000

# Check logs
tail -f backend/logs/*.log
```

### Flash-attention errors
```bash
# The system will auto-fallback to eager mode (works but slower)
# To fix properly:
cd backend
./fix_flash_attn.sh

# If it still fails, see backend/FLASH_ATTN_FIX.md
```

### Model download slow
First startup downloads ~16GB model. This is normal and only happens once.
```bash
# Check download progress
watch -n 1 'du -sh ~/.cache/huggingface/'
```

### Out of memory
```bash
# Reduce GPU memory usage in qwen_vision_service.py:
gpu_memory_utilization=0.80  # Reduce from 0.90

# Or use smaller model:
model_path="Qwen/Qwen3-VL-4B-Instruct"
```

## 📊 Performance

| Metric | Value |
|--------|-------|
| Model Size | ~16GB |
| VRAM Usage | ~20GB (with 8B model) |
| Upload Time | < 1 second |
| First Response | 1-3 seconds |
| View Detection | 5-10 seconds (background) |
| Tokens/Query | ~50-200 tokens |

With flash-attention:
- 20-30% faster inference
- Lower memory usage
- Better throughput

## 🤝 Contributing

This is a private project. For issues or suggestions, contact the maintainers.

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Qwen Team** - For the excellent Qwen3-VL models
- **vLLM Team** - For the fast inference engine
- **DeepSeek AI** - Original DeepSeek-OCR research (paper reference)

## 📚 Additional Documentation

- [Backend Setup Guide](backend/SETUP_QWEN.md)
- [Backend API Documentation](backend/README.md)
- [View Detection Feature](VIEW_DETECTION.md)
- [Flash-Attention Fix](backend/FLASH_ATTN_FIX.md)
- [Frontend Documentation](frontend/README.md)

---

**Note:** This system has been migrated from DeepSeek-OCR to Qwen3-VL for better conversational capabilities and reasoning. The original DeepSeek-OCR code has been archived.
