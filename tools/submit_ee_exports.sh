#!/usr/bin/env bash
set -euo pipefail

# ----------------------------
# submit_ee_exports.sh
# ----------------------------
# Usage:
#   ./tools/submit_ee_exports.sh AOI_FILE DRIVE_FOLDER PROJECT CLOUDPCT SCALE CRS
#
# Example:
#   ./tools/submit_ee_exports.sh aoi/india_wayanad_forest.geojson EO_Exports my-gcp-proj 60 10 EPSG:4326
#
# This script:
#   - Loads AOI GeoJSON
#   - Generates 4 date pairs
#   - Submits BEFORE and AFTER composites to Earth Engine
#   - Stores logs in logs/ee_exports/*.log
# ----------------------------

if [[ $# -lt 6 ]]; then
  echo "Usage: $0 AOI_FILE DRIVE_FOLDER PROJECT CLOUDPCT SCALE CRS"
  exit 1
fi

AOI_FILE="$1"
DRIVE_FOLDER="$2"
PROJECT="$3"
CLOUDPCT="$4"
SCALE="$5"
CRS="$6"

if [[ ! -f "$AOI_FILE" ]]; then
  echo "[ERROR] AOI file not found: $AOI_FILE"
  exit 1
fi

mkdir -p logs/ee_exports

echo "[INFO] Using AOI: $AOI_FILE"

PAIR_DATES=(
  "2021-01-01,2021-01-31,2022-01-01,2022-01-31"
  "2022-05-01,2022-05-31,2023-05-01,2023-05-31"
  "2023-09-01,2023-09-30,2024-09-01,2024-09-30"
  "2024-12-01,2024-12-31,2025-01-01,2025-01-31"
)

BASENAME=$(basename "$AOI_FILE" .geojson)

i=1
for RANGE in "${PAIR_DATES[@]}"; do
  BEFORE_START=$(echo "$RANGE" | cut -d',' -f1)
  BEFORE_END=$(echo "$RANGE" | cut -d',' -f2)
  AFTER_START=$(echo "$RANGE" | cut -d',' -f3)
  AFTER_END=$(echo "$RANGE" | cut -d',' -f4)

  LOGFILE="logs/ee_exports/${BASENAME}_pair${i}.log"

  echo "[SUBMIT] ${BASENAME}_pair${i}: ${BEFORE_START}..${BEFORE_END} -> ${AFTER_START}..${AFTER_END}"
  {
    python ingest/gee_ingest.py \
      --aoi "$AOI_FILE" \
      --drive-folder "$DRIVE_FOLDER" \
      --project "$PROJECT" \
      --cloud "$CLOUDPCT" \
      --scale "$SCALE" \
      --crs "$CRS" \
      --before-start "$BEFORE_START" \
      --before-end "$BEFORE_END" \
      --after-start "$AFTER_START" \
      --after-end "$AFTER_END"
  } &> "$LOGFILE" || {
    echo "[WARN] submit failed for ${BASENAME}_pair${i} (see $LOGFILE)"
  }

  i=$((i+1))
done

echo "[DONE] Submitted all EE export tasks."