#!/bin/bash
set -e

echo "=== Starting Brazil Pipeline ==="

# 1. Clean and Chip Data
echo "[1/5] Chipping Brazil Data..."
rm -rf data/chips/*
python3 scripts/chip.py --in-dir data/raw --out-dir data/chips --size 256 --stride 256

# 2. Train on Kaggle
echo "[2/5] Training on Kaggle..."
# Assuming username is set or passed. Hardcoding based on previous context or asking user.
# Using the username from previous context: shreyaanbanerjee
python3 tools/kaggle_runner.py --username shreyaanbanerjee

# 3. Run Inference (Full Pipeline)
echo "[3/5] Running Inference..."
MODEL_PATH=$(find runs/kaggle_result -name "model_inference.pth" | head -n 1)
if [ -z "$MODEL_PATH" ]; then
    echo "[ERR] Model not found in runs/kaggle_result!"
    exit 1
fi

PYTHONPATH=. python3 tools/full_pipeline.py \
    --model "$MODEL_PATH" \
    --pairs-dir data/raw \
    --out-dir outputs/site/visuals \
    --site-out outputs/site \
    --threshold 0.5

# 4. Populate UI
echo "[4/5] Populating UI..."
python3 tools/populate_ui.py \
    --visuals-dir outputs/site/visuals \
    --ui-public-dir ui/public/visualization_results

# 5. Start UI
echo "[5/5] Starting UI..."
cd ui
npm install
npm run dev
