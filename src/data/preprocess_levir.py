# src/data/preprocess_levir.py
import os
import argparse
from pathlib import Path
from PIL import Image
import csv
import math

def find_triplets(root):
    """
    Search for A,B,label triplets.
    Two heuristics:
      - Look for files named *_A.png, *_B.png, *_label.png
      - Or per-scene folders with A.png, B.png, label.png
    Returns list of tuples (before_path, after_path, mask_path)
    """
    root = Path(root)
    triplets = []

    # heuristic 1: pattern *_A.png or *_A.jpg
    a_files = list(root.rglob("*_A.*"))
    if a_files:
        for a in a_files:
            stem = a.name
            candidates = []
            name_prefix = stem.rsplit("_A", 1)[0]
            # try variants
            for ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
                b = a.parent / (name_prefix + "_B" + ext)
                m = a.parent / (name_prefix + "_label" + ext)
                if b.exists() and m.exists():
                    triplets.append((str(a.resolve()), str(b.resolve()), str(m.resolve())))
        if triplets:
            return triplets

    # heuristic 2: per-scene folder where filenames are A.png, B.png, label.png (case-insensitive)
    for p in root.rglob("*"):
        if p.is_dir():
            items = {f.name.lower(): f for f in p.iterdir() if f.is_file()}
            # check keys
            for a_name in ("a.png","a.jpg","a.jpeg","a.tif","a.tiff"):
                if a_name in items:
                    # try to find matching b and label
                    b_candidates = [items.get(n) for n in ("b.png","b.jpg","b.jpeg","b.tif","b.tiff")]
                    m_candidates = [items.get(n) for n in ("label.png","mask.png","label.jpg","label.tif")]
                    b = next((x for x in b_candidates if x), None)
                    m = next((x for x in m_candidates if x), None)
                    if b and m:
                        triplets.append((str(items[a_name].resolve()), str(b.resolve()), str(m.resolve())))
    # heuristic 3: look for pairs named before.png/after.png or A/B with other casings
    for p in root.rglob("*"):
        if p.is_file():
            name_lower = p.name.lower()
            if name_lower in ("before.png", "after.png", "mask.png", "label.png"):
                parent = p.parent
                before = parent / "before.png"
                after = parent / "after.png"
                mask = parent / "mask.png"
                if before.exists() and after.exists() and mask.exists():
                    triplets.append((str(before.resolve()), str(after.resolve()), str(mask.resolve())))
    return triplets

def tile_and_save(img_path, out_dir, chip=256):
    img = Image.open(img_path).convert("RGB")
    W, H = img.size
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    stride = chip
    # tile non-overlap for simplicity
    nx = math.ceil(W / chip)
    ny = math.ceil(H / chip)
    idx = 0
    for iy in range(ny):
        for ix in range(nx):
            left = ix * chip
            upper = iy * chip
            right = min(left + chip, W)
            lower = min(upper + chip, H)
            patch = img.crop((left, upper, right, lower))
            # if patch smaller than chip, pad it
            if patch.size != (chip, chip):
                new = Image.new("RGB", (chip, chip))
                new.paste(patch, (0,0))
                patch = new
            fname = f"{Path(img_path).stem}__{idx:04d}.png"
            patch.save(out_dir / fname)
            idx += 1
    return idx

def process_triplets(triplets, out_base, chip=256):
    out_base = Path(out_base)
    before_dir = out_base / "before"
    after_dir  = out_base / "after"
    mask_dir   = out_base / "masks"
    before_dir.mkdir(parents=True, exist_ok=True)
    after_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for (a,b,m) in triplets:
        # tile each and then pair by index (same stem and index)
        # note: using stem__0000.png naming ensures matching
        ai = Image.open(a).convert("RGB")
        bi = Image.open(b).convert("RGB")
        mi = Image.open(m).convert("L")

        W,H = ai.size
        nx = math.ceil(W / chip)
        ny = math.ceil(H / chip)
        idx = 0
        for iy in range(ny):
            for ix in range(nx):
                left = ix * chip
                upper = iy * chip
                right = min(left + chip, W)
                lower = min(upper + chip, H)

                pa = ai.crop((left,upper,right,lower))
                pb = bi.crop((left,upper,right,lower))
                pm = mi.crop((left,upper,right,lower))

                if pa.size != (chip,chip):
                    new = Image.new("RGB", (chip,chip))
                    new.paste(pa, (0,0))
                    pa = new
                if pb.size != (chip,chip):
                    new = Image.new("RGB", (chip,chip))
                    new.paste(pb, (0,0))
                    pb = new
                if pm.size != (chip,chip):
                    newm = Image.new("L", (chip,chip))
                    newm.paste(pm, (0,0))
                    pm = newm

                fname = f"{Path(a).stem}__{idx:04d}.png"
                pa.save(before_dir / fname)
                pb.save(after_dir  / fname)
                pm.save(mask_dir   / fname)
                rows.append((str((before_dir / fname).resolve()), str((after_dir / fname).resolve()), str((mask_dir / fname).resolve())))
                idx += 1
    # write mapping csv
    mapping_csv = out_base / "mapping_levir_processed.csv"
    with open(mapping_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["before","after","mask"])
        for r in rows:
            writer.writerow(r)
    print(f"Wrote {len(rows)} tiles and mapping CSV: {mapping_csv}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True, help="path to LEVIR root (data/raw/LEVIR CD)")
    p.add_argument("--out", default="data/processed", help="output processed dir")
    p.add_argument("--chip", type=int, default=256)
    args = p.parse_args()

    triplets = find_triplets(args.src)
    if not triplets:
        print("No triplets found with heuristics. Please check your LEVIR folder layout under", args.src)
        raise SystemExit(1)
    print(f"Found {len(triplets)} scene triplets. Starting tiling...")
    process_triplets(triplets, args.out, chip=args.chip)
