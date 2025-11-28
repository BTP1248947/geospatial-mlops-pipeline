# src/data/create_baseline.py
import json, numpy as np, os
from PIL import Image
from pathlib import Path
import argparse

def main(processed="data/processed", out="data/baseline.json", bins=256):
    before_dir = Path(processed)/"before"
    imgs = sorted([before_dir / f for f in os.listdir(before_dir)][:1000])  # sample up to 1000
    hist = np.zeros(bins, dtype=np.int64)
    mean_accum = 0.0; cnt=0
    for p in imgs:
        im = np.array(Image.open(p).convert("L")).ravel()
        hist += np.histogram(im, bins=bins, range=(0,255))[0]
        mean_accum += im.mean(); cnt += 1
    hist = hist.tolist()
    outd = {"mean": float(mean_accum/cnt), "std": None, "hist": hist}
    with open(out, "w") as f: json.dump(outd, f)
    print("Wrote", out)

if __name__ == "__main__":
    main()
