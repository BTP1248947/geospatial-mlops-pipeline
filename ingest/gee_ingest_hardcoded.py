#!/usr/bin/env python3
"""
gee_ingest_hardcoded.py - Hardcoded Earth Engine ingestion script.

Saves data to data/raw locally.
"""
import json
import ee
import sys
import os
import requests
import zipfile
import io

# Hardcoded configuration
PROJECT = 'radiant-works-474616-t3'
SERVICE_ACCOUNT = 'projectanamoly@radiant-works-474616-t3.iam.gserviceaccount.com'
KEY_FILE = 'key.json'
AOI_PATH = 'aoi/india_wayanad_forest.geojson'
BEFORE_DATES = ('2024-01-01', '2024-01-31')
AFTER_DATES = ('2024-11-01', '2024-11-30')
NAME = 'india_wayanad_forest'
CLOUD_PCT = 60
SCALE = 10
CRS = 'EPSG:4326'
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

def load_aoi(path):
    if not os.path.exists(path):
        print(f"[ERR] AOI file not found: {path}")
        sys.exit(1)
    with open(path, "r") as f:
        gj = json.load(f)
    # support FeatureCollection or single Feature
    feat = gj.get("features", [gj])[0]
    geom = ee.Geometry(feat["geometry"])
    return geom

def sentinel_composite(aoi, start, end, cloud_pct):
    col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct))
        .map(lambda i: i.clip(aoi))
    )
    size = col.size().getInfo()
    if size == 0:
        raise RuntimeError(f"No scenes found for {start}..{end} (cloud<{cloud_pct})")
    # median composite and select common bands
    img = col.median().select(["B2","B3","B4","B8","B11","B12"])
    return img

def download_to_local(img, region, name, folder, scale, crs):
    print(f"[INFO] Preparing download URL for {name}...")
    try:
        url = img.getDownloadURL({
            'scale': scale,
            'crs': crs,
            'region': region,
            'format': 'GEO_TIFF',
            'name': name
        })
        print(f"[INFO] Downloading from {url}...")
        r = requests.get(url)
        r.raise_for_status()
        
        # Save zip file
        zip_path = os.path.join(folder, f"{name}.zip")
        with open(zip_path, 'wb') as f:
            f.write(r.content)
        print(f"[INFO] Saved {zip_path}")
        
        # Extract
        print(f"[INFO] Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(folder)
        
        # Optional: remove zip
        os.remove(zip_path)
        print(f"[INFO] Extracted to {folder}")
        
    except Exception as e:
        print(f"[ERR] Failed to download {name}: {e}")

def main():
    init_ee()
    print("[INFO] Loading AOI:", AOI_PATH)
    aoi = load_aoi(AOI_PATH)
    
    before_start, before_end = BEFORE_DATES
    after_start, after_end = AFTER_DATES

    print("[INFO] Building BEFORE composite:", before_start, before_end)
    before_img = sentinel_composite(aoi, before_start, before_end, CLOUD_PCT)
    print("[INFO] Building AFTER composite:", after_start, after_end)
    after_img = sentinel_composite(aoi, after_start, after_end, CLOUD_PCT)

    fname_before = f"{NAME}_before_{before_start}_{before_end}"
    fname_after  = f"{NAME}_after_{after_start}_{after_end}"

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    download_to_local(before_img, aoi, fname_before, OUTPUT_DIR, SCALE, CRS)
    download_to_local(after_img,  aoi, fname_after,  OUTPUT_DIR, SCALE, CRS)

    print("[DONE] Processing complete.")

if __name__ == "__main__":
    main()
