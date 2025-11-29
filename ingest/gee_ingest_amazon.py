#!/usr/bin/env python3
"""
gee_ingest_amazon.py - Ingest Amazon Rainforest data for Year-over-Year comparison.
"""
import json
import ee
import sys
import os
import requests
import zipfile

# Amazon Rainforest (Smaller AOI to ensure download works)
AMAZON_AOI = {
  "type": "Feature",
  "properties": {},
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [-61.3, -9.3],
        [-61.3, -9.2],
        [-61.2, -9.2],
        [-61.2, -9.3],
        [-61.3, -9.3]
      ]
    ]
  }
}

PROJECT = 'radiant-works-474616-t3'
SERVICE_ACCOUNT = 'projectanamoly@radiant-works-474616-t3.iam.gserviceaccount.com'
KEY_FILE = 'key.json'

# Year-over-Year Comparison
BEFORE_DATES = ('2023-01-01', '2023-12-31')
AFTER_DATES = ('2024-01-01', '2024-12-31')

NAME = 'amazon_rainforest'
CLOUD_PCT = 30
SCALE = 20
OUTPUT_DIR = 'data/raw'

def init_ee():
    try:
        if os.path.exists(KEY_FILE):
            creds = ee.ServiceAccountCredentials(SERVICE_ACCOUNT, KEY_FILE)
            ee.Initialize(credentials=creds, project=PROJECT)
            print("[INFO] Earth Engine initialized successfully.")
        else:
            print(f"[ERR] Key file not found: {KEY_FILE}")
            sys.exit(1)
    except Exception as e:
        print(f"[ERR] Failed to initialize Earth Engine: {e}")
        sys.exit(1)

def sentinel_composite(geom, start, end, cloud_pct):
    col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geom)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct))
        .map(lambda i: i.clip(geom))
    )
    
    # Check if we have images
    count = col.size().getInfo()
    print(f"[INFO] Found {count} images for {start} to {end}")
    
    if count == 0:
        print("[WARN] No images found! Trying with higher cloud percentage...")
        col = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geom)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 80))
            .map(lambda i: i.clip(geom))
        )
    
    # Median composite
    img = col.median().select(["B4","B3","B2"]) # RGB only for visualization/training
    # We need 6 bands for the model? The previous script used B2,B3,B4,B8,B11,B12
    # Let's stick to that to match the model input
    img = col.median().select(["B2","B3","B4","B8","B11","B12"])
    
    return img

def download_to_local(img, region, name, folder, scale):
    print(f"[INFO] Preparing download URL for {name}...")
    try:
        url = img.getDownloadURL({
            'scale': scale,
            'crs': 'EPSG:4326',
            'region': region,
            'format': 'GEO_TIFF',
            'name': name
        })
        print(f"[INFO] Downloading from {url}...")
        r = requests.get(url)
        r.raise_for_status()
        
        zip_path = os.path.join(folder, f"{name}.zip")
        with open(zip_path, 'wb') as f:
            f.write(r.content)
            
        print(f"[INFO] Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(folder)
        
        os.remove(zip_path)
        print(f"[INFO] Saved to {folder}")
        
    except Exception as e:
        print(f"[ERR] Failed to download {name}: {e}")

def main():
    init_ee()
    
    # Use the hardcoded geometry
    geom = ee.Geometry(AMAZON_AOI['geometry'])
    
    # Also save the AOI as geojson for other scripts
    os.makedirs('aoi', exist_ok=True)
    with open('aoi/amazon_rainforest.geojson', 'w') as f:
        json.dump(AMAZON_AOI, f)
    
    before_start, before_end = BEFORE_DATES
    after_start, after_end = AFTER_DATES

    print(f"[INFO] Processing {NAME}...")
    print(f"       Before: {before_start} - {before_end}")
    print(f"       After:  {after_start} - {after_end}")

    before_img = sentinel_composite(geom, before_start, before_end, CLOUD_PCT)
    after_img = sentinel_composite(geom, after_start, after_end, CLOUD_PCT)
    
    # Also create a "Ground Truth" mask based on simple difference (NDVI)
    # This is just to have a mask file for the chipping script to work
    # Real ground truth would come from Hansen Global Forest Change or similar
    # But for this demo, we'll generate a synthetic mask from the difference
    ndvi_before = before_img.normalizedDifference(['B8', 'B4'])
    ndvi_after = after_img.normalizedDifference(['B8', 'B4'])
    diff = ndvi_before.subtract(ndvi_after)
    # If NDVI dropped significantly (>0.2), assume deforestation
    mask = diff.gt(0.2).rename('mask')

    fname_before = f"{NAME}_before_{before_start}_{before_end}"
    fname_after  = f"{NAME}_after_{after_start}_{after_end}"
    fname_mask   = f"{NAME}_mask"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    download_to_local(before_img, geom, fname_before, OUTPUT_DIR, SCALE)
    download_to_local(after_img,  geom, fname_after,  OUTPUT_DIR, SCALE)
    download_to_local(mask,       geom, fname_mask,   OUTPUT_DIR, SCALE)

    print("[DONE] Amazon ingestion complete.")

if __name__ == "__main__":
    main()
