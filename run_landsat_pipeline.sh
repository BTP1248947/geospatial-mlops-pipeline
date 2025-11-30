#!/bin/bash
set -e

echo "=== Starting Landsat 9 Pipeline ==="

# 1. Fetch Data
echo "[1/6] Fetching Landsat 9 Data..."
python3 tools/fetch_landsat.py --out-dir data/raw_landsat

# 2. Preprocess (Chip & Mask)
echo "[2/6] Preprocessing & Chipping..."
# We output to data/chips so kaggle_runner picks it up
python3 tools/preprocess_landsat.py --in-dir data/raw_landsat --out-dir data/chips

# 3. Train on Kaggle
# 3. Inference (Simple Difference)
echo "[3/4] Running Inference (Simple Difference)..."
# We don't need a model path anymore
python3 tools/infer_simple.py \
    --in-dir data/raw_landsat \
    --out-dir outputs/site/visuals \
    --threshold 30

# 4. Populate UI
echo "[4/4] Populating UI..."
# We point raw-dir to data/raw_landsat so it finds the PNGs
python3 tools/populate_ui.py --visuals-dir outputs/site/visuals --raw-dir data/raw_landsat --ui-public-dir ui/public/visualization_results

echo "[4/4] Done! Check UI."
