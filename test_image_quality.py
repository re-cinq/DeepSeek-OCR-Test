#!/usr/bin/env python3
"""
Test script to check image properties that might affect OCR performance
"""
from PIL import Image
import sys

def analyze_image(image_path):
    """Analyze image properties"""
    try:
        img = Image.open(image_path)

        print(f"Image: {image_path}")
        print(f"  Mode: {img.mode}")
        print(f"  Size: {img.size} (W x H)")
        print(f"  Format: {img.format}")
        print(f"  DPI: {img.info.get('dpi', 'Not set')}")

        # Convert to RGB for analysis
        if img.mode != 'RGB':
            print(f"  Converting from {img.mode} to RGB...")
            img = img.convert('RGB')

        # Get pixel data statistics
        import numpy as np
        pixels = np.array(img)

        print(f"  Mean brightness: {pixels.mean():.1f}")
        print(f"  Std deviation: {pixels.std():.1f}")
        print(f"  Min/Max: {pixels.min()}/{pixels.max()}")

        # Check if image is mostly white/blank
        if pixels.mean() > 240:
            print("  ⚠️  WARNING: Image appears very bright/washed out")
        elif pixels.mean() < 15:
            print("  ⚠️  WARNING: Image appears very dark")

        # Check contrast
        if pixels.std() < 30:
            print("  ⚠️  WARNING: Low contrast detected")

        print()

    except Exception as e:
        print(f"Error analyzing {image_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_image_quality.py <image_path>")
        sys.exit(1)

    for path in sys.argv[1:]:
        analyze_image(path)
