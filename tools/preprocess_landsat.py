#!/usr/bin/env python3
"""
tools/preprocess_landsat.py

Preprocesses Landsat PNGs:
1. Creates synthetic change masks (diff > threshold).
2. Slices images into 256x256 patches.
3. Saves patches to data/chips with naming convention compatible with train.py.
"""

import os
import glob
import numpy as np
from PIL import Image
import argparse

def create_synthetic_change_mask(before_path, after_path):
    b_img = Image.open(before_path).convert('RGB')
    a_img = Image.open(after_path).convert('RGB')
    
    # Ensure same size
    if b_img.size != a_img.size:
        a_img = a_img.resize(b_img.size)
        
    b_arr = np.array(b_img, dtype=np.int16)
    a_arr = np.array(a_img, dtype=np.int16)
    
    # Simple diff on grayscale for mask generation
    b_gray = np.array(b_img.convert('L'), dtype=np.int16)
    a_gray = np.array(a_img.convert('L'), dtype=np.int16)
    
    diff = np.abs(b_gray - a_gray)
    # Threshold 40 as per user snippet
    mask = np.where(diff > 40, 255, 0).astype(np.uint8)
    
    return Image.fromarray(mask), b_img, a_img

def slice_images_into_patches(b_img, a_img, m_img, patch_size, out_dir, base_name, start_num=0):
    w, h = b_img.size
    num = start_num
    
    # We save flat files: {base}_{num}_before.png, etc.
    # This matches the glob pattern *before* in train.py (if we update it to support png)
    
    for y in range(0, h - patch_size + 1, patch_size):
        for x in range(0, w - patch_size + 1, patch_size):
            box = (x, y, x + patch_size, y + patch_size)
            b_patch = b_img.crop(box)
            a_patch = a_img.crop(box)
            m_patch = m_img.crop(box)
            
            # Skip empty/black patches if needed? User script didn't, but let's keep it simple.
            
            tile_id = f"{base_name}_{num}"
            b_patch.save(os.path.join(out_dir, f"{tile_id}_before.png"))
            a_patch.save(os.path.join(out_dir, f"{tile_id}_after.png"))
            m_patch.save(os.path.join(out_dir, f"{tile_id}_mask.png"))
            
            num += 1
    return num

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", default="data/raw_landsat")
    parser.add_argument("--out-dir", default="data/chips")
    parser.add_argument("--patch-size", type=int, default=256)
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    
    # Clean output dir? Maybe not, let's append.
    
    before_files = sorted(glob.glob(os.path.join(args.in_dir, "*_before.png")))
    patch_count = 0
    
    print(f"Found {len(before_files)} before images in {args.in_dir}")
    
    for b_file in before_files:
        base = os.path.basename(b_file).replace('_before.png', '')
        a_file = os.path.join(args.in_dir, f"{base}_after.png")
        
        if not os.path.exists(a_file):
            print(f"Missing after file for {base}, skipping.")
            continue
            
        print(f"Preprocessing {base}...")
        mask_img, b_img, a_img = create_synthetic_change_mask(b_file, a_file)
        
        count = slice_images_into_patches(b_img, a_img, mask_img, args.patch_size, args.out_dir, base, start_num=patch_count)
        diff = count - patch_count
        print(f"  -> Generated {diff} patches.")
        patch_count = count

    print(f"Total patches generated: {patch_count}")

if __name__ == "__main__":
    main()
