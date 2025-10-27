# Qwen3-VL Backend für Technische Zeichnungen

Backend-Service für konversationelle Analyse technischer Zeichnungen mit Qwen3-VL-30B-A3B-Instruct.

## 🚀 Quick Start

```bash
# 1. Dependencies installieren
./fix_qwen_dependencies.sh

# 2. Backend starten
python main.py
```

Das Backend läuft dann auf `http://localhost:8000`

## 📋 Voraussetzungen

- **Python**: 3.10+
- **GPU**: 1x mit ≥20GB VRAM (A6000, A100, H100, RTX 4090, RTX 6000 Ada)
- **VRAM**: ~15-20GB
- **Storage**: ~25GB für Model-Download

## 🔧 Installation

### Option 1: Automatisch (Empfohlen)

```bash
cd backend
./fix_qwen_dependencies.sh
```

### Option 2: Mit requirements.txt

```bash
pip install -r requirements_qwen.txt

# Falls transformers qwen3_vl_moe noch nicht kennt:
pip install git+https://github.com/huggingface/transformers.git
```

### Option 3: Manuell

```bash
pip install vllm>=0.11.0
pip install 'huggingface-hub<1.0' --upgrade
pip install git+https://github.com/huggingface/transformers.git
pip install qwen-vl-utils==0.0.14
pip install fastapi uvicorn python-multipart pydantic
pip install Pillow PyMuPDF torch torchvision
```

## 📡 API Endpoints

### Health Check
```bash
GET /
GET /health
```

### Upload Image
```bash
POST /api/upload
Content-Type: multipart/form-data
Body: file=<image or PDF>

Response:
{
  "session_id": "uuid",
  "filename": "drawing.pdf",
  "status": "ready",
  "message": "Bild erfolgreich hochgeladen..."
}
```

### Chat with Image
```bash
POST /api/chat
Content-Type: multipart/form-data
Body:
  session_id=<uuid>
  question=<your question>
  use_grounding=false

Response:
{
  "text": "Die Welle hat einen Außendurchmesser von Ø25mm...",
  "markdown": "...",
  "detected_elements": [],
  "image_width": 1920,
  "image_height": 1080,
  "processing_time": 2.45,
  ...
}
```

### Delete Session
```bash
DELETE /api/session/{session_id}
```

## 🎯 Model Details

- **Model**: Qwen/Qwen3-VL-30B-A3B-Instruct
- **Architecture**: MoE (Mixture of Experts)
- **Total Parameters**: 30B
- **Active Parameters**: 3B (während Inferenz)
- **Context Length**: 8192 tokens
- **VRAM Usage**: ~15-20GB

## 🔍 Workflow

1. **Upload Phase**: Bild wird hochgeladen → Server speichert es mit Session-ID
2. **Chat Phase**: Mehrere Fragen können zum gleichen Bild gestellt werden
3. **Session Management**: Sessions verfallen nach 24h automatisch

## ⚙️ Konfiguration

In `qwen_vision_service.py`:

```python
# Model ändern
def __init__(self, model_path: str = "Qwen/Qwen3-VL-30B-A3B-Instruct"):
    # Für Testing:
    # self.model_path = "Qwen/Qwen3-VL-7B-Instruct"

# GPU Settings
engine_args = AsyncEngineArgs(
    tensor_parallel_size=1,  # 1 oder 2 GPUs
    gpu_memory_utilization=0.90,  # 0.85-0.95
    max_model_len=8192,  # Max context
    enforce_eager=False,  # False = CUDAGraph (schneller)
)
```

## 🐛 Troubleshooting

### Error: "qwen3_vl_moe not recognized"

```bash
# Transformers ist zu alt
pip install git+https://github.com/huggingface/transformers.git
```

### Error: "huggingface-hub version conflict"

```bash
pip install 'huggingface-hub<1.0' --upgrade
```

### OOM (Out of Memory)

```python
# In qwen_vision_service.py:
gpu_memory_utilization=0.85  # Reduzieren
max_model_len=4096  # Reduzieren

# Oder kleineres Model:
model_path="Qwen/Qwen3-VL-7B-Instruct"
```

### Langsame Inferenz

```python
# 2 GPUs nutzen:
tensor_parallel_size=2

# CUDAGraph aktivieren:
enforce_eager=False

# Mehr Cache:
gpu_memory_utilization=0.95
```

## 📊 Performance

Typische Antwortzeiten mit 1x A100:
- Einfache Frage: ~1-2s
- Komplexe Analyse: ~3-5s
- Tabellen-Extraktion: ~4-8s

Mit 2x GPUs (tensor_parallel_size=2):
- ~30-40% schneller

## 🔒 Session Management

- Sessions werden in `/tmp/deepseek_ocr_sessions/` gespeichert
- Automatische Bereinigung nach 24h
- Manuelle Bereinigung: `DELETE /api/session/{id}`

## 📝 Logs

Backend-Logs zeigen:
- Model-Initialisierung
- Upload-Events mit Session-IDs
- Chat-Queries mit Processing-Zeit
- Session-Bereinigung

```
INFO:main:Initializing Qwen3-VL Vision service with vLLM...
Initializing Qwen3-VL model: Qwen/Qwen3-VL-30B-A3B-Instruct
Qwen3-VL AsyncLLMEngine initialized successfully!
INFO:main:✓ Vision service initialized successfully
INFO:main:✓ GPU available: True
INFO:main:Uploaded drawing.pdf - Session: abc123...
INFO:main:Chat query for session abc123: Was ist der Außendurchmesser?
INFO:main:✓ Chat response in 2.45s - 0 elements
```

## 🔗 Siehe auch

- [SETUP_QWEN.md](SETUP_QWEN.md) - Detaillierte Setup-Anleitung
- [requirements_qwen.txt](requirements_qwen.txt) - Alle Dependencies
- [fix_qwen_dependencies.sh](fix_qwen_dependencies.sh) - Automatisches Fix-Script
