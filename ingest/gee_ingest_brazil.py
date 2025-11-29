#!/usr/bin/env python3
"""
gee_ingest_brazil.py - Ingest Brazil Novo Progresso data for Year-over-Year comparison.
"""
import json
import ee
import sys
import os
import requests
import zipfile

# Brazil Novo Progresso (Deforestation Hotspot)
# Approx bounding box
BRAZIL_AOI = {
  "type": "Feature",
  "properties": {},
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [-55.55, -7.55],
        [-55.55, -7.45],
        [-55.45, -7.45],
        [-55.45, -7.55],
        [-55.55, -7.55]
      ]
    ]
  }
}

PROJECT = 'radiant-works-474616-t3'
SERVICE_ACCOUNT = 'projectanamoly@radiant-works-474616-t3.iam.gserviceaccount.com'
KEY_FILE = 'key.json'

# Year-over-Year Comparison
BEFORE_DATES = ('2023-06-01', '2023-09-30') # Dry season for better visibility
AFTER_DATES = ('2024-06-01', '2024-09-30')

NAME = 'brazil_novo_progresso'
CLOUD_PCT = 20
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
    
    # Median composite with 6 bands
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
        
        # Check if it's a zip or direct tif (sometimes EE returns zip for large files)
        # But we'll assume it might be a zip if large, or just write content
        # Actually, let's just write to a temp file and check signature like before
        # Or simpler: just write as .tif directly if we know it's a tif, 
        # but EE usually sends a ZIP if it's > 32MB. 
        # Given our small AOI, it might be a single TIF inside a ZIP or just TIF.
        # Let's save as zip first to be safe.
        
        zip_path = os.path.join(folder, f"{name}.zip")
        with open(zip_path, 'wb') as f:
            f.write(r.content)
            
        # Check signature
        with open(zip_path, 'rb') as f:
            sig = f.read(4)
        
        if sig == b'MM\x00*' or sig == b'II*\x00':
            # It's a TIF, rename
            tif_path = os.path.join(folder, f"{name}.tif")
            os.rename(zip_path, tif_path)
            print(f"[INFO] Saved TIF to {tif_path}")
        else:
            # Try unzip
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(folder)
                os.remove(zip_path)
                print(f"[INFO] Extracted ZIP to {folder}")
            except zipfile.BadZipFile:
                print(f"[ERR] Downloaded file is neither TIF nor valid ZIP. Content start: {sig}")

    except Exception as e:
        print(f"[ERR] Failed to download {name}: {e}")

def main():
    init_ee()
    geom = ee.Geometry(BRAZIL_AOI['geometry'])
    
    before_start, before_end = BEFORE_DATES
    after_start, after_end = AFTER_DATES

    print(f"[INFO] Processing {NAME}...")
    
    before_img = sentinel_composite(geom, before_start, before_end, CLOUD_PCT)
    after_img = sentinel_composite(geom, after_start, after_end, CLOUD_PCT)
    
    # Synthetic Mask (NDVI Difference)
    ndvi_before = before_img.normalizedDifference(['B8', 'B4'])
    ndvi_after = after_img.normalizedDifference(['B8', 'B4'])
    diff = ndvi_before.subtract(ndvi_after)
    mask = diff.gt(0.2).rename('mask')

    fname_before = f"{NAME}_before_{before_start}_{before_end}"
    fname_after  = f"{NAME}_after_{after_start}_{after_end}"
    fname_mask   = f"{NAME}_mask"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    download_to_local(before_img, geom, fname_before, OUTPUT_DIR, SCALE)
    download_to_local(after_img,  geom, fname_after,  OUTPUT_DIR, SCALE)
    download_to_local(mask,       geom, fname_mask,   OUTPUT_DIR, SCALE)

    print("[DONE] Brazil ingestion complete.")

if __name__ == "__main__":
    main()
