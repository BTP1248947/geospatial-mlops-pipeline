
import argparse
import json
import glob
import rasterio
import numpy as np
import os

def compute_stats(file_list):
    means = []
    stds = []
    # Just sample a subset if too many
    sample = file_list[:100] if len(file_list) > 100 else file_list
    
    for f in sample:
        with rasterio.open(f) as src:
            arr = src.read()
            # Handle nodata/nan
            arr = arr.astype('float32')
            arr[arr == 0] = np.nan
            means.append(np.nanmean(arr, axis=(1,2)))
            stds.append(np.nanstd(arr, axis=(1,2)))
            
    if not means:
        return {}

    means = np.array(means) # (N, Bands)
    stds = np.array(stds)
    
    global_mean = np.nanmean(means, axis=0).tolist()
    global_std = np.nanmean(stds, axis=0).tolist()
    
    return {
        "mean": global_mean,
        "std": global_std,
        "n_samples": len(file_list)
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--chips", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    
    files = glob.glob(os.path.join(args.chips, "*_before.tif"))
    print(f"[INFO] Computing baseline from {len(files)} chips...")
    
    stats = compute_stats(files)
    
    with open(args.out, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"[INFO] Baseline saved to {args.out}")

if __name__ == "__main__":
    main()
