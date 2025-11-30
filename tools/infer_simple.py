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

def compute_difference(before_path, after_path, threshold=30):
    """
    Computes absolute difference between two images.
    Returns heatmap (difference magnitude) and binary mask.
    """
    b_img = Image.open(before_path).convert('RGB')
    a_img = Image.open(after_path).convert('RGB')
    
    # Resize after to match before if needed
    if b_img.size != a_img.size:
        a_img = a_img.resize(b_img.size)
        
    b_arr = np.array(b_img, dtype=np.int16)
    a_arr = np.array(a_img, dtype=np.int16)
    
    # Simple absolute difference per channel, then mean or max
    # Let's take the mean difference across RGB channels
    diff = np.abs(b_arr - a_arr)
    diff_mag = np.mean(diff, axis=2) # (H, W)
    
    # Normalize heatmap to 0-255
    heatmap = np.clip(diff_mag * 3, 0, 255).astype(np.uint8) # Scale up visibility
    
    # Binary mask
    mask = (diff_mag > threshold).astype(np.uint8) * 255
    
    return heatmap, mask

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--threshold", type=int, default=30, help="Difference threshold (0-255)")
    # --model argument is kept for compatibility but ignored
    parser.add_argument("--model", help="Ignored", default=None) 
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    
    print(f"Running simple difference inference on {args.in_dir}...")
    
    before_files = sorted(glob.glob(os.path.join(args.in_dir, "*_before.png")))
    
    if not before_files:
        print("No input files found.")
        return

    for b_file in tqdm(before_files):
        base = os.path.basename(b_file).replace('_before.png', '')
        a_file = os.path.join(args.in_dir, f"{base}_after.png")
        
        if not os.path.exists(a_file):
            print(f"Missing after file for {base}")
            continue
            
        # Compute Difference
        heatmap, mask = compute_difference(b_file, a_file, threshold=args.threshold)
        
        # Save results
        Image.fromarray(heatmap, mode='L').save(os.path.join(args.out_dir, f"{base}_heat.png"))
        Image.fromarray(mask, mode='L').save(os.path.join(args.out_dir, f"{base}_mask.png"))
        
        # Calculate simple metrics
        deforestation_px = np.sum(mask > 0)
        total_px = mask.size
        
        import json
        metrics = {
            "deforestation_percent": float((deforestation_px / total_px) * 100),
            "confidence": 1.0, # Dummy
            "changed_pixels": int(deforestation_px)
        }
        with open(os.path.join(args.out_dir, f"{base}_metrics.json"), "w") as f:
            json.dump(metrics, f)
            
    print("Done.")

if __name__ == "__main__":
    main()
