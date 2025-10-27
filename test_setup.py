#!/usr/bin/env python3
"""
Quick test script to verify setup
"""
import sys
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ required")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_imports():
    """Check required Python packages"""
    required = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pydantic', 'Pydantic'),
        ('PIL', 'Pillow'),
        ('torch', 'PyTorch'),
        ('vllm', 'vLLM'),
    ]

    all_good = True
    for module, name in required:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"❌ {name} not found")
            all_good = False

    return all_good

def check_gpu():
    """Check CUDA availability"""
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"  GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
            return True
        else:
            print("⚠️  CUDA not available (CPU mode - will be very slow)")
            return False
    except Exception as e:
        print(f"❌ Error checking GPU: {e}")
        return False

def check_deepseek_files():
    """Check if DeepSeek-OCR files exist"""
    vllm_dir = Path("DeepSeek-OCR-master/DeepSeek-OCR-vllm")
    if not vllm_dir.exists():
        print(f"❌ DeepSeek-OCR vLLM directory not found: {vllm_dir}")
        return False

    required_files = [
        'config.py',
        'process/image_process.py',
        'process/ngram_norepeat.py',
    ]

    all_exist = True
    for file in required_files:
        filepath = vllm_dir / file
        if filepath.exists():
            print(f"✓ {file}")
        else:
            print(f"❌ {file} not found")
            all_exist = False

    return all_exist

def check_backend_files():
    """Check backend files"""
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ backend/ directory not found")
        return False

    required_files = [
        'main.py',
        'ocr_service.py',
        'models.py',
        'requirements.txt',
    ]

    all_exist = True
    for file in required_files:
        filepath = backend_dir / file
        if filepath.exists():
            print(f"✓ backend/{file}")
        else:
            print(f"❌ backend/{file} not found")
            all_exist = False

    return all_exist

def check_frontend_files():
    """Check frontend files"""
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ frontend/ directory not found")
        return False

    required_files = [
        'package.json',
        'src/App.jsx',
        'src/components/ImageUpload.jsx',
        'src/components/ModeSelector.jsx',
        'src/components/BoundingBoxOverlay.jsx',
        'src/components/ResultsDisplay.jsx',
    ]

    all_exist = True
    for file in required_files:
        filepath = frontend_dir / file
        if filepath.exists():
            print(f"✓ frontend/{file}")
        else:
            print(f"❌ frontend/{file} not found")
            all_exist = False

    # Check node_modules
    if (frontend_dir / "node_modules").exists():
        print("✓ frontend/node_modules")
    else:
        print("⚠️  frontend/node_modules not found - run: cd frontend && npm install")
        all_exist = False

    return all_exist

def main():
    print("=" * 60)
    print("DeepSeek-OCR Web App - Setup Verification")
    print("=" * 60)
    print()

    print("1. Python Environment")
    print("-" * 60)
    python_ok = check_python_version()
    print()

    print("2. Python Packages")
    print("-" * 60)
    packages_ok = check_imports()
    print()

    print("3. GPU & CUDA")
    print("-" * 60)
    gpu_ok = check_gpu()
    print()

    print("4. DeepSeek-OCR Files")
    print("-" * 60)
    deepseek_ok = check_deepseek_files()
    print()

    print("5. Backend Files")
    print("-" * 60)
    backend_ok = check_backend_files()
    print()

    print("6. Frontend Files")
    print("-" * 60)
    frontend_ok = check_frontend_files()
    print()

    print("=" * 60)
    print("Summary")
    print("=" * 60)

    all_checks = [
        ("Python", python_ok),
        ("Packages", packages_ok),
        ("GPU", gpu_ok),
        ("DeepSeek Files", deepseek_ok),
        ("Backend", backend_ok),
        ("Frontend", frontend_ok),
    ]

    for name, status in all_checks:
        symbol = "✓" if status else "❌"
        print(f"{symbol} {name}")

    print()

    if all(status for _, status in all_checks):
        print("🎉 All checks passed! Ready to start.")
        print()
        print("Next steps:")
        print("  1. Terminal 1: ./start_backend.sh")
        print("  2. Terminal 2: ./start_frontend.sh")
        print("  3. Browser: http://localhost:5173")
        return 0
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
