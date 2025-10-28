#!/bin/bash
# Start Backend in screen with proper conda activation

# Initialize conda
if [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
else
    eval "$(conda shell.bash hook)"
fi

# Activate conda environment
conda activate deepseek-ocr

# Check activation
if [ "$CONDA_DEFAULT_ENV" != "deepseek-ocr" ]; then
    echo "❌ Failed to activate deepseek-ocr conda environment"
    echo "Current environment: $CONDA_DEFAULT_ENV"
    exit 1
fi

echo "✓ Conda environment activated: $CONDA_DEFAULT_ENV"
echo "✓ Python path: $(which python)"

# Run the backend startup script
cd "$(dirname "$0")"
./start_backend.sh
