
import os
import glob
import json
import shutil
import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--visuals-dir", default="outputs/site/visuals")
    p.add_argument("--raw-dir", default="data/raw")
    p.add_argument("--ui-public-dir", default="ui/public/visualization_results")
    args = p.parse_args()

    os.makedirs(args.ui_public_dir, exist_ok=True)

    # 1. Iterate raw files to find available data pairs
    raw_files = glob.glob(os.path.join(args.raw_dir, "*_before.png"))
    print(f"DEBUG: Found {len(raw_files)} raw files in {args.raw_dir}")
    
    index_data = {"regions": [], "years": {}}
    
    for raw_path in raw_files:
        # raw_path: .../brazil_mato_grosso_2020_2021_before.png
        filename = os.path.basename(raw_path)
        
        # Parse base name and years
        import re
        match = re.search(r"(.*)_(\d{4})_(\d{4})_before\.png", filename)
        if match:
            aoi_name = match.group(1)
            before_year = int(match.group(2))
            after_year = int(match.group(3))
            base_prefix = filename.replace("_before.png", "")
        else:
            # Legacy support or skip
            print(f"[WARN] Skipping non-standard file: {filename}")
            continue

        # Check if inference results exist
        heat_src = os.path.join(args.visuals_dir, f"{base_prefix}_heat.png")
        mask_src = os.path.join(args.visuals_dir, f"{base_prefix}_mask.png")
        
        if not os.path.exists(heat_src) or not os.path.exists(mask_src):
            print(f"[WARN] Missing inference results for {base_prefix}, skipping.")
            continue

        # Create region folder
        region_dir = os.path.join(args.ui_public_dir, aoi_name)
        os.makedirs(region_dir, exist_ok=True)
        
        # Copy Raw Before -> before_{year}.png
        shutil.copy(raw_path, os.path.join(region_dir, f"before_{before_year}.png"))
        
        # Copy Raw After -> after_{year}.png
        raw_after = os.path.join(args.raw_dir, f"{base_prefix}_after.png")
        if os.path.exists(raw_after):
            shutil.copy(raw_after, os.path.join(region_dir, f"after_{after_year}.png"))
            
        # Copy Mask -> mask_{before_year}.png
        shutil.copy(mask_src, os.path.join(region_dir, f"mask_{before_year}.png"))

        # Copy Heatmap -> heat_{before_year}.png
        shutil.copy(heat_src, os.path.join(region_dir, f"heat_{before_year}.png"))
            
        # Read Metrics
        metrics_src = os.path.join(args.visuals_dir, f"{base_prefix}_metrics.json")
        if os.path.exists(metrics_src):
            with open(metrics_src) as f:
                metrics = json.load(f)
            if "metrics" not in index_data:
                index_data["metrics"] = {}
            if aoi_name not in index_data["metrics"]:
                index_data["metrics"][aoi_name] = {}
            index_data["metrics"][aoi_name][before_year] = metrics
            
        # Update Index
        if aoi_name not in index_data["regions"]:
            index_data["regions"].append(aoi_name)
            
        if aoi_name not in index_data["years"]:
            index_data["years"][aoi_name] = []
        
        index_data["years"][aoi_name].extend([before_year, after_year])
        index_data["years"][aoi_name] = sorted(list(set(index_data["years"][aoi_name])))
        
        print(f"[INFO] Processed {aoi_name}: {before_year} -> {after_year}")

    index_data["regions"].sort()
    
    with open(os.path.join(args.ui_public_dir, "index.json"), "w") as f:
        json.dump(index_data, f, indent=2)
    
    print(f"[INFO] Updated index.json with {len(index_data['regions'])} regions.")

if __name__ == "__main__":
    main()
