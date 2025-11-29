
#!/usr/bin/env python3
"""
scripts/chip.py
Chips large TIFFs into smaller tiles (e.g., 256x256).
Supports directory input mode (scanning for *_before*.tif).
"""
import argparse, os, glob, sys
import rasterio
from rasterio.windows import Window
import numpy as np

def chip_pair(before_path, after_path, mask_path, out_dir, size, stride):
    with rasterio.open(before_path) as bsrc, rasterio.open(after_path) as asrc:
        # Basic checks
        if bsrc.width != asrc.width or bsrc.height != asrc.height:
            print(f"[WARN] Size mismatch {before_path} vs {after_path}, skipping.")
            return

        msrc = None
        if mask_path and os.path.exists(mask_path):
            msrc = rasterio.open(mask_path)
        
        basename = os.path.basename(before_path).replace("_before", "").replace(".tif", "")
        
        count = 0
        for yi in range(0, bsrc.height - size + 1, stride):
            for xi in range(0, bsrc.width - size + 1, stride):
                win = Window(xi, yi, size, size)
                
                # Check if window contains valid data (not all nodata)
                # For speed, just read one band or check nodata
                b_data = bsrc.read(window=win)
                
                # Skip if mostly empty/nodata (simple heuristic)
                if (b_data == 0).all(): 
                    continue

                a_data = asrc.read(window=win)
                
                if msrc:
                    m_data = msrc.read(1, window=win)
                else:
                    # Create proxy mask using NDVI difference
                    # Assuming bands: 0=Blue, 1=Green, 2=Red, 3=NIR
                    def calc_ndvi(arr):
                        # arr is (C, H, W)
                        nir = arr[3].astype(float)
                        red = arr[2].astype(float)
                        denom = nir + red
                        denom[denom == 0] = 1 # avoid div by zero
                        return (nir - red) / denom

                    ndvi_b = calc_ndvi(b_data)
                    ndvi_a = calc_ndvi(a_data)
                    
                    # Deforestation = Drop in NDVI
                    ndvi_diff = ndvi_b - ndvi_a
                    
                    # Threshold: 0.2 drop is significant
                    m_data = (ndvi_diff > 0.2).astype('uint8') * 255

                # Write chips
                tile_id = f"{basename}_{yi}_{xi}"
                meta = bsrc.profile.copy()
                meta.update(width=size, height=size, transform=bsrc.window_transform(win))
                
                # Save before
                with rasterio.open(os.path.join(out_dir, f"{tile_id}_before.tif"), "w", **meta) as dst:
                    dst.write(b_data)
                
                # Save after
                with rasterio.open(os.path.join(out_dir, f"{tile_id}_after.tif"), "w", **meta) as dst:
                    dst.write(a_data)
                
                # Save mask
                meta_mask = meta.copy()
                meta_mask.update(count=1, dtype='uint8')
                with rasterio.open(os.path.join(out_dir, f"{tile_id}_mask.tif"), "w", **meta_mask) as dst:
                    dst.write(m_data.astype('uint8'), 1)
                
                count += 1
        
        if msrc: msrc.close()
        print(f"[INFO] Chipped {basename}: {count} tiles.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--size", type=int, default=256)
    p.add_argument("--stride", type=int, default=256)
    p.add_argument("--pattern", default="*before*.tif")
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    
    # Find before files
    before_files = glob.glob(os.path.join(args.in_dir, args.pattern))
    print(f"[INFO] Found {len(before_files)} 'before' files in {args.in_dir}")

    for b_path in before_files:
        # Try to find matching after
        # Assumption: name is something_before_date.tif -> something_after_date.tif
        # or just replace "before" with "after"
        a_path = b_path.replace("before", "after")
        if not os.path.exists(a_path):
            # Try looser match
            base = os.path.basename(b_path).split("_before")[0]
            candidates = glob.glob(os.path.join(args.in_dir, f"{base}*after*.tif"))
            if candidates:
                a_path = candidates[0]
            else:
                print(f"[WARN] No matching 'after' file for {b_path}")
                continue
        
        # Try to find mask
        m_path = b_path.replace("before", "mask")
        if not os.path.exists(m_path):
            m_path = None # Will generate blank/proxy
            
        chip_pair(b_path, a_path, m_path, args.out_dir, args.size, args.stride)

if __name__ == "__main__":
    main()
