# Qwen3-VL Setup für re:cinq Technical Drawing Chat

## ⚡ Empfohlenes Model: Qwen3-VL-30B-A3B-Instruct

**Optimal für Production!**
- **30B Parameter** (MoE mit nur 3B aktiven Parametern)
- **Läuft auf 1-2 GPUs** statt 8!
- **~15-20GB VRAM** statt 100GB+
- **Sehr schnell** durch MoE-Architektur
- **Exzellente Qualität** für technische Zeichnungen

## Option 1: AsyncLLMEngine direkt (✅ Aktuell implementiert)

Das Backend nutzt `AsyncLLMEngine` direkt ohne separaten vLLM Server.

### Voraussetzungen:

**⚠️ WICHTIG**: Qwen3-VL-30B ist sehr neu (Januar 2025) und benötigt die neueste `transformers` Version!

#### Schnelle Installation (empfohlen):

```bash
cd backend

# Automatisches Fix-Script
./fix_qwen_dependencies.sh
```

#### Manuelle Installation:

```bash
# 1. vLLM
pip install vllm>=0.11.0

# 2. Fix huggingface-hub version conflict
pip install 'huggingface-hub<1.0' --upgrade

# 3. Upgrade transformers
pip install --upgrade transformers

# 4. Falls transformers qwen3_vl_moe noch nicht kennt:
#    (Das passiert, wenn das Model zu neu ist)
pip install git+https://github.com/huggingface/transformers.git

# 5. Qwen VL Utils
pip install qwen-vl-utils==0.0.14
```

#### Oder alle Requirements auf einmal:

```bash
pip install -r requirements_qwen.txt
```

### Model Download:

Das Model wird automatisch beim ersten Start heruntergeladen:
- Model: `Qwen/Qwen3-VL-30B-A3B-Instruct` ✅ **AKTUELL**
- Größe: ~30B Parameter (MoE mit 3B aktiven Parametern)
- Download: ~20GB
- VRAM: ~15-20GB (1 GPU)

Für mehr Performance nutze 2 GPUs mit tensor_parallel_size=2

### Backend starten:

```bash
cd backend
python main.py
```

Das Backend initialisiert beim Start automatisch den `QwenVisionService` mit `AsyncLLMEngine`.

### GPU-Anforderungen:

Für Qwen3-VL-30B-A3B-Instruct ✅:
- **1x GPU** mit ≥20GB VRAM (A6000, A100, H100, RTX 4090)
- **2x GPUs** für bessere Performance (tensor_parallel_size=2)

Zum Anpassen der GPU-Anzahl, editiere `backend/qwen_vision_service.py`:

```python
engine_args = AsyncEngineArgs(
    model=self.model_path,
    trust_remote_code=True,
    tensor_parallel_size=1,  # ← 1 oder 2 GPUs
    gpu_memory_utilization=0.90,
    ...
)
```

---

## Option 2: vLLM OpenAI API Server (Alternative)

Falls du einen separaten vLLM Server bevorzugst:

### Server starten:

```bash
# Qwen3-VL-30B auf 1 GPU
python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-VL-30B-A3B-Instruct \
    --tensor-parallel-size 1 \
    --max-model-len 8192 \
    --trust-remote-code \
    --gpu-memory-utilization 0.90 \
    --port 8001 \
    --host 0.0.0.0

# Oder mit 2 GPUs für bessere Performance
python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-VL-30B-A3B-Instruct \
    --tensor-parallel-size 2 \
    --max-model-len 8192 \
    --trust-remote-code \
    --gpu-memory-utilization 0.90 \
    --port 8001 \
    --host 0.0.0.0
```

**Dann** das Backend anpassen, um den API Server zu nutzen statt AsyncLLMEngine (requires code changes).

---

## Model-Vergleich:

| Model | Parameters | Active Params | Memory | GPUs | Speed | Quality |
|-------|-----------|---------------|--------|------|-------|---------|
| **Qwen3-VL-30B-A3B** ✅ | 30B (MoE) | 3B | **~15-20GB** | **1-2** | **Sehr schnell** | **Excellent** |
| Qwen3-VL-235B-A22B | 235B (MoE) | 22B | ~100GB | 8 | Medium | Excellent |
| Qwen3-VL-7B | 7B | 7B | ~14GB | 1 | Sehr schnell | Good |
| Qwen3-VL-72B | 72B | 72B | ~144GB | 4+ | Langsam | Great |

### ✅ Empfehlung: Qwen3-VL-30B-A3B-Instruct

**Warum dieses Model?**
- **Optimal für 1-2 GPUs**: Passt auf Standard-Hardware
- **MoE-Architektur**: Nur 3B aktive Parameter = sehr schnell
- **Excellent Quality**: Comparable zu viel größeren Models
- **Production-ready**: Stabil und effizient
- **Kostengünstig**: Weniger GPUs = weniger Kosten

---

## Configuration Anpassen:

In `backend/qwen_vision_service.py`:

```python
def __init__(self, model_path: str = "Qwen/Qwen3-VL-30B-A3B-Instruct"):
    # ✅ Aktuell: 30B Model (optimal!)
    self.model_path = model_path

    # Oder für Testing auf kleinerer Hardware:
    # self.model_path = "Qwen/Qwen3-VL-7B-Instruct"
```

Und GPU-Settings:

```python
engine_args = AsyncEngineArgs(
    model=self.model_path,
    trust_remote_code=True,
    tensor_parallel_size=1,  # ← 1 GPU (oder 2 für mehr Performance)
    gpu_memory_utilization=0.90,
    max_model_len=8192,
    enforce_eager=False,
)
```

---

## Troubleshooting:

### ❌ Fehler: "model type `qwen3_vl_moe` not recognized"

```
ValueError: The checkpoint you are trying to load has model type `qwen3_vl_moe`
but Transformers does not recognize this architecture.
```

**Problem**: Deine `transformers` Version kennt den neuen `qwen3_vl_moe` Typ noch nicht.

**Lösung**:
```bash
# Schnellste Lösung: Fix-Script
cd backend
./fix_qwen_dependencies.sh

# Oder manuell:
pip install git+https://github.com/huggingface/transformers.git
```

Nach der Installation Backend neu starten:
```bash
python main.py
```

### ❌ Fehler: "huggingface-hub>=0.30.0,<1.0 is required"

```
ImportError: huggingface-hub>=0.30.0,<1.0 is required for a normal functioning
of this module, but found huggingface-hub==1.0.0.
```

**Lösung**:
```bash
pip install 'huggingface-hub<1.0' --upgrade
```

### OOM (Out of Memory):
Mit Qwen3-VL-30B sollte das selten passieren, aber falls doch:
1. Reduziere `gpu_memory_utilization` auf 0.85
2. Reduziere `max_model_len` auf 4096
3. Nutze kleineres Model: `Qwen3-VL-7B-Instruct`

### Langsame Inferenz:
1. Nutze 2 GPUs mit `tensor_parallel_size=2`
2. Setze `enforce_eager=False` (nutzt CUDAGraph für Speed)
3. Erhöhe `gpu_memory_utilization` auf 0.95 (mehr Cache)

### Model Download langsam:
```bash
# Vorher downloaden mit huggingface-cli (~20GB)
huggingface-cli download Qwen/Qwen3-VL-30B-A3B-Instruct
```

---

## ✅ Aktuelle Konfiguration:

Das Backend ist für **1 GPU** mit **Qwen3-VL-30B-A3B-Instruct** konfiguriert.

**Hardware-Anforderungen:**
- 1x GPU mit ≥20GB VRAM (A6000, A100, H100, RTX 4090, RTX 6000 Ada)
- Oder 2x GPUs für bessere Performance

**Zum Starten:**
```bash
cd backend
python main.py
```

Das Model wird beim ersten Start automatisch heruntergeladen (~20GB).
