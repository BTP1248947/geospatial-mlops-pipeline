#!/usr/bin/env python3
"""
generate_visuals.py - Convert GeoTIFFs to PNGs for the UI.

This script reads the raw Before/After TIFs and the Prediction TIF,
normalizes them for display, and saves them as PNGs in outputs/site/visuals.
"""
import os
import argparse
import numpy as np
import rasterio
from PIL import Image
import matplotlib.pyplot as plt

def normalize(arr):
    """Normalize array to 0-255 uint8"""
    # Clip to 2nd and 98th percentiles to remove outliers
    p2, p98 = np.percentile(arr, (2, 98))
    arr = np.clip(arr, p2, p98)
    # Scale to 0-255
    arr = (arr - p2) / (p98 - p2) * 255
    return arr.astype(np.uint8)

def save_rgb(tif_path, out_path):
    """Read RGB bands from Sentinel-2 TIF and save as PNG"""
    print(f"Converting {os.path.basename(tif_path)} -> {os.path.basename(out_path)}")
    with rasterio.open(tif_path) as src:
        # Assuming bands are B2, B3, B4, B8, B11, B12
        # RGB is B4, B3, B2 -> Indices 3, 2, 1 (1-based)
        # Wait, previous script saved B2,B3,B4,B8,B11,B12
        # So RGB is indices 3, 2, 1
        r = src.read(3)
        g = src.read(2)
        b = src.read(1)
        
        rgb = np.dstack((normalize(r), normalize(g), normalize(b)))
        img = Image.fromarray(rgb)
        img.save(out_path)

def save_mask(tif_path, out_path):
    """Read single band mask and save as PNG"""
    print(f"Converting {os.path.basename(tif_path)} -> {os.path.basename(out_path)}")
    with rasterio.open(tif_path) as src:
        mask = src.read(1)
        
        # Normalize if needed (prediction might be 0-1 probability or 0-255)
        if mask.max() <= 1.0:
            mask = mask * 255
        
        mask = mask.astype(np.uint8)
        img = Image.fromarray(mask, mode='L') # Grayscale
        img.save(out_path)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--before", required=True)
    p.add_argument("--after", required=True)
    p.add_argument("--pred", required=True)
    p.add_argument("--name", required=True, help="AOI name, e.g. amazon_rainforest")
    p.add_argument("--year-before", required=True, help="Year of before image")
    p.add_argument("--year-after", required=True, help="Year of after image")
    p.add_argument("--out-dir", default="outputs/site/visuals")
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # Output filenames expected by populate_ui.py:
    # {name}_before_{year}.png
    # {name}_after_{year}.png
    # {name}_mask_{year_before}_{year_after}.png

    save_rgb(args.before, os.path.join(args.out_dir, f"{args.name}_before_{args.year_before}.png"))
    save_rgb(args.after,  os.path.join(args.out_dir, f"{args.name}_after_{args.year_after}.png"))
    save_mask(args.pred,  os.path.join(args.out_dir, f"{args.name}_mask_{args.year_before}.png")) # Mask usually associated with the 'before' year in UI logic or just one of them

    print("[DONE] Visuals generated.")

if __name__ == "__main__":
    main()
