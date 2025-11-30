#!/usr/bin/env python3
"""
Create visualization_results/ structure for the React UI.

Will copy per-ROI before/after/mask images (fullsize) into
visualization_results/<roi>/before_YEAR.png etc
and produce index.json used by the UI.

Usage:
  python scripts/preprocess/generate_visualization_index.py --processed processed_data --out visualization_results
"""
import argparse, os, glob, json, shutil
from PIL import Image

def ensure_png_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im = Image.open(src)
    im.save(dst)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--processed', default='processed_data')
    p.add_argument('--out', default='visualization_results')
    args = p.parse_args()
    os.makedirs(args.out, exist_ok=True)

    # look for before files like <roi>_before.png
    before_files = glob.glob(os.path.join(args.processed, 'before', '*_before.*'))
    regions = []
    years_map = {}
    metrics_map = {}

    for b in before_files:
        base = os.path.basename(b)
        key = base.replace('_before','').rsplit('.',1)[0]
        # try extract year if filename contains a year; otherwise leave it simple
        year = None
        import re
        m = re.search(r'(\d{4})', key)
        if m:
            year = m.group(1)
            roi = key.replace('_'+year,'')
        else:
            roi = key
            year = '2024'  # default label if none present

        a_candidate = os.path.join(args.processed, 'after', f'{key}_after.png')
        mask_candidate = os.path.join(args.processed, 'mask', f'{key}_mask.png')
        if not os.path.exists(a_candidate) or not os.path.exists(mask_candidate):
            print(f"[WARN] missing after/mask for {key}, skipping visual item")
            continue

        roi_dir = os.path.join(args.out, roi)
        os.makedirs(roi_dir, exist_ok=True)
        before_out = os.path.join(roi_dir, f'before_{year}.png')
        after_out = os.path.join(roi_dir, f'after_{year}.png')
        mask_out  = os.path.join(roi_dir, f'mask_{year}.png')
        ensure_png_copy(b, before_out)
        ensure_png_copy(a_candidate, after_out)
        ensure_png_copy(mask_candidate, mask_out)

        regions.append(roi)
        years_map.setdefault(roi, []).append(int(year))
        # simple metric placeholder
        metrics_map.setdefault(roi, {})[str(year)] = {
            'changed_pixels': int(os.path.getsize(mask_out) % 10000), # placeholder
            'deforestation_percent': round((int(os.path.getsize(mask_out) % 100)/10.0), 2),
            'area_ha': None
        }

    # canonicalize years per ROI sorted
    years_map = {r: sorted(list(set(years_map[r]))) for r in years_map}

    index = {
        'regions': sorted(list(set(regions))),
        'years': years_map,
        'metrics': metrics_map
    }
    with open(os.path.join(args.out, 'index.json'), 'w') as f:
        json.dump(index, f, indent=2)
    print(f"[OK] visualization index written to {args.out}/index.json")

if __name__ == '__main__':
    main()