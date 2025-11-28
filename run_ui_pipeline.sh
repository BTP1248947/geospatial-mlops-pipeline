
#!/bin/bash
set -e

# run_ui_pipeline.sh
# Runs inference on available data and starts the React UI

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Geospatial MLOps Pipeline -> UI ===${NC}"

# 1. Check for Model
# The training script saves to runs/model_inference.pth (or best_model.pth if using callbacks)
# We'll look for model_inference.pth first as we saw it in logs
MODEL_PATH="runs/model_inference.pth"
if [ ! -f "$MODEL_PATH" ]; then
    # Try finding any .pth in runs
    MODEL_PATH=$(find runs -name "*.pth" | head -n 1)
fi

if [ -z "$MODEL_PATH" ] || [ ! -f "$MODEL_PATH" ]; then
    echo -e "${RED}Error: No model found in runs/.${NC}"
    echo "Please run training first (Option 2 in run_demo.sh) or ensure a model exists."
    exit 1
fi
echo -e "${YELLOW}Using model: $MODEL_PATH${NC}"

# 2. Run Inference & Stitching
# We'll run full_pipeline.py but point it to the model
# This generates outputs/site/visuals/*
echo -e "${YELLOW}Running Inference & Generating Visuals...${NC}"
PYTHONPATH=. python3 tools/full_pipeline.py \
    --model "$MODEL_PATH" \
    --pairs-dir data/raw \
    --site-out outputs/site \
    --threshold 0.5

# 3. Populate UI Assets
echo -e "${YELLOW}Populating React UI Assets...${NC}"
python3 tools/populate_ui.py \
    --visuals-dir outputs/site/visuals \
    --ui-public-dir ui/public/visualization_results

# 4. Start React App
echo -e "${GREEN}Starting React App...${NC}"
echo "Navigate to http://localhost:5173 (or port shown)"
cd ui
npm install
npm run dev
