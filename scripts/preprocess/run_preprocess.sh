#!/usr/bin/env bash
set -euo pipefail

RAW=${1:-raw_data}             # raw images location
PROCESSED=${2:-processed_data} # where before/after/mask will be saved
CHIPS=${3:-data/chips}         # chips output
VIS_OUT=${4:-visualization_results}

echo "[STEP] create masks from $RAW -> $PROCESSED"
python scripts/preprocess/create_mask.py --input-dir "$RAW" --out-dir "$PROCESSED" --threshold 40

echo "[STEP] chip images into $CHIPS"
python scripts/preprocess/chip.py --in-dir "$PROCESSED" --out-dir "$CHIPS" --size 256

echo "[STEP] build visualization assets -> $VIS_OUT"
python scripts/preprocess/generate_visualization_index.py --processed "$PROCESSED" --out "$VIS_OUT"

echo "[DONE] Preprocessing pipeline complete."