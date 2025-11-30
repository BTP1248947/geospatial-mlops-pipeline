#!/usr/bin/env python3
"""
Create synthetic change masks from before/after images.

Usage:
    python scripts/preprocess/create_mask.py --input-dir raw_data --out-dir processed_data --threshold 40
"""
import argparse, os, glob
from PIL import Image
import numpy as np

def make_mask(before_path, after_path, threshold):
    b = Image.open(before_path).convert('L')
    a = Image.open(after_path).convert('L')
    if b.size != a.size:
        a = a.resize(b.size)
    b_arr = np.array(b, dtype=np.int16)
    a_arr = np.array(a, dtype=np.int16)
    diff = np.abs(a_arr - b_arr)
    mask = (diff > threshold).astype('uint8') * 255
    return Image.fromarray(mask)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input-dir', default='raw_data')
    p.add_argument('--out-dir', default='processed_data')
    p.add_argument('--threshold', type=int, default=40)
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(os.path.join(args.out_dir, 'before'), exist_ok=True)
    os.makedirs(os.path.join(args.out_dir, 'after'), exist_ok=True)
    os.makedirs(os.path.join(args.out_dir, 'mask'), exist_ok=True)

    # Try pattern <roi>_before.* and <roi>_after.*
    befores = sorted(glob.glob(os.path.join(args.input_dir, '*_before.*')))
    if not befores:
        # fallback: subfolders with before.png / after.png
        candidates = []
        for sub in sorted(glob.glob(os.path.join(args.input_dir, '*'))):
            before = os.path.join(sub, 'before.png')
            after = os.path.join(sub, 'after.png')
            if os.path.exists(before) and os.path.exists(after):
                candidates.append((before, after, os.path.basename(sub)))
        for before, after, name in candidates:
            mask = make_mask(before, after, args.threshold)
            mask.save(os.path.join(args.out_dir, 'mask', f'{name}_mask.png'))
            Image.open(before).save(os.path.join(args.out_dir, 'before', f'{name}_before.png'))
            Image.open(after).save(os.path.join(args.out_dir, 'after', f'{name}_after.png'))
        print(f"Processed {len(candidates)} folders.")
        return

    count = 0
    for bpath in befores:
        base = os.path.basename(bpath)
        key = base.replace('_before', '').rsplit('.', 1)[0]
        apath = bpath.replace('_before', '_after')
        if not os.path.exists(apath):
            print(f"[WARN] No after for {bpath}, skipping")
            continue
        mask = make_mask(bpath, apath, args.threshold)
        mask_out = os.path.join(args.out_dir, 'mask', f'{key}_mask.png')
        b_out = os.path.join(args.out_dir, 'before', f'{key}_before.png')
        a_out = os.path.join(args.out_dir, 'after', f'{key}_after.png')
        mask.save(mask_out)
        # copy original scaled imagery (PIL preserve)
        Image.open(bpath).save(b_out)
        Image.open(apath).save(a_out)
        count += 1
    print(f"[OK] Created masks for {count} pairs.")

if __name__ == '__main__':
    main()