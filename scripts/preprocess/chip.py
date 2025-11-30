#!/usr/bin/env python3
"""
Cut before/after/mask images into 256x256 tiles.

Usage:
  python scripts/preprocess/chip.py --in-dir processed_data --out-dir data/chips --size 256
"""
import argparse, os, glob
from PIL import Image

def chip_single(img, out_dir, prefix, size=256, start=0):
    w,h = img.size
    num = start
    for y in range(0, h - size + 1, size):
        for x in range(0, w - size + 1, size):
            box = (x,y,x+size,y+size)
            tile = img.crop(box)
            tile.save(os.path.join(out_dir, f'{prefix}_{num}.png'))
            num += 1
    return num

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--in-dir', default='processed_data')
    p.add_argument('--out-dir', default='data/chips')
    p.add_argument('--size', type=int, default=256)
    args = p.parse_args()

    before_files = sorted(glob.glob(os.path.join(args.in_dir, 'before', '*_before.*')))
    os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(os.path.join(args.out_dir,'before'), exist_ok=True)
    os.makedirs(os.path.join(args.out_dir,'after'), exist_ok=True)
    os.makedirs(os.path.join(args.out_dir,'mask'), exist_ok=True)

    idx = 0
    for b in before_files:
        key = os.path.basename(b).replace('_before','').rsplit('.',1)[0]
        a = os.path.join(args.in_dir, 'after', f'{key}_after.png')
        m = os.path.join(args.in_dir, 'mask', f'{key}_mask.png')
        if not (os.path.exists(a) and os.path.exists(m)):
            print(f"[WARN] missing pair or mask for {key}, skipping")
            continue
        bimg = Image.open(b).convert('RGB')
        aimg = Image.open(a).convert('RGB')
        mimg = Image.open(m).convert('L')
        idx = chip_single(bimg, os.path.join(args.out_dir,'before'), key+'_before', args.size, idx)
        idx = chip_single(aimg, os.path.join(args.out_dir,'after'), key+'_after', args.size, idx)
        idx = chip_single(mimg, os.path.join(args.out_dir,'mask'), key+'_mask', args.size, idx)
    print(f"[OK] Chipped tiles written (approx tiles per channel): {idx}")
if __name__ == '__main__':
    main()