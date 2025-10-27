# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies

**Backend:**
```bash
pip install -r backend/requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

### Step 2: Start the Servers

**Open Terminal 1 - Backend:**
```bash
./start_backend.sh
```
Wait for: `✓ OCR service initialized successfully`

**Open Terminal 2 - Frontend:**
```bash
./start_frontend.sh
```
Wait for: `Local: http://localhost:5173/`

### Step 3: Use the Application

1. Open your browser to **http://localhost:5173**
2. Drag & drop a technical drawing or click to upload
3. Ask questions in natural language:
   - "What is the outer diameter?"
   - "List all dimensions"
   - "What's in the BOM table?"
4. View answers with interactive bounding boxes!

## 📁 Project Structure

```
DeepSeek-OCR/
├── backend/                          # FastAPI backend
│   ├── main.py                      # API endpoints
│   ├── ocr_service.py               # Wraps existing DeepSeek scripts
│   ├── models.py                    # Request/response models
│   └── requirements.txt             # Python dependencies
│
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── App.jsx                  # Main app component
│   │   ├── components/
│   │   │   ├── ImageUpload.jsx     # Drag & drop upload
│   │   │   ├── ModeSelector.jsx    # Analysis mode picker
│   │   │   ├── BoundingBoxOverlay.jsx  # Visual grounding
│   │   │   └── ResultsDisplay.jsx  # Results with tabs
│   │   └── index.css                # Tailwind styles
│   └── package.json
│
├── DeepSeek-OCR-master/             # Original DeepSeek-OCR
│   └── DeepSeek-OCR-vllm/          # Used by backend
│
├── start_backend.sh                 # Backend launcher
├── start_frontend.sh                # Frontend launcher
└── README_WEBAPP.md                 # Full documentation
```

## 🎯 Features

### Conversational OCR:
- **Natural Language Questions**: Ask anything about your drawings
- **Visual Grounding**: Colored bounding boxes on detected elements
- **Chat History**: Track Q&A across multiple questions
- **Smart Responses**: Context-aware answers specific to your question
- **Quick Questions**: Pre-defined prompts for common queries

### Technical Highlights:
- Uses your **existing vLLM 0.8.5** installation (no reinstall!)
- Model loads **once** and stays in memory
- Processing: **2-10 seconds** per image
- GPU efficient: **~10-20GB** VRAM usage
- Supports: **JPG, PNG, TIFF, PDF**

## 📊 Example API Usage

### Ask Questions via API

**cURL:**
```bash
curl -X POST http://localhost:8000/api/ocr \
  -F "file=@technical_drawing.jpg" \
  -F "mode=custom" \
  -F "custom_prompt=<image>\nWhat is the outer diameter?" \
  -F "grounding=true"
```

**Python:**
```python
import requests

with open('drawing.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/ocr',
        files={'file': f},
        data={
            'mode': 'custom',
            'custom_prompt': '<image>\nWhat is the outer diameter?',
            'grounding': 'true'
        }
    )

results = response.json()
print(f"Answer: {results['text']}")
print(f"Found {len(results['detected_elements'])} elements")
```

**JavaScript:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('mode', 'custom');
formData.append('custom_prompt', '<image>\nList all dimensions with tolerances');

const response = await fetch('http://localhost:8000/api/ocr', {
  method: 'POST',
  body: formData
});

const results = await response.json();
console.log('Answer:', results.text);
```

## 🔧 Troubleshooting

### Backend won't start
```bash
# Check Python environment
which python
pip list | grep vllm  # Should show vllm-0.8.5

# Install missing dependencies
pip install -r backend/requirements.txt
```

### Frontend errors
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### GPU out of memory
Edit `backend/ocr_service.py`:
```python
self.model = LLM(
    ...
    gpu_memory_utilization=0.7,  # Reduce from 0.9
    ...
)
```

### Port already in use
```bash
# Backend (default 8000)
# Edit backend/main.py: uvicorn.run(..., port=8001)

# Frontend (default 5173)
# Edit frontend/vite.config.js: server: { port: 3000 }
```

## 📚 Next Steps

- Read [FEATURES.md](FEATURES.md) for complete feature list
- Experiment with different types of questions
- Try complex queries like "Compare dimensions in section A vs B"
- Build production deployment (see README_WEBAPP.md)

## ⚡ Performance Tips

1. **Faster processing**: Set `crop_mode=False` for simple images
2. **Lower memory**: Reduce `base_size` from 1024 to 768
3. **Batch processing**: Use `/api/ocr/batch` for multiple files
4. **PDF handling**: Use `/api/ocr/pdf` for multi-page documents

Enjoy! 🎉
