# Qwen3-VL Setup für re:cinq Technical Drawing Chat

## Option 1: AsyncLLMEngine direkt (Aktuell implementiert)

Das Backend nutzt `AsyncLLMEngine` direkt ohne separaten vLLM Server.

### Voraussetzungen:

```bash
# vLLM >= 0.11.0 installieren
pip install vllm>=0.11.0

# Qwen VL Utils (optional aber empfohlen)
pip install qwen-vl-utils==0.0.14
```

### Model Download:

Das Model wird automatisch beim ersten Start heruntergeladen:
- Model: `Qwen/Qwen3-VL-235B-A22B-Instruct`
- Größe: ~235B Parameter (MoE mit 22B aktiven Parametern)
- Speicher: ~100GB+ (je nach Quantisierung)

Alternativ FP8-quantisierte Version (schneller, weniger Speicher):
- Model: `Qwen/Qwen3-VL-235B-A22B-Instruct-FP8`
- Speicher: ~50-60GB

### Backend starten:

```bash
cd backend
python main.py
```

Das Backend initialisiert beim Start automatisch den `QwenVisionService` mit `AsyncLLMEngine`.

### GPU-Anforderungen:

Für Qwen3-VL-235B-A22B:
- **8x A100/H100** (tensor_parallel_size=8 in qwen_vision_service.py)
- Oder weniger GPUs mit FP8-Quantisierung

Zum Anpassen der GPU-Anzahl, editiere `backend/qwen_vision_service.py`:

```python
engine_args = AsyncEngineArgs(
    model=self.model_path,
    trust_remote_code=True,
    tensor_parallel_size=4,  # ← Hier anpassen
    gpu_memory_utilization=0.90,
    ...
)
```

---

## Option 2: vLLM OpenAI API Server (Alternative)

Falls du einen separaten vLLM Server bevorzugst:

### Server starten:

```bash
# Standard Version
python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-VL-235B-A22B-Instruct \
    --tensor-parallel-size 8 \
    --max-model-len 8192 \
    --trust-remote-code \
    --gpu-memory-utilization 0.90 \
    --port 8001 \
    --host 0.0.0.0

# FP8 Version (empfohlen für weniger GPUs)
python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-VL-235B-A22B-Instruct-FP8 \
    --tensor-parallel-size 8 \
    --mm-encoder-tp-mode data \
    --enable-expert-parallel \
    --max-model-len 8192 \
    --trust-remote-code \
    --gpu-memory-utilization 0.90 \
    --port 8001 \
    --host 0.0.0.0
```

**Dann** das Backend anpassen, um den API Server zu nutzen statt AsyncLLMEngine (requires code changes).

---

## Model-Vergleich:

| Model | Parameters | Active Params | Memory | Speed | Quality |
|-------|-----------|---------------|--------|-------|---------|
| Qwen3-VL-235B-A22B | 235B (MoE) | 22B | ~100GB | Medium | Excellent |
| Qwen3-VL-235B-FP8 | 235B (MoE) | 22B | ~50GB | Fast | Excellent |
| Qwen3-VL-72B | 72B | 72B | ~144GB | Slow | Great |
| Qwen3-VL-7B | 7B | 7B | ~14GB | Very Fast | Good |

### Empfehlung:

Für Production mit 8x GPUs: **Qwen3-VL-235B-A22B-Instruct-FP8**
- Beste Balance aus Qualität und Performance
- Passt auf 8x A100 80GB oder 4x H100
- `--enable-expert-parallel` nutzt MoE optimal

---

## Configuration Anpassen:

In `backend/qwen_vision_service.py`:

```python
def __init__(self, model_path: str = "Qwen/Qwen3-VL-235B-A22B-Instruct-FP8"):
    # Wechsel zum FP8 Model
    self.model_path = model_path

    # Oder kleineres Model für Testing:
    # self.model_path = "Qwen/Qwen3-VL-7B-Instruct"
```

Und GPU-Settings:

```python
engine_args = AsyncEngineArgs(
    model=self.model_path,
    trust_remote_code=True,
    tensor_parallel_size=4,  # ← Deine GPU-Anzahl
    gpu_memory_utilization=0.90,
    max_model_len=8192,
    enforce_eager=False,
)
```

---

## Troubleshooting:

### OOM (Out of Memory):
1. Nutze FP8-Model: `Qwen3-VL-235B-A22B-Instruct-FP8`
2. Reduziere `gpu_memory_utilization` auf 0.85
3. Reduziere `max_model_len` auf 4096
4. Nutze kleineres Model: `Qwen3-VL-7B-Instruct`

### Langsame Inferenz:
1. Nutze FP8-Model
2. Erhöhe `tensor_parallel_size`
3. Aktiviere `--enable-expert-parallel` (nur bei MoE Models)
4. Setze `enforce_eager=False` (nutzt CUDAGraph)

### Model Download langsam:
```bash
# Vorher downloaden mit huggingface-cli
huggingface-cli download Qwen/Qwen3-VL-235B-A22B-Instruct-FP8
```

---

## Aktuelle Konfiguration:

Das Backend ist aktuell für **8x GPUs** mit dem **Full Precision Model** konfiguriert.

Zum Testen auf weniger Hardware, editiere `qwen_vision_service.py` und nutze:
- `Qwen3-VL-7B-Instruct` (1 GPU, ~14GB)
- `tensor_parallel_size=1`
