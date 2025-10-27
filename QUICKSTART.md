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
2. Choose an analysis mode (start with "Technical Drawing")
3. Drag & drop a technical drawing or click to upload
4. Wait ~3-10 seconds for processing
5. View results with interactive bounding boxes!

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

### For Technical Drawings:
- **Dimension Extraction**: Finds measurements like "50mm", "Ø25", "R10"
- **Part Numbers**: Detects "P/N: ABC-123", item numbers, callouts
- **BOM Tables**: Extracts bills of materials with structure
- **Visual Grounding**: Colored bounding boxes on detected elements
- **5 Analysis Modes**: Technical, Dimensions, Parts, BOM, Plain OCR

### Technical Highlights:
- Uses your **existing vLLM 0.8.5** installation (no reinstall!)
- Model loads **once** and stays in memory
- Processing: **2-10 seconds** per image
- GPU efficient: **~10-20GB** VRAM usage
- Supports: **JPG, PNG, TIFF, PDF**

## 📊 Example API Usage

### cURL
```bash
curl -X POST http://localhost:8000/api/ocr \
  -F "file=@technical_drawing.jpg" \
  -F "mode=technical_drawing" \
  -F "grounding=true"
```

### Python
```python
import requests

with open('drawing.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/ocr',
        files={'file': f},
        data={'mode': 'technical_drawing'}
    )

results = response.json()
print(f"Found {len(results['dimensions'])} dimensions")
print(f"Found {len(results['part_numbers'])} part numbers")
```

### JavaScript
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('mode', 'dimensions_only');

const response = await fetch('http://localhost:8000/api/ocr', {
  method: 'POST',
  body: formData
});

const results = await response.json();
console.log('Dimensions:', results.dimensions);
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

- Read [README_WEBAPP.md](README_WEBAPP.md) for full documentation
- Try different analysis modes on your technical drawings
- Adjust prompts in `backend/ocr_service.py` for custom analysis
- Build production deployment (see README_WEBAPP.md)

## ⚡ Performance Tips

1. **Faster processing**: Set `crop_mode=False` for simple images
2. **Lower memory**: Reduce `base_size` from 1024 to 768
3. **Batch processing**: Use `/api/ocr/batch` for multiple files
4. **PDF handling**: Use `/api/ocr/pdf` for multi-page documents

Enjoy! 🎉
