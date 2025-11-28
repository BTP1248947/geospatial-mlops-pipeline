
#!/bin/bash
set -e

# run_demo.sh
# Master script to run the Geospatial MLOps Pipeline Demo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Geospatial MLOps Pipeline Demo ===${NC}"

# 1. Environment Checks
echo -e "${YELLOW}[1/6] Checking environment...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found.${NC}"
    echo "Please copy .env.template to .env and fill in your details."
    exit 1
fi
source .env

if [ ! -f "key.json" ]; then
    echo -e "${YELLOW}Warning: key.json not found in root.${NC}"
    echo "If you are using Service Account auth for GEE, please place key.json here."
    # Don't exit, user might use user-auth
fi

# 2. Start MLflow (Background)
echo -e "${YELLOW}[2/6] Starting MLflow server...${NC}"
if pgrep -f "mlflow server" > /dev/null; then
    echo "MLflow already running."
else
    mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns --host 0.0.0.0 --port 5001 > logs/mlflow.log 2>&1 &
    echo "MLflow started on http://localhost:5001 (pid $!)"
    sleep 3
fi
export MLFLOW_TRACKING_URI=http://localhost:5001

# 3. Mode Selection
echo -e "${YELLOW}Select Mode:${NC}"
echo "1) PROXY VISUALS ONLY (Fastest - uses existing data or creates proxy heatmaps)"
echo "2) FULL PIPELINE (Ingest -> Train -> Deploy - Requires GEE & GPU/Time)"
echo "3) INGEST ONLY (Submit GEE tasks)"
read -p "Enter choice [1-3]: " choice

if [ "$choice" == "3" ]; then
    echo -e "${YELLOW}Submitting GEE Export Tasks...${NC}"
    # Example: Submit for one of the new AOIs
    python3 ingest/gee_ingest.py \
        --project "${GEE_PROJECT_ID:-radiant-works-474616-t3}" \
        --aoi aoi/brazil_novo_progresso.geojson \
        --before 2023-08-01 2023-08-30 \
        --after 2024-08-01 2024-08-30 \
        --name brazil_novo_progresso \
        --drive-folder "${DRIVE_FOLDER:-EO_Exports}" \
        --service-account "${GEE_SERVICE_ACCOUNT:-}" \
        --key-file "${GEE_SERVICE_ACCOUNT_JSON:-key.json}"
    
    echo -e "${GREEN}Tasks submitted! Check Earth Engine Task Manager.${NC}"
    echo "Once tasks are done, run this script again and choose 'Download' or 'Full Pipeline' (manual download step required currently)."
    exit 0
fi

if [ "$choice" == "2" ]; then
    echo -e "${YELLOW}[3/6] Full Pipeline Selected.${NC}"
    
    # Check for raw data
    count=$(ls data/raw/*.tif 2>/dev/null | wc -l)
    if [ "$count" -eq "0" ]; then
        echo -e "${RED}No raw data found in data/raw/.${NC}"
        echo "Have you downloaded the GEE exports?"
        read -p "Do you want to download from Drive now? (y/n) " dl_choice
        if [ "$dl_choice" == "y" ]; then
             python3 tools/download_from_drive.py \
                --service-account-key key.json \
                --drive-folder "${DRIVE_FOLDER:-EO_Exports}" \
                --out-dir data/raw \
                --pattern "*.tif"
        else
            echo "Please place .tif files in data/raw/ and retry."
            exit 1
        fi
    fi

    echo -e "${YELLOW}[4/6] Preprocessing (Chipping)...${NC}"
    python3 scripts/chip.py --in-dir data/raw --out-dir data/chips --size 256 --stride 256

    echo -e "${YELLOW}[5/6] Training (Demo Mode)...${NC}"
    python3 -m train.train --data-dir data/chips --epochs 2 --batch-size 4 --lr 3e-4 --experiment demo_run

    # Find best model
    LATEST_RUN=$(ls -td runs/*/ | head -1)
    MODEL_PATH="${LATEST_RUN}best_model.pth"
    echo "Using model: $MODEL_PATH"

    echo -e "${YELLOW}[6/6] Inference & Site Generation...${NC}"
    PYTHONPATH=. python3 tools/full_pipeline.py --model "$MODEL_PATH" --pairs-dir data/raw --site-out outputs/site
    
    echo -e "${GREEN}Done! Serving site...${NC}"
    python3 -m http.server --directory outputs/site 8000
    exit 0
fi

if [ "$choice" == "1" ]; then
    echo -e "${YELLOW}[3/6] Proxy Visuals Mode Selected.${NC}"
    
    # Check if we have ANY data
    count=$(ls data/raw/*.tif 2>/dev/null | wc -l)
    if [ "$count" -eq "0" ]; then
        echo -e "${YELLOW}No data in data/raw/. Checking for sample data...${NC}"
        # Optional: Download sample data if available?
        # For now, warn user
        echo -e "${RED}No .tif files found in data/raw/.${NC}"
        echo "Please put at least one before/after pair in data/raw/ to visualize."
        echo "You can use the 'Ingest' option to generate them via GEE."
        exit 1
    fi

    echo -e "${YELLOW}Generating Proxy Visuals (NDVI Difference)...${NC}"
    PYTHONPATH=. python3 tools/full_pipeline_proxy.py \
        --pairs-dir data/raw \
        --out-dir outputs/aois \
        --site-out outputs/site \
        --proxy-only \
        --verbose

    echo -e "${GREEN}Done! Serving site...${NC}"
    echo "Open http://localhost:8000 in your browser."
    python3 -m http.server --directory outputs/site 8000
fi
