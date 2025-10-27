#!/usr/bin/env python3
"""
Quick environment check for DeepSeek-OCR backend
"""
import sys

def check_imports():
    """Check all required imports"""
    required = [
        ('torch', 'PyTorch - from main requirements.txt'),
        ('vllm', 'vLLM - from main requirements.txt'),
        ('transformers', 'Transformers - from main requirements.txt'),
        ('fastapi', 'FastAPI - from backend/requirements.txt'),
        ('uvicorn', 'Uvicorn - from backend/requirements.txt'),
        ('pydantic', 'Pydantic - from backend/requirements.txt'),
        ('PIL', 'Pillow - from backend/requirements.txt'),
    ]

    missing = []

    print("Checking Python environment...")
    print(f"Python: {sys.version}")
    print(f"Executable: {sys.executable}")
    print()

    print("Checking dependencies:")
    for module, name in required:
        try:
            mod = __import__(module)
            # Get version if available
            version = getattr(mod, '__version__', 'installed')
            print(f"✓ {name:50s} {version}")
        except ImportError:
            print(f"✗ {name:50s} MISSING")
            missing.append((module, name))

    print()

    if missing:
        print("❌ Missing dependencies:")
        print()
        main_deps = []
        backend_deps = []

        for module, name in missing:
            if 'main requirements' in name:
                main_deps.append(module)
            else:
                backend_deps.append(module)

        if main_deps:
            print("Install from main requirements.txt:")
            print("  pip install -r requirements.txt")
            print()

        if backend_deps:
            print("Install from backend requirements.txt:")
            print("  pip install -r backend/requirements.txt")
            print()

        return False
    else:
        print("✓ All dependencies installed!")
        print()
        print("You can now start the backend:")
        print("  ./start_backend.sh")
        return True

if __name__ == "__main__":
    success = check_imports()
    sys.exit(0 if success else 1)
