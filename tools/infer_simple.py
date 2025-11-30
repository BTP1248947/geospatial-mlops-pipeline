#!/usr/bin/env python3
"""
tools/infer_simple.py

Generates masks based on simple pixel-wise difference between before and after images.
No neural network required.

Usage:
  python tools/infer_simple.py --in-dir data/raw_landsat --out-dir outputs/site/visuals
"""

import os
import glob
import argparse
import numpy as np
from PIL import Image
from tqdm import tqdm
import matplotlib.cm as cm

def compute_ndvi(rgb_path, nir_path):
    """
    Computes NDVI from RGB (Red channel) and NIR image.
    NDVI = (NIR - Red) / (NIR + Red)
    """
    # Load images
    rgb_img = Image.open(rgb_path).convert('RGB')
    nir_img = Image.open(nir_path).convert('L') # Grayscale
    
    # Resize NIR to match RGB if needed
    if rgb_img.size != nir_img.size:
        nir_img = nir_img.resize(rgb_img.size)
        
    rgb_arr = np.array(rgb_img, dtype=np.float32)
    nir_arr = np.array(nir_img, dtype=np.float32)
    
    # Extract Red channel (0)
    # Normalize to reflectance (approximate based on visualization params)
    # RGB was saved with max=0.3, NIR with max=0.5
    red = (rgb_arr[:, :, 0] / 255.0) * 0.3
    nir = (nir_arr / 255.0) * 0.5
    
    # Calculate NDVI
    # Add epsilon to avoid division by zero
    ndvi = (nir - red) / (nir + red + 1e-6)
    
    return ndvi

def compute_difference(before_path, after_path, before_nir_path, after_nir_path, threshold=0.1):
    """
    Computes difference in NDVI.
    Returns heatmap (colored RGB) and binary mask.
    """
    # Check if NIR files exist
    if not os.path.exists(before_nir_path) or not os.path.exists(after_nir_path):
        print(f"Warning: NIR files missing for {os.path.basename(before_path)}. Falling back to RGB difference.")
        return compute_rgb_difference(before_path, after_path)

    ndvi_before = compute_ndvi(before_path, before_nir_path)
    ndvi_after = compute_ndvi(after_path, after_nir_path)
    
    # Calculate dNDVI (Difference in NDVI)
    # Deforestation = Loss of vegetation = Decrease in NDVI
    # So we look for (Before - After) > 0
    d_ndvi = ndvi_before - ndvi_after
    
    # Filter out negative changes (regrowth) if we only care about deforestation
    # Or just take absolute difference to show all change
    # For deforestation, we usually care about loss.
    # Let's use absolute difference for visualization, but maybe signed for mask?
    # The user asked for "NDVI difference", usually implies magnitude of change.
    diff_mag = np.abs(d_ndvi)
    
    # Normalize heatmap
    # dNDVI ranges from -2 to 2, but usually -1 to 1.
    # Significant change is around 0.1 - 0.5
    norm_diff = np.clip(diff_mag / 0.5, 0, 1.0)
    
    # Apply colormap
    heatmap_rgba = cm.jet(norm_diff)
    heatmap_rgb = (heatmap_rgba[:, :, :3] * 255).astype(np.uint8)
    
    # Binary mask
    # Threshold for NDVI difference is usually small, e.g., 0.1 or 0.2
    mask = (diff_mag > threshold).astype(np.uint8) * 255
    
    return heatmap_rgb, mask

def compute_rgb_difference(before_path, after_path, threshold=30):
    """Fallback to old RGB difference"""
    b_img = Image.open(before_path).convert('RGB')
    a_img = Image.open(after_path).convert('RGB')
    if b_img.size != a_img.size: a_img = a_img.resize(b_img.size)
    b_arr = np.array(b_img, dtype=np.int16)
    a_arr = np.array(a_img, dtype=np.int16)
    diff = np.abs(b_arr - a_arr)
    diff_mag = np.mean(diff, axis=2)
    norm_diff = np.clip(diff_mag / 100.0, 0, 1.0)
    heatmap_rgba = cm.jet(norm_diff)
    heatmap_rgb = (heatmap_rgba[:, :, :3] * 255).astype(np.uint8)
    mask = (diff_mag > threshold).astype(np.uint8) * 255
    return heatmap_rgb, mask

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    # Threshold for NDVI is much smaller (0.0 - 2.0), default 0.15
    parser.add_argument("--threshold", type=float, default=0.15, help="Difference threshold (NDVI: 0.1-0.5, RGB: 0-255)")
    parser.add_argument("--model", help="Ignored", default=None) 
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    
    print(f"Running NDVI difference inference on {args.in_dir}...")
    
    before_files = sorted(glob.glob(os.path.join(args.in_dir, "*_before.png")))
    before_files = [f for f in before_files if "_nir_before.png" not in f]
    
    if not before_files:
        print("No input files found.")
        return

    for b_file in tqdm(before_files):
        base = os.path.basename(b_file).replace('_before.png', '')
        a_file = os.path.join(args.in_dir, f"{base}_after.png")
        
        # Construct NIR paths
        b_nir = os.path.join(args.in_dir, f"{base}_nir_before.png")
        a_nir = os.path.join(args.in_dir, f"{base}_nir_after.png")
        
        if not os.path.exists(a_file):
            print(f"Missing after file for {base}")
            continue
            
        # Compute Difference
        heatmap, mask = compute_difference(b_file, a_file, b_nir, a_nir, threshold=args.threshold)
        
        # Save results
        Image.fromarray(heatmap, mode='RGB').save(os.path.join(args.out_dir, f"{base}_heat.png"))
        Image.fromarray(mask, mode='L').save(os.path.join(args.out_dir, f"{base}_mask.png"))
        
        # Calculate simple metrics
        deforestation_px = np.sum(mask > 0)
        total_px = mask.size
        
        import json
        metrics = {
            "deforestation_percent": float((deforestation_px / total_px) * 100),
            "confidence": 1.0, 
            "changed_pixels": int(deforestation_px)
        }
        with open(os.path.join(args.out_dir, f"{base}_metrics.json"), "w") as f:
            json.dump(metrics, f)
            
    print("Done.")

if __name__ == "__main__":
    main()
